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
# [您的项目名]/urls.py (tiktok_pm_project/urls.py)
# tiktok_pm_project/urls.py (推荐的修复方案)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls), # <--- 保持默认，不要包装！
    path('api/', include('products.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# 🌟 关键：使用 MEDIA_URL 和 MEDIA_ROOT 服务动态文件 🌟
if settings.DEBUG:
    print("\n--- URL Patterns ---")
    for pattern in urlpatterns:
        # 打印所有 URL 模式，包括服务 media/data 的模式
        print(pattern)
    print("--- End Patterns ---\n")
    # 确保 MEDIA_URL 和 MEDIA_ROOT 已经在 settings.py 中配置
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)