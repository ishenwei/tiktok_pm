from django.shortcuts import render

# Create your views here.
# products/views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Product, ProductVariation
from .serializers import ProductSerializer, ProductVariationSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class ProductViewSet(viewsets.ModelViewSet):
    """
    提供 Product 资源的 CRUD 操作 API。
    实现：快速搜索 (要求 3.8)，多条件过滤 (要求 3.9)
    """
    queryset = Product.objects.all().order_by('-updated_at')
    serializer_class = ProductSerializer

    # 限制只有认证用户才能访问 API
    # permission_classes = [IsAuthenticated]

    # 启用过滤和搜索后端
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]

    # 启用字段过滤（多条件过滤）
    filterset_fields = [
        'available',
        'In_stock',
        'category',
        'seller_id',
        'final_price',
    ]

    # 启用快速搜索 (要求 3.8)
    search_fields = [
        '=source_id',  # 精确匹配
        'title',
        'store_name',
        'description'
    ]

    # 可选：自定义查询集以提高性能
    def get_queryset(self):
        # 预加载关联数据以解决 N+1 查询问题
        return Product.objects.all().select_related().prefetch_related(
            'images', 'variations', 'videos_list'
        ).order_by('-updated_at')


class ProductVariationViewSet(viewsets.ModelViewSet):
    """
    提供 ProductVariation 资源的 CRUD 操作 API。
    """
    queryset = ProductVariation.objects.all()
    serializer_class = ProductVariationSerializer

    # 启用字段过滤
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'sku', 'stock']
    search_fields = ['=sku', 'product__source_id']