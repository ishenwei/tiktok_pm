import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class SyncType(Enum):
    FULL = 'FULL'
    INCREMENTAL = 'INCREMENTAL'


class SyncDirection(Enum):
    BOTH = 'BOTH'
    REMOTE_TO_LOCAL = 'REMOTE_TO_LOCAL'
    LOCAL_TO_REMOTE = 'LOCAL_TO_REMOTE'


class ConflictResolution(Enum):
    REMOTE_WINS = 'REMOTE_WINS'
    LOCAL_WINS = 'LOCAL_WINS'
    SKIP = 'SKIP'
    MANUAL = 'MANUAL'


@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str

    @classmethod
    def from_env(cls, prefix: str) -> 'DatabaseConfig':
        return cls(
            host=os.environ.get(f'{prefix}_HOST', 'localhost'),
            port=int(os.environ.get(f'{prefix}_PORT', '3306')),
            name=os.environ.get(f'{prefix}_NAME', 'tiktok_products_dev'),
            user=os.environ.get(f'{prefix}_USER', 'root'),
            password=os.environ.get(f'{prefix}_PASSWORD', '')
        )


@dataclass
class TableSyncConfig:
    table_name: str
    sync_enabled: bool = True
    sync_type: SyncType = SyncType.INCREMENTAL
    sync_direction: SyncDirection = SyncDirection.BOTH
    last_sync_time: Optional[str] = None
    last_sync_position: Optional[str] = None
    priority: int = 0
    conflict_resolution: ConflictResolution = ConflictResolution.REMOTE_WINS


class SyncConfig:
    def __init__(self):
        self.enabled = os.environ.get('DB_SYNC_ENABLED', 'False').lower() == 'true'
        self.interval = int(os.environ.get('DB_SYNC_INTERVAL', '60'))
        self.direction = SyncDirection(os.environ.get('DB_SYNC_DIRECTION', 'BOTH'))
        self.sync_type = SyncType(os.environ.get('DB_SYNC_TYPE', 'INCREMENTAL'))
        
        self.remote_db = DatabaseConfig.from_env('DB_REMOTE')
        self.local_db = DatabaseConfig.from_env('DB_LOCAL')
        
        self.tables: List[TableSyncConfig] = []
        self._load_table_configs()
    
    def _load_table_configs(self):
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT table_name, sync_enabled, sync_type, sync_direction, '
                              'last_sync_time, last_sync_position, priority, conflict_resolution '
                              'FROM db_sync_config ORDER BY priority DESC')
                results = cursor.fetchall()
                
                for row in results:
                    self.tables.append(TableSyncConfig(
                        table_name=row[0],
                        sync_enabled=bool(row[1]),
                        sync_type=SyncType(row[2]),
                        sync_direction=SyncDirection(row[3]),
                        last_sync_time=row[4],
                        last_sync_position=row[5],
                        priority=row[6],
                        conflict_resolution=ConflictResolution(row[7])
                    ))
        except Exception as e:
            print(f"加载表同步配置失败: {e}")
    
    def get_enabled_tables(self) -> List[TableSyncConfig]:
        return [t for t in self.tables if t.sync_enabled]
    
    def get_table_config(self, table_name: str) -> Optional[TableSyncConfig]:
        for table in self.tables:
            if table.table_name == table_name:
                return table
        return None