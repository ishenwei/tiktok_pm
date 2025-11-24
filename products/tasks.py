# products/tasks.py
import json
import os
import requests
from django_q.tasks import async_task
from django_q.models import Schedule
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .importer_wrapper import start_import_process

# 轮询任务配置
INITIAL_DELAY = 30 # 第一次轮询延迟（秒）
RETRY_DELAY = 60   # 重新轮询的间隔（秒）

# --------------------------
# 任务 A (trigger_bright_data_task): 触发外部 API，成功后获取 ID。
#
# 任务 A 调度任务 B： 使用 async_task 调度 poll_bright_data_result 在 30 秒后运行。
#
# 任务 B (poll_bright_data_result): 检查状态，如果未完成，再次调度任务 B (实现循环)。
# --------------------------
def trigger_bright_data_task(urls):
    # ... (构造 payload 和 headers 的代码不变) ...

    # 1. 构造 JSON Payload
    payload = {
        "input": [{"url": u} for u in urls]
    }

    # 2. 构造 HTTP 请求头
    headers = {
        "Authorization": f"Bearer {settings.BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            settings.BRIGHT_DATA_TRIGGER_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=INITIAL_DELAY
        )
        response.raise_for_status()

        response_data = response.json()
        snapshot_id = response_data.get("snapshot_id")

        if snapshot_id:
            print(f"✅ Bright Data API 触发成功。snapshot_id: {snapshot_id}")

            # 第一次轮询任务（立即运行）
            #Schedule.objects.create(
            #    name=f"poll_{snapshot_id}",
            #    func="products.tasks.poll_bright_data_result",
            #    args=snapshot_id,
            #    schedule_type=Schedule.ONCE,
            #    next_run=timezone.now(),
            #)
            _schedule_delayed_poll(snapshot_id, delay_seconds=0)
            return True
        else:
            print(f"❌ Bright Data API 触发成功，但未返回 snapshot_id。响应: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Bright Data API 触发失败。错误: {e}")
        return False

    except Exception as e:
        print(f"❌ 任务执行期间发生未知错误: {e}")
        return False

# ==========================================================
# 任务：轮询 Bright Data 结果
# ==========================================================
def poll_bright_data_result(snapshot_id_list):
    # 关键修复：从列表中取出实际的 ID 字符串
    snapshot_id = snapshot_id_list[0]
    print(f"🔄 轮询 snapshot_id={snapshot_id}")

    headers = {
        "Authorization": f"Bearer {settings.BRIGHT_DATA_API_KEY}"
    }

    try:
        status_url = f"{settings.BRIGHT_DATA_STATUS_URL}{snapshot_id}"
        response = requests.get(status_url, headers=headers, timeout=30)
        response.raise_for_status()
        status_data = response.json()
        status = status_data.get("status")
        print(f"   Bright Data 状态 = {status}")

        # 未完成 → 重新调度（不阻塞 worker）
        if status in ["pending", "running", "collecting"]:
            print("   ▶ 状态未完成，30 秒后继续轮询")

            _schedule_delayed_poll(snapshot_id, delay_seconds=30)
            return

            return

        # 完成 → 下载数据
        if status == "ready":
            download_url = f"{settings.BRIGHT_DATA_DOWNLOAD_BASE_URL}{snapshot_id}?format=json"
            download_response = requests.get(download_url, headers=headers, timeout=180)
            download_response.raise_for_status()

            downloaded_data = download_response.json()
            print(f"   下载成功 {len(downloaded_data)} records")

            # 保存 JSON 文件（建议单独 async）
            async_task(
                "products.tasks.save_snapshot_file",
                snapshot_id,
                downloaded_data
            )

            # 启动导入任务（分离职责）
            async_task(
                "products.importer_wrapper.start_import_process",
                downloaded_data
            )

            return

        print(f"❌ Bright Data 返回失败状态: {status}")

    except Exception as e:
        print(f"❌ 轮询异常: {e}")
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
            print(f"✅ HOOK: 任务 {task.name} 成功完成。")

            # task.result 包含了主任务 (trigger_bright_data_task) 的返回值
            if task.result is True:
                print("      Bright Data API 触发成功。")
            else:
                print(f"      Bright Data API 触发失败，请检查主任务日志。")

        else:
            print(f"❌ HOOK: 任务 {task.name} 执行失败!")
            # 失败的 traceback 存储在 task.result 中
            print(f"      失败原因: {task.result[:200]}...")

    except Exception as e:
        # 如果 Hook 函数本身出错，打印日志而不是抛出异常
        print(f"❌ HOOK 自身发生错误: {e}")

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
        args=repr([snapshot_id]),   # 必须是字符串，而不是 Python object
        schedule_type=Schedule.ONCE,
        next_run=timezone.now() + timedelta(seconds=delay_seconds)
    )

    print(f"⏱ 已调度下一次轮询：{delay_seconds} 秒后执行")

# ===================================================================================
# 数据保存（异步任务）
# ===================================================================================

def save_snapshot_file(snapshot_id, data):
    """
    将 Bright Data 下载的数据保存到 /data/snapshot_xxx.json
    """
    json_data_dir = os.path.join(settings.BASE_DIR, 'data', 'json')
    os.makedirs(json_data_dir, exist_ok=True)

    target_file = os.path.join(json_data_dir, f"snapshot_{snapshot_id}.json")

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"📁 JSON 文件保存成功：{target_file}")
