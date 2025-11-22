"""
URL configuration for tiktok_pm_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
# 导入 csrf_exempt 装饰器
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # 1. 对 admin 禁用 CSRF 保护
    path('admin/', csrf_exempt(admin.site.urls)),

    # 将所有 API 路由包含进来
    path('api/', include('products.urls')),

    # 2. 对 DRF 认证路由禁用 CSRF 保护
    # 注意：我们必须对 include() 结果进行包装
    path('api-auth/', csrf_exempt(include('rest_framework.urls', namespace='rest_framework'))),
]