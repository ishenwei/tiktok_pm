# products/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# 使用 DefaultRouter 自动生成标准的 CRUD 路由 (GET/POST/PUT/DELETE)
router = DefaultRouter()
# 注册 ProductViewSet，生成 /products/ 和 /products/{id}/ 路由
router.register(r"products", views.ProductViewSet)
# 注册 ProductVariationViewSet，生成 /variations/ 和 /variations/{id}/ 路由
router.register(r"variations", views.ProductVariationViewSet)

# DRF 最佳实践：使用 ViewSet 和 Router 自动构建 API
urlpatterns = [
    path("", include(router.urls)),
    # 🔴 修改前: path('api/update_product/', views.update_product_api, ...)
    # 🟢 修改后: 去掉 'api/'，因为主路由已经包含了它
    path("update_product/", views.update_product_api, name="update_product_api"),
    # 导出产品 JSON
    path("export/<int:product_id>/", views.export_product_json_view, name="export_product_json"),
    # n8n 分析功能
    path("n8n-analyze/<int:product_id>/", views.n8n_analyze_view, name="n8n_analyze"),
    # 产品抓取视图
    path("fetch/", views.product_fetch_view, name="product_fetch"),
]
