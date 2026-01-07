from django.core.management.base import BaseCommand
from django.conf import settings
from tiktok_pm_project.db_sync import SyncManager, SyncType, SyncDirection


class Command(BaseCommand):
    help = '手动触发数据库同步'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['FULL', 'INCREMENTAL'],
            help='同步类型: FULL(全量) 或 INCREMENTAL(增量)',
            default=None
        )
        parser.add_argument(
            '--direction',
            type=str,
            choices=['BOTH', 'REMOTE_TO_LOCAL', 'LOCAL_TO_REMOTE'],
            help='同步方向: BOTH(双向), REMOTE_TO_LOCAL(远程到本地), LOCAL_TO_REMOTE(本地到远程)',
            default=None
        )
        parser.add_argument(
            '--table',
            type=str,
            help='指定同步的表名(可选)',
            default=None
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='显示详细输出',
        )

    def handle(self, *args, **options):
        if not getattr(settings, 'DB_SYNC_ENABLED', False):
            self.stdout.write(self.style.ERROR('数据同步未启用'))
            return

        sync_type = None
        if options.get('type'):
            sync_type = SyncType(options['type'])

        sync_direction = None
        if options.get('direction'):
            sync_direction = SyncDirection(options['direction'])

        table_name = options.get('table')
        verbose = options.get('verbose', False)

        self.stdout.write('开始数据库同步...')
        self.stdout.write(f'同步类型: {sync_type.value if sync_type else "默认"}')
        self.stdout.write(f'同步方向: {sync_direction.value if sync_direction else "默认"}')
        if table_name:
            self.stdout.write(f'指定表: {table_name}')

        try:
            manager = SyncManager()
            
            if table_name:
                self.stdout.write(f'同步表: {table_name}')
                result = manager.sync_table(table_name, sync_type, sync_direction)
            else:
                result = manager.sync_all(sync_type, sync_direction)

            if result['success']:
                self.stdout.write(self.style.SUCCESS('同步成功!'))
                self.stdout.write(f'同步表数: {len(result.get("tables", []))}')
                self.stdout.write(f'影响行数: {result.get("total_rows", 0)}')
                self.stdout.write(f'耗时: {result.get("duration", 0):.2f}秒')
                
                if verbose and result.get('tables'):
                    self.stdout.write('\n详细同步结果:')
                    for table_result in result['tables']:
                        self.stdout.write(f"  - {table_result['table_name']}: "
                                       f"{table_result.get('rows_affected', 0)} 行")
            else:
                self.stdout.write(self.style.ERROR('同步失败!'))
                if result.get('message'):
                    self.stdout.write(f'错误信息: {result["message"]}')
                
                if result.get('errors'):
                    self.stdout.write('\n错误详情:')
                    for error in result['errors']:
                        self.stdout.write(f"  - {error.get('table', '未知')}: {error.get('error', '未知错误')}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'同步过程发生异常: {str(e)}'))
            if verbose:
                import traceback
                self.stdout.write(traceback.format_exc())