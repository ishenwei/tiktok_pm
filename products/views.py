import json
import requests  # <--- 确保安装了 requests: pip install requests
from django.shortcuts import render, redirect, get_object_or_404 # <--- 关键补充
from django.http import JsonResponse # <--- 导出 JSON 需要这个
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
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

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


# ============================================================
# 1. 导出 JSON 功能
# ============================================================
def export_product_json_view(request, product_id):
    """生成并下载产品的 JSON 文件"""
    product = get_object_or_404(Product, pk=product_id)

    # 提取数据 (抽取为通用函数以便复用)
    product_data = _extract_product_data(product)

    # 生成响应
    response = JsonResponse(product_data, json_dumps_params={'indent': 4, 'ensure_ascii': False})
    response['Content-Disposition'] = f'attachment; filename="product_{product.source_id}.json"'
    return response


# ============================================================
# 2. 调用 n8n 分析功能
# ============================================================
def n8n_analyze_view(request, product_id):
    """
    1. 生成产品 JSON
    2. 发送给 n8n Webhook
    3. 接收 n8n 返回的优化文案
    4. 更新 Product 的 description_1 和 description_2
    """
    product = get_object_or_404(Product, pk=product_id)
    product_data = _extract_product_data(product)

    n8n_webhook_url = getattr(settings, 'N8N_WEBHOOK_OPTIMIZE_PRODUCT_TEST_URL', None)

    try:
        # 发送请求给 n8n
        # timeout 设置为 30秒，防止 n8n 处理太久导致 Django 卡死
        response = requests.post(n8n_webhook_url, json=product_data, timeout=30)

        if response.status_code == 200:
            result = response.json()

            # 🌟 预期 n8n 返回格式: {"desc_1": "...", "desc_2": "..."}
            new_desc_1 = result.get('desc_1')
            new_desc_2 = result.get('desc_2')

            updated_fields = []
            if new_desc_1:
                product.description_1 = new_desc_1
                updated_fields.append("Description 1")

            if new_desc_2:
                product.description_2 = new_desc_2
                updated_fields.append("Description 2")

            if updated_fields:
                product.save()
                messages.success(request, f"✅ AI 优化成功！已更新: {', '.join(updated_fields)}")
            else:
                messages.warning(request, "⚠️ n8n 返回成功，但没有包含有效的 desc_1 或 desc_2 字段。")
        else:
            messages.error(request, f"❌ n8n 调用失败: HTTP {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"❌ 连接 n8n 发生错误: {str(e)}")

    # 操作完成后，重定向回产品详情页
    return redirect('admin:products_product_change', product_id)


# ============================================================
# 通用工具函数：提取产品数据
# ============================================================
def _extract_product_data(product):
    """构造标准化的产品数据字典"""

    # 获取图片列表
    images = [img.original_url for img in product.product_images.all() if img.original_url]

    return {
        "id": product.source_id,
        "title": product.title,
        "category": product.category,
        "url": product.url,
        "price": str(product.final_price),
        "description": product.description,  # 原始描述
        "description_detail": product.desc_detail,  # 详细描述
        "specifications": product.specifications,  # 规格参数
        "images": images,  # 图片 URL 列表
        # 如果有变体信息也可以加上
        # "variations": [...]
    }


# ============================================================
# 接收 n8n 回调 API (新增)
# ============================================================
@csrf_exempt  # 必须：允许 n8n 无 CSRF Token 访问
@require_POST  # 必须：只允许 POST 请求
def update_product_api(request):
    """
    供 n8n 调用的 Webhook 回调接口。
    接收 JSON: {"product_id": "...", "desc_1": "...", "api_key": "..."}
    """
    # 建议将密钥移至 settings.py，这里为了演示直接定义
    API_SECRET = "tk_n8n_update_2025_safe"

    try:
        data = json.loads(request.body)

        # 1. 安全校验
        req_key = data.get('api_key')
        if req_key != API_SECRET:
            return JsonResponse({'status': 'error', 'message': 'Invalid API Key'}, status=403)

        # 2. 获取参数
        # 注意：这里接收的是 product_id，对应你的 source_id (你在 _extract_product_data 里把 source_id 传给了 n8n)
        p_id = data.get('product_id')
        desc_1 = data.get('desc_1')

        # 如果 n8n 还能生成 desc_2，也可以接收
        desc_2 = data.get('desc_2')

        if not p_id:
            return JsonResponse({'status': 'error', 'message': 'Missing product_id'}, status=400)

        # 3. 查找产品
        # 优先尝试用 source_id 查找 (因为导出时你给 n8n 的是 source_id)
        product = Product.objects.filter(source_id=p_id).first()

        # 如果找不到，尝试用主键 ID 查找 (兼容性)
        if not product and str(p_id).isdigit():
            product = Product.objects.filter(pk=p_id).first()

        if not product:
            return JsonResponse({'status': 'error', 'message': f'Product {p_id} not found'}, status=404)

        # 4. 更新字段
        updated_fields = []
        if desc_1:
            product.description_1 = desc_1
            updated_fields.append('description_1')

        if desc_2:
            product.description_2 = desc_2
            updated_fields.append('description_2')

        if updated_fields:
            product.save()
            return JsonResponse({
                'status': 'success',
                'message': f'Updated {", ".join(updated_fields)} for product {p_id}'
            })
        else:
            return JsonResponse({'status': 'warning', 'message': 'No fields provided to update'}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)