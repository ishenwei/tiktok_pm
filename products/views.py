from django.shortcuts import render

# Create your views here.
# products/views.py

from rest_framework import viewsets
from .models import Product, ProductVariation
from .serializers import ProductSerializer, ProductVariationSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import render, redirect
from django import forms
from django.contrib import messages
# 导入 django-q 任务调度器
from django_q.tasks import async_task
# 导入触发 Bright Data 任务的函数 (该函数现在将接收一个 URL 列表)
from .tasks import trigger_bright_data_task

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


# ----------------------------------------------------
# 1. 定义表单 (使用 Textarea 控件)
# ----------------------------------------------------
class ProductUrlsForm(forms.Form):
    product_urls = forms.CharField(
        label="产品 URL 列表",
        widget=forms.Textarea(attrs={'rows': 10, 'placeholder': '一行一个 TikTok 产品 URL'}),
        help_text="请输入要抓取的 TikTok 产品完整 URL，每行一个。"
    )

    def clean_product_urls(self):
        """清理并转换多行文本为 URL 列表，并过滤空行。"""
        raw_text = self.cleaned_data['product_urls']

        # 1. 按行分割
        # 2. 移除每行首尾空格
        # 3. 过滤掉空行
        urls = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not urls:
            raise forms.ValidationError("请输入至少一个有效的 URL。")

        # 可以在此处添加更复杂的 URL 格式验证
        # ...

        # 返回 URL 列表
        return urls


# ----------------------------------------------------
# 2. 定义视图
# ----------------------------------------------------
def product_fetch_view(request):
    """
    自定义 Admin 视图，用于接收 URL 列表并触发异步产品抓取任务。
    """
    if request.method == 'POST':
        form = ProductUrlsForm(request.POST)
        if form.is_valid():
            # 获取清理后的 URL 列表
            urls_list = form.cleaned_data['product_urls']

            # ----------------------------------------------------
            # 🌟 核心操作：将 URL 列表传递给异步任务
            # ----------------------------------------------------
            # 注意: trigger_bright_data_task 的签名必须接受这个列表作为参数
            async_task(
                trigger_bright_data_task,
                urls_list,  # 传递 URL 列表
                hook='products.tasks.log_task_completion',
            )

            # 成功消息
            messages.success(request, f"成功提交 {len(urls_list)} 个产品URL任务。任务已转入后台异步处理。")

            # 重定向回 Products 列表页
            url_name = 'admin:products_product_changelist'
            return redirect(url_name)
    else:
        # GET 请求：显示空表单
        form = ProductUrlsForm()

    # 渲染模板
    return render(request, 'admin/product_fetch.html', context={
        'title': '触发产品数据抓取',
        'form': form,
        'has_permission': True,
        'opts': {'verbose_name_plural': '产品'},
    })