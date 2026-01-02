# products/tasks.py
import json
import logging
import os
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import async_task

logger = logging.getLogger(__name__)

# 轮询任务配置
INITIAL_DELAY = 30  # 第一次轮询延迟（秒）
RETRY_DELAY = 60  # 重新轮询的间隔（秒）


# --------------------------
# 任务 A (trigger_bright_data_task): 触发外部 API，成功后获取 ID。
#
# 任务 A 调度任务 B： 使用 async_task 调度 poll_bright_data_result 在 30 秒后运行。
#
# 任务 B (poll_bright_data_result): 检查状态，如果未完成，再次调度任务 B (实现循环)。
# --------------------------
def trigger_bright_data_task(urls, collection_mode):
    # ... (构造 payload 和 headers 的代码不变) ...

    # ----------------------------------------------------
    # 1. 构造 JSON Payload (根据 collection_mode 动态变化)
    # ----------------------------------------------------

    if collection_mode in ["url", "shop"]:
        # 模式 1: 'url' 或 'shop' 保持不变，键为 "url"
        payload = {"input": [{"url": u} for u in urls]}

    elif collection_mode == "category":
        # 模式 2: 'category' 使用 "category_url" 键
        payload = {"input": [{"category_url": u} for u in urls]}

    elif collection_mode == "keyword":
        # 模式 3: 'keyword' 使用 "keyword" 键，并包含 "domain"
        payload = {"input": [{"keyword": u, "domain": "https://www.tiktok.com/shop"} for u in urls]}

    else:
        logger.error(f"未知的采集模式: {collection_mode}")
        return False

    logger.info(f"Payload: {payload}")

    # ----------------------------------------------------
    # 2. 构造 HTTP 请求头
    # ----------------------------------------------------
    headers = {
        "Authorization": f"Bearer {settings.BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json",
    }

    # ----------------------------------------------------
    # 3. 构造最终触发 URL (URL 逻辑保持不变)
    # ----------------------------------------------------
    base_trigger_url = settings.BRIGHT_DATA_BASE_SCRAPE_URL
    final_trigger_url = base_trigger_url

    if collection_mode == "category":
        final_trigger_url += f"{settings.BRIGHT_DATA_DISCOVER_TYPE}{settings.BRIGHT_DATA_DISCOVER_BY_CATEGORY}{settings.BRIGHT_DATA_PARAM_LIMIT_PER_INPUT}"

    elif collection_mode == "shop":
        final_trigger_url += f"{settings.BRIGHT_DATA_DISCOVER_TYPE}{settings.BRIGHT_DATA_DISCOVER_BY_SHOP}{settings.BRIGHT_DATA_PARAM_LIMIT_PER_INPUT}"

    elif collection_mode == "keyword":
        final_trigger_url += f"{settings.BRIGHT_DATA_DISCOVER_TYPE}{settings.BRIGHT_DATA_DISCOVER_BY_KEYWORD}{settings.BRIGHT_DATA_PARAM_LIMIT_PER_INPUT}"

    logger.info(f"Final Trigger URL: {final_trigger_url}")

    # ----------------------------------------------------
    # 4. 执行 API 调用
    # ----------------------------------------------------
    try:
        response = requests.post(
            final_trigger_url, headers=headers, data=json.dumps(payload), timeout=INITIAL_DELAY
        )
        response.raise_for_status()

        response_data = response.json()
        logger.debug(f"response data: {response_data}")
        snapshot_id = response_data.get("snapshot_id")

        if snapshot_id:
            logger.info(f"Bright Data API 触发成功。snapshot_id: {snapshot_id}")

            # 第一次轮询任务（立即运行）
            _schedule_delayed_poll(snapshot_id, delay_seconds=0)
            return True
        else:
            logger.error(f"Bright Data API 触发成功，但未返回 snapshot_id。响应: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Bright Data API 触发失败。错误: {e}")
        return False

    except Exception as e:
        logger.error(f"任务执行期间发生未知错误: {e}")
        return False


