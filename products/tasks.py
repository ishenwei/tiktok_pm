# products/tasks.py
import json
import time
import requests
from datetime import datetime, timedelta
from django_q.tasks import async_task
from django_q.models import Task, Schedule # 🌟 确保导入 Task 🌟
from django.conf import settings
from .importer_wrapper import start_import_process  # 导入导入入口

# --------------------------
# Bright Data API URLs (固定不变，无需在 settings 中声明)
# --------------------------
BRIGHT_DATA_API_KEY = "011ac709c39e73762ef01946f0ca17b151e8c612e4c532e87764c23c61047ecf"
BRIGHT_DATA_URL = "https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_m45m1u911dsa4274pi&notify=false&include_errors=true"

BRIGHT_DATA_TRIGGER_URL = "https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_m45m1u911dsa4274pi&notify=false&include_errors=true"
BRIGHT_DATA_STATUS_URL = "https://api.brightdata.com/datasets/v3/progress/"
BRIGHT_DATA_DOWNLOAD_BASE_URL = "https://api.brightdata.com/datasets/v3/snapshot/"
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
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            BRIGHT_DATA_TRIGGER_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=INITIAL_DELAY
        )
        response.raise_for_status()

        response_data = response.json()
        snapshot_id = response_data.get("snapshot_id")

        if snapshot_id:
            print(f"✅ Bright Data API 触发成功。snapshot_id: {snapshot_id}")

            # 调度下一步的轮询任务
            async_task(
                'products.tasks.poll_bright_data_result',
                snapshot_id,  # 唯一位置参数
            )
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
def poll_bright_data_result(snapshot_id, **kwargs):
    """
    轮询 Bright Data 任务状态，如果完成则下载并导入数据，否则重新调度自身。
    """
    print(f"🔄 轮询开始: Checking status for snapshot_id: {snapshot_id}")

    # 🌟 关键：定义唯一的组名 🌟

    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}"
    }

    print(f"🔄 轮询开始: Checking status for snapshot_id: {snapshot_id}")
    while True:
        try:
            # 1. 查询任务状态
            # ... (查询状态的代码不变) ...
            status_url = f"{BRIGHT_DATA_STATUS_URL}{snapshot_id}"
            response = requests.get(status_url, headers=headers, timeout=30)
            response.raise_for_status()

            status_data = response.json()
            status = status_data.get('status')
            print(f"   当前状态: {status}")

            if status == 'ready':
                # 2. 任务已完成，下载结果
                print(f"🎉 任务完成: {snapshot_id}。开始下载数据...")

                # Bright Data 下载 URL (通常是 snapshot_id/download)
                #download_url = f"{BRIGHT_DATA_STATUS_URL}{snapshot_id}/download"
                download_url = f"{BRIGHT_DATA_DOWNLOAD_BASE_URL}{snapshot_id}?format=json"
                print(f"🎉  开始下载:" + download_url)
                download_response = requests.get(download_url, headers=headers, timeout=120)
                download_response.raise_for_status()

                # 假设数据是 JSON 格式（如果不是，您需要相应处理）
                downloaded_data = download_response.json()
                print(f"   下载 {len(downloaded_data)} 条记录。")

                # 🌟 关键：调用您的导入逻辑 🌟
                try:
                    start_import_process(downloaded_data)
                    print("   [数据导入] 导入逻辑调用成功！")  # 临时占位符
                except Exception as e:
                    print(f"   ❌ 数据导入失败: {e}")
                    return False

                return True  # 🌟 成功，跳出循环并结束任务 🌟

            elif status in ['running', 'collecting', 'pending']:
                # 任务仍在运行，暂停 Worker
                # 任务仍在运行，强制等待 30 秒
                print("   任务仍在运行。强制等待 30 秒后继续轮询...")

                # 🌟 核心：强制等待 30 秒 🌟
                time.sleep(30)
            else:
                # 任务失败
                print(f"❌ 任务失败。状态: {status}")
                return False  # 失败，跳出循环并结束任务
        except Exception as e:
            print(f"❌ 轮询任务执行期间发生未知错误: {e}")
            return False

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