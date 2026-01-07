from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from tiktok_pm_project.db_sync.scheduler import setup_db_sync_scheduler, disable_db_sync_scheduler, get_scheduler_status


class Command(BaseCommand):
    help = '管理数据库同步定时任务'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['enable', 'disable', 'status', 'restart'],
            help='操作类型: enable(启用), disable(禁用), status(查看状态), restart(重启)',
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'enable':
            self._enable_scheduler()
        elif action == 'disable':
            self._disable_scheduler()
        elif action == 'status':
            self._show_status()
        elif action == 'restart':
            self._restart_scheduler()

    def _enable_scheduler(self):
        """启用数据库同步定时任务"""
        if not getattr(settings, 'DB_SYNC_ENABLED', False):
            self.stdout.write(self.style.ERROR('数据同步未启用(DB_SYNC_ENABLED=False)'))
            self.stdout.write('请在.env文件中设置 DB_SYNC_ENABLED=True')
            return
        
        sync_interval = getattr(settings, 'DB_SYNC_INTERVAL', 60)
        sync_direction = getattr(settings, 'DB_SYNC_DIRECTION', 'BOTH')
        sync_type = getattr(settings, 'DB_SYNC_TYPE', 'INCREMENTAL')
        
        self.stdout.write(f'配置信息:')
        self.stdout.write(f'  - 同步间隔: {sync_interval}分钟')
        self.stdout.write(f'  - 同步方向: {sync_direction}')
        self.stdout.write(f'  - 同步类型: {sync_type}')
        
        result = setup_db_sync_scheduler()
        
        if result:
            self.stdout.write(self.style.SUCCESS('数据库同步定时任务已启用'))
            self.stdout.write(f'任务将每{sync_interval}分钟自动执行一次')
        else:
            self.stdout.write(self.style.ERROR('启用定时任务失败'))

    def _disable_scheduler(self):
        """禁用数据库同步定时任务"""
        result = disable_db_sync_scheduler()
        
        if result:
            self.stdout.write(self.style.SUCCESS('数据库同步定时任务已禁用'))
        else:
            self.stdout.write(self.style.ERROR('禁用定时任务失败'))

    def _show_status(self):
        """显示定时任务状态"""
        status = get_scheduler_status()
        
        self.stdout.write('\n数据库同步定时任务状态:')
        self.stdout.write('=' * 50)
        
        if status.get('enabled'):
            self.stdout.write(self.style.SUCCESS('状态: 已启用'))
            self.stdout.write(f'调度类型: {status.get("schedule_type")}')
            self.stdout.write(f'执行间隔: {status.get("minutes")} 分钟')
            self.stdout.write(f'下次执行: {status.get("next_run")}')
            self.stdout.write(f'上次执行: {status.get("last_run")}')
            self.stdout.write(f'成功次数: {status.get("success_count", 0)}')
            self.stdout.write(f'失败次数: {status.get("failed_count", 0)}')
        else:
            self.stdout.write(self.style.WARNING('状态: 未启用'))
            if 'message' in status:
                self.stdout.write(f'信息: {status["message"]}')
            if 'error' in status:
                self.stdout.write(self.style.ERROR(f'错误: {status["error"]}'))
        
        self.stdout.write('=' * 50)
        
        if not getattr(settings, 'DB_SYNC_ENABLED', False):
            self.stdout.write(self.style.WARNING('\n注意: 数据同步功能未启用(DB_SYNC_ENABLED=False)'))

    def _restart_scheduler(self):
        """重启数据库同步定时任务"""
        self.stdout.write('重启数据库同步定时任务...')
        
        disable_result = disable_db_sync_scheduler()
        if not disable_result:
            self.stdout.write(self.style.WARNING('禁用旧任务失败，继续尝试启用新任务'))
        
        if not getattr(settings, 'DB_SYNC_ENABLED', False):
            self.stdout.write(self.style.ERROR('数据同步未启用(DB_SYNC_ENABLED=False)'))
            return
        
        enable_result = setup_db_sync_scheduler()
        
        if enable_result:
            self.stdout.write(self.style.SUCCESS('数据库同步定时任务已重启'))
        else:
            self.stdout.write(self.style.ERROR('重启定时任务失败'))
