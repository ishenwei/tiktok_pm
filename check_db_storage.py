import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiktok_pm_project.settings')
django.setup()

from products.models import Product, AIContentItem

print("=" * 80)
print("检查数据库中的AI内容存储情况")
print("=" * 80)

# 查询测试产品
product_id = "1731500998159798308"
try:
    product = Product.objects.get(source_id=product_id)
    print(f"\n✅ 找到产品: {product.title} (ID: {product.id}, source_id: {product.source_id})")
except Product.DoesNotExist:
    print(f"\n❌ 未找到产品 (source_id: {product_id})")
    exit(1)

# 查询该产品的所有AI内容项
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

# 统计各类型的内容数量
print("\n\n按类型统计:")
print("=" * 80)
content_types = ['desc', 'script', 'voice', 'img_prompt']
for ct in content_types:
    count = ai_items.filter(content_type=ct).count()
    print(f"{ct}: {count} 项")

print("\n" + "=" * 80)
print("检查完成！")
print("=" * 80)
