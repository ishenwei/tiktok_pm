import pymysql
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from .config import DatabaseConfig


class DatabaseConnection:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
    
    def connect(self):
        if not self.connection or not self.connection.open:
            self.connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        return self.connection
    
    def disconnect(self):
        if self.connection and self.connection.open:
            self.connection.close()
            self.connection = None
    
    @contextmanager
    def get_cursor(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        with self.get_cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    
    def execute_update(self, sql: str, params: Optional[tuple] = None) -> int:
        with self.get_cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.rowcount
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        sql = """
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, 
                   COLUMN_DEFAULT, EXTRA, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(sql, (self.config.name, table_name))
    
    def get_table_data(self, table_name: str, 
                      where_clause: Optional[str] = None, 
                      params: Optional[tuple] = None,
                      limit: Optional[int] = None,
                      offset: Optional[int] = None) -> List[Dict[str, Any]]:
        sql = f"SELECT * FROM {table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"
        return self.execute_query(sql, params)
    
    def get_row_count(self, table_name: str) -> int:
        result = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
        return result[0]['count'] if result else 0
    
    def get_max_id(self, table_name: str, id_column: str = 'id') -> Optional[int]:
        result = self.execute_query(f"SELECT MAX({id_column}) as max_id FROM {table_name}")
        return result[0]['max_id'] if result and result[0]['max_id'] else None
    
    def get_last_update_time(self, table_name: str, 
                           update_column: str = 'updated_at') -> Optional[str]:
        result = self.execute_query(
            f"SELECT MAX({update_column}) as last_update FROM {table_name}"
        )
        return result[0]['last_update'] if result and result[0]['last_update'] else None
    
    def insert_data(self, table_name: str, data: Dict[str, Any]) -> int:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.execute_update(sql, tuple(data.values()))
    
    def update_data(self, table_name: str, data: Dict[str, Any], 
                   where_clause: str, params: tuple) -> int:
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        return self.execute_update(sql, tuple(data.values()) + params)
    
    def delete_data(self, table_name: str, where_clause: str, params: tuple) -> int:
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        return self.execute_update(sql, params)
    
    def batch_insert(self, table_name: str, data_list: List[Dict[str, Any]]) -> int:
        if not data_list:
            return 0
        
        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['%s'] * len(data_list[0]))
        
        update_columns = ', '.join([f"{col} = VALUES({col})" for col in data_list[0].keys() if col != 'id'])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_columns}"
        
        total_rows = 0
        with self.get_cursor() as cursor:
            for data in data_list:
                cursor.execute(sql, tuple(data.values()))
                total_rows += cursor.rowcount
        return total_rows
    
    def table_exists(self, table_name: str) -> bool:
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
            (self.config.name, table_name)
        )
        return result[0]['count'] > 0 if result else False