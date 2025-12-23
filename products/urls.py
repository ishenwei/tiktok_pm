# products/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 使用 DefaultRouter 自动生成标准的 CRUD 路由 (GET/POST/PUT/DELETE)
router = DefaultRouter()
# 注册 ProductViewSet，生成 /products/ 和 /products/{id}/ 路由
router.register(r'products', views.ProductViewSet)
# 注册 ProductVariationViewSet，生成 /variations/ 和 /variations/{id}/ 路由
router.register(r'variations', views.ProductVariationViewSet)

# DRF 最佳实践：使用 ViewSet 和 Router 自动构建 API
urlpatterns = [
    path('', include(router.urls)),

    # 🌟 新增：n8n 回调专用接口
    path('api/update_product/', views.update_product_api, name='api_update_product'),

    # (可选) 如果你需要通过 URL 触发 n8n 分析，可以保留之前的路由
    # path('n8n-analyze/<int:product_id>/', views.n8n_analyze_view, name='n8n_analyze'),
]