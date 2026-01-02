# products/serializers.py

from rest_framework import serializers

from .models import Product, ProductImage, ProductVariation, ProductVideo

# --- 辅助序列化器 (用于嵌套展示) ---


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image_type", "original_url", "zipline_url"]
        read_only_fields = ["id"]


class ProductVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVideo
        fields = ["id", "video_type", "original_url", "zipline_url"]
        read_only_fields = ["id"]


class ProductVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariation
        fields = ["id", "product", "sku", "final_price", "stock", "created_at"]
        read_only_fields = ["id", "created_at"]

    # --- 核心产品序列化器 (用于 Product API) ---


class ProductSerializer(serializers.ModelSerializer):
    # 将关联模型嵌套进来，方便 n8n 一次性获取所有信息
    images = ProductImageSerializer(many=True, read_only=True, source="product_images")
    variations = ProductVariationSerializer(many=True, read_only=True, source="product_variations")
    videos_list = ProductVideoSerializer(many=True, read_only=True, source="product_videos")

    class Meta:
        model = Product
        # 排除 'input', 'raw_json' 等大型或内部字段，简化常用 API 响应
        # 如果需要，可以创建 ProductDetailSerializer 来包含它们
        exclude = ["raw_json", "input", "timestamp"]

        # 确保 created_at, updated_at, source_id, seller_id 等关键字段可读
        read_only_fields = ["id", "created_at", "updated_at"]