# ==========================================================
# 任务：轮询 Bright Data 结果
# ==========================================================
# ==========================================================
# 任务：轮询 Bright Data 结果
# ==========================================================
def poll_bright_data_result(snapshot_id_list):
    # 关键修复：从列表中取出实际的 ID 字符串
    snapshot_id = snapshot_id_list[0]
    logger.info(f"轮询 snapshot_id={snapshot_id}")

    headers = {"Authorization": f"Bearer {settings.BRIGHT_DATA_API_KEY}"}

    try:
        status_url = f"{settings.BRIGHT_DATA_STATUS_URL}{snapshot_id}"
        response = requests.get(status_url, headers=headers, timeout=30)
        response.raise_for_status()
        status_data = response.json()
        status = status_data.get("status")
        logger.debug(f"Bright Data 状态 = {status}")

        # 未完成 → 重新调度（不阻塞 worker）
        if status in ["pending", "running", "collecting"]:
            logger.info("状态未完成，30 秒后继续轮询")

            _schedule_delayed_poll(snapshot_id, delay_seconds=30)
            return

        # 完成 → 下载数据
        if status == "ready":
            download_url = f"{settings.BRIGHT_DATA_DOWNLOAD_BASE_URL}{snapshot_id}?format=json"
            download_response = requests.get(download_url, headers=headers, timeout=180)
            download_response.raise_for_status()

            downloaded_data = download_response.json()
            logger.info(f"下载成功 {len(downloaded_data)} records")

            # 保存 JSON 文件
            async_task("products.tasks.save_snapshot_file", snapshot_id, downloaded_data)

            # 🌟 关键修改：指向新的 ORM 导入服务 🌟
            async_task(
                "products.services.product_importer.import_products_from_list", downloaded_data
            )

            return

        logger.error(f"Bright Data 返回失败状态: {status}")

    except Exception as e:
        logger.error(f"轮询异常: {e}")
        # 失败也建议 30 秒后重试一次
        _schedule_delayed_poll(snapshot_id, delay_seconds=30)


def log_task_completion(task):
    """
    任务完成后执行的回调函数，必须接受一个 Task 对象作为唯一的位置参数。

    参数:
    task: django_q.models.Task 对象，包含任务的元数据、结果和状态。
    """
    try:
        # 检查主任务是否成功
        if task.success:
            logger.info(f"任务 {task.name} 成功完成。")

            # task.result 包含了主任务 (trigger_bright_data_task) 的返回值
            if task.result is True:
                logger.info("Bright Data API 触发成功。")
            else:
                logger.warning("Bright Data API 触发失败，请检查主任务日志。")

        else:
            logger.error(f"任务 {task.name} 执行失败!")
            # 失败的 traceback 存储在 task.result 中
            logger.error(f"失败原因: {task.result[:200]}...")

    except Exception as e:
        # 如果 Hook 函数本身出错，打印日志而不是抛出异常
        logger.error(f"HOOK 自身发生错误: {e}")


# ===================================================================================
# 轮询任务延迟调度（Django-Q 2.x 正确写法）
# ===================================================================================


def _schedule_delayed_poll(snapshot_id, delay_seconds=30):
    """
    创建 legitimate Django-Q 2.x schedule args:
    使用 repr(list) 确保 args 存储为 Python literal 列表。
    """

    # 删除旧任务（避免重复）
    Schedule.objects.filter(name=f"poll_{snapshot_id}").delete()

    Schedule.objects.create(
        name=f"poll_{snapshot_id}",
        func="products.tasks.poll_bright_data_result",
        args=repr([snapshot_id]),  # 必须是字符串，而不是 Python object
        schedule_type=Schedule.ONCE,
        next_run=timezone.now() + timedelta(seconds=delay_seconds),
    )

    logger.info(f"已调度下一次轮询：{delay_seconds} 秒后执行")


# ===================================================================================
# 数据保存（异步任务）
# ===================================================================================


def save_snapshot_file(snapshot_id, data):
    """
    将 Bright Data 下载的数据保存到 /data/snapshot_xxx.json
    """
    json_data_dir = os.path.join(settings.BASE_DIR, "data", "json")
    os.makedirs(json_data_dir, exist_ok=True)

    target_file = os.path.join(json_data_dir, f"snapshot_{snapshot_id}.json")

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"JSON 文件保存成功：{target_file}")
