#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiktok_pm_project.settings')
django.setup()

from django.db import connection


class DatabaseCleaner:
    """数据库清理工具"""
    
    @staticmethod
    def get_tables_to_clean():
        """获取需要清理的表列表（按外键依赖顺序）"""
        return [
            'product_images',
            'product_videos',
            'product_variations',
            'product_reviews',
            'product_tags',
            'ai_content_items',
            'products',
            'stores'
        ]
    
    @staticmethod
    def clean_table(table_name, confirm=True):
        """清理指定表的数据"""
        if confirm:
            response = input(f"确认要清理表 {table_name} 的所有数据吗？(yes/no): ")
            if response.lower() != 'yes':
                print(f"跳过表 {table_name}")
                return False
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print(f"表 {table_name} 已经是空的")
                    return True
                
                print(f"清理表 {table_name} 中的 {count} 条记录...")
                
                cursor.execute(f'TRUNCATE TABLE {table_name}')
                connection.commit()
                
                print(f"✓ 表 {table_name} 清理完成")
                return True
        except Exception as e:
            print(f"✗ 清理表 {table_name} 失败: {e}")
            connection.rollback()
            return False
    
    @staticmethod
    def clean_all_tables(confirm=True):
        """清理所有表的数据"""
        print("=" * 80)
        print("清理本地数据库")
        print("=" * 80)
        
        tables = DatabaseCleaner.get_tables_to_clean()
        
        print("\n将要清理以下表的数据:")
        for table in tables:
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} 条记录")
        
        if confirm:
            response = input("\n确认要清理所有表的数据吗？(yes/no): ")
            if response.lower() != 'yes':
                print("取消清理操作")
                return False
        
        print("\n开始清理...")
        print("-" * 80)
        
        success = True
        for table in tables:
            if not DatabaseCleaner.clean_table(table, confirm=False):
                success = False
                break
        
        print("-" * 80)
        
        if success:
            print("\n✓ 所有表清理完成")
        else:
            print("\n✗ 清理过程中出现错误")
        
        return success
    
    @staticmethod
    def verify_clean():
        """验证清理结果"""
        print("\n" + "=" * 80)
        print("验证清理结果")
        print("=" * 80)
        
        tables = DatabaseCleaner.get_tables_to_clean()
        
        all_empty = True
        for table in tables:
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print(f"✓ {table}: 空")
                else:
                    print(f"✗ {table}: 仍有 {count} 条记录")
                    all_empty = False
        
        print("\n" + "=" * 80)
        if all_empty:
            print("✓ 所有表已成功清理")
        else:
            print("✗ 部分表仍有数据")
        print("=" * 80)
        
        return all_empty


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清理本地数据库')
    parser.add_argument('--table', type=str, help='清理指定的表')
    parser.add_argument('--all', action='store_true', help='清理所有表')
    parser.add_argument('--no-confirm', action='store_true', help='跳过确认提示')
    parser.add_argument('--verify', action='store_true', help='验证清理结果')
    
    args = parser.parse_args()
    
    if args.verify:
        DatabaseCleaner.verify_clean()
    elif args.all:
        DatabaseCleaner.clean_all_tables(confirm=not args.no_confirm)
    elif args.table:
        DatabaseCleaner.clean_table(args.table, confirm=not args.no_confirm)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
