#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiktok_pm_project.settings')
django.setup()

from products.models import Product, AIContentItem


class DatabaseStorageChecker:
    """数据库存储检查工具"""
    
    @staticmethod
    def check_product_storage(product_id):
        """检查产品存储"""
        try:
            product = Product.objects.get(source_id=product_id)
            print(f"✓ 找到产品: {product.title} (ID: {product.id}, source_id: {product.source_id})")
            return product
        except Product.DoesNotExist:
            print(f"✗ 未找到产品 (source_id: {product_id})")
            return None
    
    @staticmethod
    def check_ai_content_storage(product):
        """检查AI内容存储"""
        ai_items = AIContentItem.objects.filter(product=product).order_by('id')
        print(f"\n找到 {ai_items.count()} 个AI内容项:")
        print("=" * 80)
        
        for item in ai_items:
            print(f"\nID: {item.id}")
            print(f"类型: {item.content_type}")
            print(f"中文内容长度: {len(item.content_zh) if item.content_zh else 0} 字符")
            print(f"英文内容长度: {len(item.content_en) if item.content_en else 0} 字符")
            print(f"中文内容预览: {item.content_zh[:100] if item.content_zh else 'None'}...")
            print(f"英文内容预览: {item.content_en[:100] if item.content_en else 'None'}...")
            print("-" * 80)
        
        return ai_items
    
    @staticmethod
    def show_content_type_stats(ai_items):
        """显示内容类型统计"""
        print("\n\n按类型统计:")
        print("=" * 80)
        content_types = ['desc', 'script', 'voice', 'img_prompt']
        for ct in content_types:
            count = ai_items.filter(content_type=ct).count()
            print(f"{ct}: {count} 项")


def check_database_storage(product_id):
    """检查数据库存储"""
    print("=" * 80)
    print("检查数据库中的AI内容存储情况")
    print("=" * 80)
    
    checker = DatabaseStorageChecker()
    
    product = checker.check_product_storage(product_id)
    if not product:
        return False
    
    ai_items = checker.check_ai_content_storage(product)
    checker.show_content_type_stats(ai_items)
    
    print("\n" + "=" * 80)
    print("检查完成！")
    print("=" * 80)
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='检查数据库存储')
    parser.add_argument('--product-id', type=str, required=True, help='产品ID')
    
    args = parser.parse_args()
    
    check_database_storage(args.product_id)
