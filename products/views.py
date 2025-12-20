from django.shortcuts import render, redirect
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django import forms
from django.contrib import messages

# 🌟 1. 导入 admin 模块 (用于获取 sidebar context)
from django.contrib import admin

# 导入 django-q 任务调度器
from django_q.tasks import async_task

# 导入模型和序列化器
from .models import Product, ProductVariation
from .serializers import ProductSerializer, ProductVariationSerializer

# 导入任务函数
from .tasks import trigger_bright_data_task


class ProductViewSet(viewsets.ModelViewSet):
    """
    提供 Product 资源的 CRUD 操作 API。
    实现：快速搜索 (要求 3.8)，多条件过滤 (要求 3.9)
    """
    queryset = Product.objects.all().order_by('-updated_at')
    serializer_class = ProductSerializer

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

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'sku', 'stock']
    search_fields = ['=sku', 'product__source_id']


# ----------------------------------------------------
# Form 定义
# ----------------------------------------------------
class ProductUrlsForm(forms.Form):
    # 定义模式选项
    MODE_CHOICES = [
        ('url', '1. Collect by URL (单个产品链接)'),
        ('category', '2. Discover by Category (单个分类链接)'),
        ('shop', '3. Discover by Shop (单个店铺链接)'),
        ('keyword', '4. Discover by Keyword (单个关键词)'),
    ]

    collection_mode = forms.ChoiceField(
        label="选择采集方式",
        choices=MODE_CHOICES,
        widget=forms.RadioSelect,
        initial='url'
    )

    product_urls = forms.CharField(
        label="产品 URL 列表",
        widget=forms.Textarea(attrs={'rows': 10, 'placeholder': '一行一个 TikTok 产品 URL'}),
        help_text="请输入要抓取的 TikTok 产品完整 URL，每行一个。"
    )

    def clean_product_urls(self):
        """清理并转换多行文本为 URL 列表，并过滤空行。"""
        raw_text = self.cleaned_data['product_urls']
        urls = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not urls:
            raise forms.ValidationError("请输入至少一个有效的 URL。")
        return urls


# ----------------------------------------------------
# 🌟 View 定义 (已修改支持 Sidebar)
# ----------------------------------------------------
def product_fetch_view(request):
    """
    自定义 Admin 视图，用于接收 URL 列表并触发异步产品抓取任务。
    """
    if request.method == 'POST':
        form = ProductUrlsForm(request.POST)
        if form.is_valid():
            urls_list = form.cleaned_data['product_urls']
            collection_mode = form.cleaned_data['collection_mode']
            print("collection_mode: ", collection_mode)

            # 触发异步任务
            async_task(
                trigger_bright_data_task,
                urls_list, collection_mode,
                hook='products.tasks.log_task_completion',
            )

            messages.success(request, f"成功提交 {len(urls_list)} 个任务。任务已转入后台异步处理。")

            # 重定向回 Products 列表页
            return redirect('admin:products_product_changelist')
    else:
        form = ProductUrlsForm()

    # 🌟 核心修改：构建包含 Admin Context 的数据字典
    context = {
        'title': 'TikTok 产品数据抓取',  # 页面标题
        'form': form,
        'has_permission': True,
        # 使用 Product._meta 让模板正确识别 App 和 Model 名称 (用于面包屑)
        'opts': Product._meta,
    }

    # 🌟 关键：注入 available_apps 等全局 Admin 数据
    # 没有这一行，侧边栏 (Sidebar) 就不会显示
    context.update(admin.site.each_context(request))

    return render(request, 'admin/product_fetch.html', context)