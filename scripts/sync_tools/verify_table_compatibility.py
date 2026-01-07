#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiktok_pm_project.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from tiktok_pm_project.db_sync.connection import DatabaseConnection, DatabaseConfig


class TableCompatibilityVerifier:
    """表兼容性验证器"""

    def __init__(self, table_name='ai_content_items'):
        self.table_name = table_name
        self.local_db = None
        self.remote_db = None

    def create_connections(self):
        """创建数据库连接"""
        local_config = DatabaseConfig(
            host=os.getenv('DB_LOCAL_HOST', 'mariadb'),
            port=int(os.getenv('DB_LOCAL_PORT', 3306)),
            name=os.getenv('DB_LOCAL_NAME', 'tiktok_products_dev'),
            user=os.getenv('DB_LOCAL_USER', 'shenwei'),
            password=os.getenv('DB_LOCAL_PASSWORD', '!Abcde12345')
        )
        self.local_db = DatabaseConnection(local_config)

        remote_config = DatabaseConfig(
            host=os.getenv('DB_REMOTE_HOST', '192.168.3.17'),
            port=int(os.getenv('DB_REMOTE_PORT', 3307)),
            name=os.getenv('DB_REMOTE_NAME', 'tiktok_products_dev'),
            user=os.getenv('DB_REMOTE_USER', 'shenwei'),
            password=os.getenv('DB_REMOTE_PASSWORD', '!Abcde12345')
        )
        self.remote_db = DatabaseConnection(remote_config)

    def close_connections(self):
        """关闭数据库连接"""
        if self.local_db:
            self.local_db.disconnect()
        if self.remote_db:
            self.remote_db.disconnect()

    def verify_table_exists(self):
        """验证表是否存在"""
        print("\n1. 检查表是否存在")
        print("-" * 80)
        
        local_exists = self.local_db.table_exists(self.table_name)
        remote_exists = self.remote_db.table_exists(self.table_name)
        
        print(f"本地数据库: {'✓ 存在' if local_exists else '✗ 不存在'}")
        print(f"远程数据库: {'✓ 存在' if remote_exists else '✗ 不存在'}")
        
        return local_exists and remote_exists

    def verify_table_structure(self):
        """验证表结构"""
        print("\n2. 比较表结构")
        print("-" * 80)
        
        local_columns = self.local_db.get_table_schema(self.table_name)
        remote_columns = self.remote_db.get_table_schema(self.table_name)
        
        print(f"\n本地表字段数: {len(local_columns)}")
        print(f"远程表字段数: {len(remote_columns)}")
        
        if len(local_columns) != len(remote_columns):
            print("✗ 字段数量不一致")
            return False
        
        print("✓ 字段数量一致")
        return True

    def verify_columns(self):
        """验证字段详细信息"""
        print("\n3. 字段详细对比")
        print("-" * 80)
        print(f"{'字段名':20} | {'本地类型':20} | {'远程类型':20} | {'状态'}")
        print("-" * 80)
        
        local_columns = self.local_db.get_table_schema(self.table_name)
        remote_columns = self.remote_db.get_table_schema(self.table_name)
        
        all_match = True
        for local_col, remote_col in zip(local_columns, remote_columns):
            field_name = local_col['COLUMN_NAME']
            local_type = local_col['COLUMN_TYPE']
            remote_type = remote_col['COLUMN_TYPE']
            
            match = local_type == remote_type
            status = '✓ 一致' if match else '✗ 不一致'
            
            print(f"{field_name:20} | {local_type:20} | {remote_type:20} | {status}")
            
            if not match:
                all_match = False
        
        return all_match

    def verify_row_count(self):
        """验证记录数"""
        print("\n4. 检查记录数")
        print("-" * 80)
        
        local_count = self.local_db.get_row_count(self.table_name)
        remote_count = self.remote_db.get_row_count(self.table_name)
        
        print(f"本地记录数: {local_count}")
        print(f"远程记录数: {remote_count}")
        
        if local_count != remote_count:
            print("⚠ 记录数不一致（这是正常的，同步后会一致）")
        else:
            print("✓ 记录数一致")

    def verify_indexes(self):
        """验证索引"""
        print("\n5. 检查索引")
        print("-" * 80)
        print("⚠ 索引检查跳过（需要额外实现）")

    def verify(self):
        """执行完整验证"""
        print("开始验证ai_content_items表的兼容性...")
        print("=" * 80)
        
        try:
            self.create_connections()
            
            if not self.verify_table_exists():
                print("\n✗ 表不存在，无法继续验证")
                return False
            
            if not self.verify_table_structure():
                return False
            
            if not self.verify_columns():
                print("\n✗ 字段类型不一致")
                return False
            
            print("\n✓ 所有字段类型一致")
            
            self.verify_row_count()
            self.verify_indexes()
            
            print("\n" + "=" * 80)
            print("表结构验证完成！")
            print("=" * 80)
            print("\n结论: ai_content_items表在源系统和目标系统之间的结构兼容 ✓")
            
            return True
            
        except Exception as e:
            print(f"\n✗ 验证过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.close_connections()


def main():
    """主函数"""
    verifier = TableCompatibilityVerifier('ai_content_items')
    success = verifier.verify()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()