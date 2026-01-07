import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from .config import SyncConfig, SyncType, SyncDirection, ConflictResolution, TableSyncConfig
from .connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SyncManager:
    def __init__(self, config: Optional[SyncConfig] = None):
        self.config = config or SyncConfig()
        self.remote_db = DatabaseConnection(self.config.remote_db)
        self.local_db = DatabaseConnection(self.config.local_db)
    
    def sync_all(self, sync_type: Optional[SyncType] = None,
                direction: Optional[SyncDirection] = None) -> Dict[str, Any]:
        if not self.config.enabled:
            return {'success': False, 'message': '数据同步未启用'}
        
        sync_type = sync_type or self.config.sync_type
        direction = direction or self.config.direction
        
        result = {
            'success': True,
            'sync_type': sync_type.value,
            'direction': direction.value,
            'start_time': datetime.now(),
            'tables': [],
            'total_rows': 0,
            'errors': []
        }
        
        log_id = self._create_sync_log(sync_type, direction, result['start_time'])
        
        try:
            tables = self.config.get_enabled_tables()
            if not tables:
                result['success'] = False
                result['message'] = '没有启用同步的表'
                self._update_sync_log(log_id, 'FAILED', result)
                return result
            
            for table_config in tables:
                try:
                    table_result = self._sync_table(table_config, sync_type, direction)
                    result['tables'].append(table_result)
                    result['total_rows'] += table_result.get('rows_affected', 0)
                except Exception as e:
                    logger.error(f"同步表 {table_config.table_name} 失败: {e}")
                    result['errors'].append({
                        'table': table_config.table_name,
                        'error': str(e)
                    })
            
            result['success'] = len(result['errors']) == 0
            status = 'SUCCESS' if result['success'] else 'FAILED'
            
        except Exception as e:
            logger.error(f"同步过程发生错误: {e}")
            result['success'] = False
            result['message'] = str(e)
            status = 'FAILED'
        
        result['end_time'] = datetime.now()
        result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
        
        self._update_sync_log(log_id, status, result)
        return result
    
    def _sync_table(self, table_config: TableSyncConfig, 
                   sync_type: SyncType, 
                   direction: SyncDirection) -> Dict[str, Any]:
        table_name = table_config.table_name
        result = {
            'table_name': table_name,
            'sync_type': sync_type.value,
            'direction': direction.value,
            'rows_affected': 0,
            'errors': []
        }
        
        if direction in [SyncDirection.REMOTE_TO_LOCAL, SyncDirection.BOTH]:
            remote_to_local = self._sync_table_direction(
                table_name, table_config, sync_type, 
                self.remote_db, self.local_db, 'REMOTE_TO_LOCAL'
            )
            result['remote_to_local'] = remote_to_local
            result['rows_affected'] += remote_to_local.get('rows_affected', 0)
        
        if direction in [SyncDirection.LOCAL_TO_REMOTE, SyncDirection.BOTH]:
            local_to_remote = self._sync_table_direction(
                table_name, table_config, sync_type, 
                self.local_db, self.remote_db, 'LOCAL_TO_REMOTE'
            )
            result['local_to_remote'] = local_to_remote
            result['rows_affected'] += local_to_remote.get('rows_affected', 0)
        
        self._update_table_sync_time(table_name)
        return result
    
    def _sync_table_direction(self, table_name: str, 
                              table_config: TableSyncConfig,
                              sync_type: SyncType,
                              source_db: DatabaseConnection,
                              target_db: DatabaseConnection,
                              direction: str) -> Dict[str, Any]:
        result = {
            'direction': direction,
            'rows_affected': 0,
            'errors': []
        }
        
        try:
            if not source_db.table_exists(table_name):
                result['errors'].append(f'源数据库中表 {table_name} 不存在')
                return result
            
            if not target_db.table_exists(table_name):
                result['errors'].append(f'目标数据库中表 {table_name} 不存在')
                return result
            
            if sync_type == SyncType.FULL:
                result['rows_affected'] = self._full_sync(
                    table_name, source_db, target_db
                )
            else:
                result['rows_affected'] = self._incremental_sync(
                    table_name, table_config, source_db, target_db
                )
            
        except Exception as e:
            logger.error(f"同步表 {table_name} ({direction}) 失败: {e}")
            result['errors'].append(str(e))
        
        return result
    
    def _full_sync(self, table_name: str, 
                   source_db: DatabaseConnection,
                   target_db: DatabaseConnection) -> int:
        rows_affected = 0
        
        batch_size = 1000
        offset = 0
        
        while True:
            data = source_db.get_table_data(
                table_name, 
                limit=batch_size,
                offset=offset
            )
            
            if not data:
                break
            
            target_db.batch_insert(table_name, data)
            rows_affected += len(data)
            offset += batch_size
            logger.info(f"已同步表 {table_name} {rows_affected} 行...")
        
        logger.info(f"全量同步表 {table_name} 完成, 共 {rows_affected} 行")
        return rows_affected
    
    def _incremental_sync(self, table_name: str,
                         table_config: TableSyncConfig,
                         source_db: DatabaseConnection,
                         target_db: DatabaseConnection) -> int:
        rows_affected = 0
        last_sync_time = table_config.last_sync_time
        
        if not last_sync_time:
            logger.warning(f"表 {table_name} 没有上次同步时间, 执行全量同步")
            return self._full_sync(table_name, source_db, target_db)
        
        update_column = self._get_update_column(table_name, source_db)
        if not update_column:
            logger.warning(f"表 {table_name} 没有更新时间字段, 执行全量同步")
            return self._full_sync(table_name, source_db, target_db)
        
        where_clause = f"{update_column} > %s"
        data = source_db.get_table_data(table_name, where_clause, (last_sync_time,))
        
        if data:
            for row in data:
                try:
                    if self._row_exists(target_db, table_name, row.get('id')):
                        self._update_row(target_db, table_name, row, table_config.conflict_resolution)
                    else:
                        target_db.insert_data(table_name, row)
                    rows_affected += 1
                except Exception as e:
                    logger.error(f"同步行失败: {e}")
        
        logger.info(f"增量同步表 {table_name} 完成, 共 {rows_affected} 行")
        return rows_affected
    
    def _get_update_column(self, table_name: str, db: DatabaseConnection) -> Optional[str]:
        schema = db.get_table_schema(table_name)
        for column in schema:
            if column['COLUMN_NAME'] in ['updated_at', 'update_time', 'modified_at']:
                return column['COLUMN_NAME']
        return None
    
    def _row_exists(self, db: DatabaseConnection, table_name: str, row_id: Any) -> bool:
        result = db.execute_query(
            f"SELECT COUNT(*) as count FROM {table_name} WHERE id = %s",
            (row_id,)
        )
        return result[0]['count'] > 0 if result else False
    
    def _update_row(self, db: DatabaseConnection, table_name: str, 
                   data: Dict[str, Any], 
                   conflict_resolution: ConflictResolution):
        row_id = data.pop('id', None)
        if not row_id:
            raise ValueError("行数据缺少ID字段")
        
        if conflict_resolution == ConflictResolution.SKIP:
            return
        
        db.update_data(table_name, data, "id = %s", (row_id,))
    
    def _create_sync_log(self, sync_type: SyncType, 
                        direction: SyncDirection, 
                        start_time: datetime) -> int:
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO db_sync_log (sync_type, direction, status, start_time) "
                    "VALUES (%s, %s, %s, %s)",
                    (sync_type.value, direction.value, 'IN_PROGRESS', start_time)
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"创建同步日志失败: {e}")
            return 0
    
    def _update_sync_log(self, log_id: int, status: str, result: Dict[str, Any]):
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                end_time = result.get('end_time', datetime.now())
                duration = result.get('duration', 0)
                tables_synced = len(result.get('tables', []))
                rows_affected = result.get('total_rows', 0)
                error_message = None
                
                if result.get('errors'):
                    error_message = '; '.join([e.get('error', '') for e in result['errors']])
                
                cursor.execute(
                    "UPDATE db_sync_log SET status = %s, end_time = %s, "
                    "duration = %s, tables_synced = %s, rows_affected = %s, "
                    "error_message = %s WHERE id = %s",
                    (status, end_time, duration, tables_synced, 
                     rows_affected, error_message, log_id)
                )
        except Exception as e:
            logger.error(f"更新同步日志失败: {e}")
    
    def _update_table_sync_time(self, table_name: str):
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE db_sync_config SET last_sync_time = NOW() "
                    "WHERE table_name = %s",
                    (table_name,)
                )
        except Exception as e:
            logger.error(f"更新表同步时间失败: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM db_sync_log ORDER BY start_time DESC LIMIT 10"
                )
                recent_logs = cursor.fetchall()
                
                cursor.execute(
                    "SELECT table_name, sync_enabled, sync_type, sync_direction, "
                    "last_sync_time FROM db_sync_config ORDER BY priority DESC"
                )
                table_configs = cursor.fetchall()
                
                return {
                    'recent_logs': recent_logs,
                    'table_configs': table_configs,
                    'sync_enabled': self.config.enabled
                }
        except Exception as e:
            logger.error(f"获取同步状态失败: {e}")
            return {'error': str(e)}