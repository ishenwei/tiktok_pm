import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiktok_pm_project.settings')
django.setup()

from django.db import connection
import pymysql


class DatabaseTool:
    """数据库工具基类"""
    
    @staticmethod
    def get_local_connection():
        """获取本地数据库连接"""
        return connection
    
    @staticmethod
    def get_remote_connection():
        """获取远程数据库连接"""
        return pymysql.connect(
            host='192.168.3.17',
            port=3307,
            user='shenwei',
            password='!Abcde12345',
            database='tiktok_products_dev',
            charset='utf8mb4'
        )
    
    @staticmethod
    def execute_query(query, params=None, use_remote=False):
        """执行查询"""
        if use_remote:
            conn = DatabaseTool.get_remote_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
            finally:
                conn.close()
        else:
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
    
    @staticmethod
    def execute_update(query, params=None, use_remote=False):
        """执行更新操作"""
        if use_remote:
            conn = DatabaseTool.get_remote_connection()
            try:
                with conn.cursor() as cursor:
                    result = cursor.execute(query, params or ())
                    conn.commit()
                    return result
            finally:
                conn.close()
        else:
            with connection.cursor() as cursor:
                result = cursor.execute(query, params or ())
                connection.commit()
                return result


class SyncConfigTool(DatabaseTool):
    """同步配置工具"""
    
    @staticmethod
    def get_sync_config():
        """获取同步配置"""
        query = '''
            SELECT id, table_name, sync_enabled, sync_type, sync_direction, 
                   last_sync_time, priority, conflict_resolution 
            FROM db_sync_config 
            ORDER BY priority DESC
        '''
        return SyncConfigTool.execute_query(query)
    
    @staticmethod
    def get_table_structure(table_name, use_remote=False):
        """获取表结构"""
        query = f'DESCRIBE {table_name}'
        return SyncConfigTool.execute_query(query, use_remote=use_remote)
    
    @staticmethod
    def get_row_count(table_name, use_remote=False):
        """获取表行数"""
        query = f'SELECT COUNT(*) FROM {table_name}'
        result = SyncConfigTool.execute_query(query, use_remote=use_remote)
        return result[0][0] if result else 0
    
    @staticmethod
    def print_sync_config():
        """打印同步配置"""
        results = SyncConfigTool.get_sync_config()
        print('db_sync_config 表内容:')
        print('ID\t表名\t启用\t类型\t方向\t最后同步时间\t优先级\t冲突解决')
        print('-' * 120)
        for row in results:
            print(f'{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\t{row[4]}\t{row[5]}\t{row[6]}\t{row[7]}')
    
    @staticmethod
    def print_table_structure(table_name, use_remote=False):
        """打印表结构"""
        results = SyncConfigTool.get_table_structure(table_name, use_remote=use_remote)
        db_type = '远程' if use_remote else '本地'
        print(f'{db_type}数据库 {table_name} 表结构:')
        print('Field\tType\tNull\tKey\tDefault\tExtra')
        print('-' * 100)
        for row in results:
            print(f'{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\t{row[4]}\t{row[5]}')


class DatabaseInfoTool(DatabaseTool):
    """数据库信息工具"""
    
    @staticmethod
    def get_database_version(use_remote=False):
        """获取数据库版本"""
        query = 'SELECT VERSION()'
        result = DatabaseInfoTool.execute_query(query, use_remote=use_remote)
        return result[0][0] if result else None
    
    @staticmethod
    def get_all_tables(use_remote=False):
        """获取所有表"""
        query = 'SHOW TABLES'
        return DatabaseInfoTool.execute_query(query, use_remote=use_remote)
    
    @staticmethod
    def print_database_info(use_remote=False):
        """打印数据库信息"""
        db_type = '远程' if use_remote else '本地'
        print(f'{db_type}数据库信息:')
        
        version = DatabaseInfoTool.get_database_version(use_remote)
        print(f'  数据库版本: {version}')
        
        tables = DatabaseInfoTool.get_all_tables(use_remote)
        print(f'  数据库表数量: {len(tables)}')
        
        if tables:
            print('  表名列表:')
            for table in tables:
                print(f'    - {table[0]}')
