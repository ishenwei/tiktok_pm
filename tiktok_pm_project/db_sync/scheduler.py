import logging
from django_q.tasks import schedule
from django_q.models import Schedule
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .sync_manager import SyncManager

logger = logging.getLogger(__name__)


def setup_db_sync_scheduler():
    """
    设置数据库同步的定时任务
    
    根据配置的同步间隔，创建或更新定时任务
    """
    if not getattr(settings, 'DB_SYNC_ENABLED', False):
        logger.info('数据同步未启用，跳过定时任务设置')
        return None
    
    sync_interval = getattr(settings, 'DB_SYNC_INTERVAL', 60)
    sync_direction = getattr(settings, 'DB_SYNC_DIRECTION', 'BOTH')
    sync_type = getattr(settings, 'DB_SYNC_TYPE', 'INCREMENTAL')
    
    task_name = 'db_sync_scheduled_task'
    
    try:
        existing_schedule = Schedule.objects.filter(name=task_name).first()
        
        if existing_schedule:
            logger.info(f'更新现有同步任务，间隔: {sync_interval}分钟')
            existing_schedule.schedule_type = Schedule.MINUTES
            existing_schedule.minutes = sync_interval
            existing_schedule.next_run = timezone.now() + timedelta(minutes=sync_interval)
            existing_schedule.save()
        else:
            logger.info(f'创建新的同步任务，间隔: {sync_interval}分钟')
            schedule(
                'tiktok_pm_project.db_sync.scheduler.run_db_sync',
                name=task_name,
                schedule_type=Schedule.MINUTES,
                minutes=sync_interval,
                repeats=-1
            )
        
        logger.info(f'数据库同步定时任务已设置: 每{sync_interval}分钟执行一次')
        return True
        
    except Exception as e:
        logger.error(f'设置数据库同步定时任务失败: {e}')
        return False


def run_db_sync():
    """
    执行数据库同步的定时任务
    
    此函数由Django Q调度器定期调用
    """
    if not getattr(settings, 'DB_SYNC_ENABLED', False):
        logger.warning('数据同步未启用，跳过本次同步')
        return {'success': False, 'message': '数据同步未启用'}
    
    sync_direction = getattr(settings, 'DB_SYNC_DIRECTION', 'BOTH')
    sync_type = getattr(settings, 'DB_SYNC_TYPE', 'INCREMENTAL')
    
    logger.info(f'开始执行定时数据库同步 - 类型: {sync_type}, 方向: {sync_direction}')
    
    try:
        from . import SyncType, SyncDirection
        
        manager = SyncManager()
        result = manager.sync_all(
            sync_type=SyncType(sync_type),
            direction=SyncDirection(sync_direction)
        )
        
        if result['success']:
            logger.info(f'定时同步成功 - 同步表数: {len(result.get("tables", []))}, '
                       f'影响行数: {result.get("total_rows", 0)}, '
                       f'耗时: {result.get("duration", 0):.2f}秒')
        else:
            logger.error(f'定时同步失败: {result.get("message", "未知错误")}')
            if result.get('errors'):
                for error in result['errors']:
                    logger.error(f"  - {error.get('table', '未知')}: {error.get('error', '未知错误')}")
        
        return result
        
    except Exception as e:
        logger.error(f'定时同步过程发生异常: {e}', exc_info=True)
        return {'success': False, 'message': str(e)}


def disable_db_sync_scheduler():
    """
    禁用数据库同步的定时任务
    
    删除已注册的同步定时任务
    """
    task_name = 'db_sync_scheduled_task'
    
    try:
        deleted_count = Schedule.objects.filter(name=task_name).delete()[0]
        if deleted_count > 0:
            logger.info(f'已删除数据库同步定时任务')
        else:
            logger.info('未找到数据库同步定时任务')
        return True
    except Exception as e:
        logger.error(f'删除数据库同步定时任务失败: {e}')
        return False


def get_scheduler_status():
    """
    获取同步定时任务的状态
    
    Returns:
        dict: 包含定时任务状态信息的字典
    """
    task_name = 'db_sync_scheduled_task'
    
    try:
        schedule_obj = Schedule.objects.filter(name=task_name).first()
        
        if schedule_obj:
            return {
                'enabled': True,
                'schedule_type': schedule_obj.schedule_type,
                'minutes': schedule_obj.minutes,
                'next_run': schedule_obj.next_run,
                'last_run': schedule_obj.last_run,
                'success_count': schedule_obj.success_count,
                'failed_count': schedule_obj.failed_count,
            }
        else:
            return {
                'enabled': False,
                'message': '未找到定时任务'
            }
    except Exception as e:
        logger.error(f'获取定时任务状态失败: {e}')
        return {
            'enabled': False,
            'error': str(e)
        }
