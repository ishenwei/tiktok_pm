#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiktok_pm_project.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connections
from tiktok_pm_project.db_sync.connection import DatabaseConnection, DatabaseConfig


class DataIntegrityVerifier:
    """数据完整性验证器"""

    def __init__(self):
        self.tables = [
            'stores', 'products', 'ai_content_items', 'product_tags', 
            'product_reviews', 'product_variations', 'product_videos', 'product_images'
        ]
        self.local_db = None
        self.remote_db = None

    def create_connections(self):
        """创建数据库连接"""
        local_config = DatabaseConfig(
            host=os.getenv('DB_LOCAL_HOST', 'mariadb'),
            port=int(os.getenv('DB_LOCAL_PORT', 3306)),
            user=os.getenv('DB_LOCAL_USER', 'shenwei'),
            password=os.getenv('DB_LOCAL_PASSWORD', '!Abcde12345'),
            name=os.getenv('DB_LOCAL_NAME', 'tiktok_products_dev')
        )
        self.local_db = DatabaseConnection(local_config)

        remote_config = DatabaseConfig(
            host=os.getenv('DB_REMOTE_HOST', '192.168.3.17'),
            port=int(os.getenv('DB_REMOTE_PORT', 3307)),
            user=os.getenv('DB_REMOTE_USER', 'shenwei'),
            password=os.getenv('DB_REMOTE_PASSWORD', '!Abcde12345'),
            name=os.getenv('DB_REMOTE_NAME', 'tiktok_products_dev')
        )
        self.remote_db = DatabaseConnection(remote_config)

    def close_connections(self):
        """关闭数据库连接"""
        if self.local_db:
            self.local_db.disconnect()
        if self.remote_db:
            self.remote_db.disconnect()

    def verify_table(self, table_name):
        """验证单个表"""
        print(f"\n验证表: {table_name}")
        print("-" * 80)
        
        all_match = True
        
        try:
            local_count = self.local_db.get_row_count(table_name)
            remote_count = self.remote_db.get_row_count(table_name)
            
            print(f"本地记录数: {local_count}")
            print(f"远程记录数: {remote_count}")
            
            if local_count == remote_count:
                print(f"✓ 记录数一致")
            else:
                print(f"✗ 记录数不一致 (差异: {abs(local_count - remote_count)})")
                all_match = False
            
            local_max_id = self.local_db.get_max_id(table_name)
            remote_max_id = self.remote_db.get_max_id(table_name)
            
            print(f"本地最大ID: {local_max_id}")
            print(f"远程最大ID: {remote_max_id}")
            
            if local_max_id == remote_max_id:
                print(f"✓ 最大ID一致")
            else:
                print(f"✗ 最大ID不一致")
                all_match = False
            
            schema_match = True
            local_schema = self.local_db.get_table_schema(table_name)
            remote_schema = self.remote_db.get_table_schema(table_name)
            
            if len(local_schema) == len(remote_schema):
                print(f"✓ 字段数量一致 ({len(local_schema)})")
            else:
                print(f"✗ 字段数量不一致 (本地: {len(local_schema)}, 远程: {len(remote_schema)})")
                schema_match = False
                all_match = False
            
            if schema_match:
                for i, (local_col, remote_col) in enumerate(zip(local_schema, remote_schema)):
                    if local_col['COLUMN_NAME'] != remote_col['COLUMN_NAME']:
                        print(f"✗ 字段名称不一致: {local_col['COLUMN_NAME']} vs {remote_col['COLUMN_NAME']}")
                        all_match = False
                        break
                else:
                    print(f"✓ 字段结构一致")
            
        except Exception as e:
            print(f"✗ 验证失败: {e}")
            all_match = False
        
        return all_match

    def verify(self):
        """执行完整验证"""
        print("=" * 80)
        print("数据完整性验证")
        print("=" * 80)
        
        try:
            self.create_connections()
            
            all_match = True
            for table in self.tables:
                if not self.verify_table(table):
                    all_match = False
            
            print("\n" + "=" * 80)
            if all_match:
                print("数据完整性验证: 全部通过 ✓")
            else:
                print("数据完整性验证: 存在差异 ✗")
            print("=" * 80)
            
            return all_match
            
        except Exception as e:
            print(f"✗ 验证过程中发生错误: {e}")
            return False
        finally:
            self.close_connections()


class ServiceAccessTester:
    """服务访问测试器"""

    def __init__(self):
        self.models = {
            'Store': 'Store',
            'Product': 'Product',
            'ProductTagDefinition': 'ProductTagDefinition',
            'ProductReview': 'ProductReview',
            'ProductVariation': 'ProductVariation',
            'ProductVideo': 'ProductVideo',
            'ProductImage': 'ProductImage'
        }

    def test_model(self, model_name, model_class):
        """测试单个模型"""
        print(f"\n测试 {model_name} 模型:")
        try:
            count = model_class.objects.count()
            print(f"✓ {model_name} 记录数: {count}")
            return True
        except Exception as e:
            print(f"✗ {model_name} 测试失败: {e}")
            return False

    def test_product_details(self):
        """测试产品详细信息"""
        print("\n测试数据查询:")
        try:
            from products.models import Product
            
            first_product = Product.objects.first()
            if first_product:
                print(f"✓ 成功查询到第一个产品: {first_product.title}")
                print(f"  - ID: {first_product.id}")
                print(f"  - Store: {first_product.store.name if first_product.store else 'N/A'}")
                print(f"  - Price: {first_product.final_price}")
                
                variations = first_product.product_variations.all()
                print(f"  - 变体数量: {variations.count()}")
                
                images = first_product.product_images.all()
                print(f"  - 图片数量: {images.count()}")
                
                return True
            else:
                print("⚠ 没有找到产品数据")
                return True
        except Exception as e:
            print(f"✗ 产品详细信息测试失败: {e}")
            return False

    def test(self):
        """执行完整测试"""
        print("\n" + "=" * 80)
        print("服务访问测试")
        print("=" * 80)
        
        try:
            from products.models import (
                Store, Product, ProductTagDefinition, ProductReview,
                ProductVariation, ProductVideo, ProductImage
            )
            
            model_classes = {
                'Store': Store,
                'Product': Product,
                'ProductTagDefinition': ProductTagDefinition,
                'ProductReview': ProductReview,
                'ProductVariation': ProductVariation,
                'ProductVideo': ProductVideo,
                'ProductImage': ProductImage
            }
            
            all_pass = True
            for model_name, model_class in model_classes.items():
                if not self.test_model(model_name, model_class):
                    all_pass = False
            
            if not self.test_product_details():
                all_pass = False
            
            print("\n" + "=" * 80)
            if all_pass:
                print("服务访问测试: 全部通过 ✓")
            else:
                print("服务访问测试: 部分失败 ✗")
            print("=" * 80)
            
            return all_pass
            
        except Exception as e:
            print(f"\n✗ 服务访问测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    print("\n开始数据完整性验证和服务访问测试...\n")
    
    integrity_verifier = DataIntegrityVerifier()
    service_tester = ServiceAccessTester()
    
    integrity_ok = integrity_verifier.verify()
    service_ok = service_tester.test()
    
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"数据完整性验证: {'通过 ✓' if integrity_ok else '失败 ✗'}")
    print(f"服务访问测试: {'通过 ✓' if service_ok else '失败 ✗'}")
    
    if integrity_ok and service_ok:
        print("\n所有测试通过！数据同步成功且服务正常。")
        sys.exit(0)
    else:
        print("\n部分测试失败，请检查上述错误信息。")
        sys.exit(1)


if __name__ == '__main__':
    main()