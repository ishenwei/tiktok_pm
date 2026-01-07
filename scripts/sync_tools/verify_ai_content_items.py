#!/usr/bin/env python3
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiktok_pm_project.settings')
django.setup()

from django.db import connection


class AIContentItemsVerifier:
    """AI内容项验证器"""

    def __init__(self):
        self.local_conn = connection
        self.remote_conn = None

    def connect_remote(self):
        """连接远程数据库"""
        try:
            import pymysql
            self.remote_conn = pymysql.connect(
                host=os.getenv('DB_REMOTE_HOST', '192.168.3.17'),
                port=int(os.getenv('DB_REMOTE_PORT', 3307)),
                user=os.getenv('DB_REMOTE_USER', 'shenwei'),
                password=os.getenv('DB_REMOTE_PASSWORD', '!Abcde12345'),
                database=os.getenv('DB_REMOTE_NAME', 'tiktok_products_dev'),
                charset='utf8mb4'
            )
            return True
        except Exception as e:
            print(f"✗ 远程数据库连接失败: {e}")
            return False

    def disconnect_remote(self):
        """断开远程数据库连接"""
        if self.remote_conn:
            self.remote_conn.close()
            self.remote_conn = None

    def get_local_data(self):
        """获取本地数据库数据"""
        with self.local_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ai_content_items ORDER BY id")
            results = cursor.fetchall()
            cursor.execute("DESCRIBE ai_content_items")
            columns = [row[0] for row in cursor.fetchall()]
            return results, columns

    def get_remote_data(self):
        """获取远程数据库数据"""
        if not self.remote_conn:
            return None, None
        
        with self.remote_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ai_content_items ORDER BY id")
            results = cursor.fetchall()
            return results, None

    def verify_record_count(self, local_count, remote_count):
        """验证记录数"""
        if local_count == remote_count:
            print(f"   ✓ 记录数一致: {local_count} 条")
            return True
        else:
            print(f"   ✗ 记录数不一致: 本地 {local_count} 条, 远程 {remote_count} 条")
            return False

    def verify_records(self, local_results, remote_results):
        """验证每条记录"""
        all_match = True
        for i, (local_row, remote_row) in enumerate(zip(local_results, remote_results)):
            if local_row == remote_row:
                print(f"   ✓ 记录 {i+1} 数据一致 (ID: {local_row[0]})")
            else:
                print(f"   ✗ 记录 {i+1} 数据不一致 (ID: {local_row[0]})")
                all_match = False
        return all_match

    def verify_sync_config(self):
        """验证同步配置"""
        with self.local_conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM db_sync_config WHERE table_name = 'ai_content_items'"
            )
            config = cursor.fetchone()
            if config:
                print(f"   ✓ ai_content_items表已在同步配置中")
                print(f"      - 优先级: {config[3]}")
                print(f"      - 同步方向: {config[1]}")
                print(f"      - 同步类型: {config[2]}")
                print(f"      - 同步启用: {'是' if config[4] else '否'}")
                return True
            else:
                print(f"   ✗ ai_content_items表未在同步配置中")
                return False

    def verify_foreign_keys(self):
        """验证外键关系"""
        with self.local_conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM ai_content_items a
                LEFT JOIN products p ON a.product_id = p.id
                WHERE p.id IS NULL
            """)
            orphan_count = cursor.fetchone()[0]
            if orphan_count == 0:
                print(f"   ✓ 所有ai_content_items记录都有对应的产品")
                return True
            else:
                print(f"   ✗ 发现 {orphan_count} 条孤立的ai_content_items记录")
                return False

    def verify_data_integrity(self):
        """验证数据完整性"""
        with self.local_conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM ai_content_items
                WHERE id IS NULL OR ai_model IS NULL OR content_type IS NULL
                OR content_zh IS NULL OR content_en IS NULL OR product_id IS NULL
            """)
            null_count = cursor.fetchone()[0]
            if null_count == 0:
                print(f"   ✓ 所有必填字段都有值")
                return True
            else:
                print(f"   ✗ 发现 {null_count} 条记录的必填字段为空")
                return False

    def verify(self):
        """执行完整验证"""
        print("=" * 80)
        print("ai_content_items表数据一致性验证")
        print("=" * 80)

        all_match = True

        print("\n1. 从本地数据库获取ai_content_items数据...")
        local_results, columns = self.get_local_data()
        local_count = len(local_results)
        print(f"   本地数据库记录数: {local_count}")
        print(f"   表结构列数: {len(columns)}")
        print(f"   列名: {', '.join(columns)}")

        print("\n2. 从远程数据库获取ai_content_items数据...")
        if not self.connect_remote():
            return False
        
        try:
            remote_results, _ = self.get_remote_data()
            remote_count = len(remote_results)
            print(f"   远程数据库记录数: {remote_count}")

            print("\n3. 比较记录数...")
            if not self.verify_record_count(local_count, remote_count):
                all_match = False

            print("\n4. 比较每条记录的详细信息...")
            if not self.verify_records(local_results, remote_results):
                all_match = False

            print("\n5. 验证同步配置...")
            if not self.verify_sync_config():
                all_match = False

            print("\n6. 验证外键关系...")
            if not self.verify_foreign_keys():
                all_match = False

            print("\n7. 验证数据完整性...")
            if not self.verify_data_integrity():
                all_match = False

        finally:
            self.disconnect_remote()

        print("\n" + "=" * 80)
        if all_match:
            print("✓ 数据一致性验证通过")
        else:
            print("✗ 数据一致性验证失败")
        print("=" * 80)

        return all_match


def main():
    """主函数"""
    verifier = AIContentItemsVerifier()
    success = verifier.verify()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()