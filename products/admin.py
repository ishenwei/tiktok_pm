from django.contrib import admin

# Register your models here.
from django.urls import path
from django.contrib import admin
# --- 导入富文本字段 ---
from tinymce.widgets import TinyMCE
# --- 导入 forms 模块 ---
from django import forms
# --- 新增导入：用于渲染HTML ---
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from .models import (
    Product,
    ProductImage,
    ProductVideo,
    ProductVariation,
    ProductReview,
    Store
)
# --- 产品抓取 ---
from .views import product_fetch_view

# ----------------------------------------------------------------------
# 核心类: 定义富文本表单 (用于 ProductAdmin)
# ----------------------------------------------------------------------
class ProductAdminForm(forms.ModelForm):
    """
    定义 Product 模型的自定义表单，指定字段使用 TinyMCE 插件。
    """
    class Meta:
        model = Product
        fields = '__all__'
        # 将描述字段指定为 TinyMCE 富文本 widget
        widgets = {
            'description': TinyMCE(attrs={'cols': 80, 'rows': 20}),
            'description_1': TinyMCE(attrs={'cols': 80, 'rows': 15}),
            'description_2': TinyMCE(attrs={'cols': 80, 'rows': 10}),
        }

# ----------------------------------------------------------------------
# 辅助类: 用于在 Product 详情页内嵌显示关联信息
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# 1. 产品图片 (ProductImages)
# ----------------------------------------------------------------------
class ProductImageInline(admin.TabularInline):
    """在 Product 编辑页内嵌展示产品图片"""
    model = ProductImage
    # 指定显示的字段
    fields = ('image_type', 'original_url', 'zipline_url', 'image_preview', 'created_at')
    readonly_fields = ('image_preview', 'created_at',)
    extra = 1  # 额外显示一行空白表单供新增

    def image_preview(self, obj):
        """生成图片预览，并添加 JavaScript 点击事件支持"""
        if obj.original_url:
            # 不再使用 <a> 标签，而是使用带 data 属性的 <img> 标签
            return mark_safe(f'''
                <img 
                    src="{obj.original_url}" 
                    data-large-url="{obj.original_url}" 
                    class="image-clickable" 
                    style="max-width: 100px; max-height: 100px; cursor: pointer;" 
                    title="点击查看大图"
                />
            ''')
        return "No Image"

    image_preview.short_description = 'Preview'

# ----------------------------------------------------------------------
# 2. 产品视频 (ProductVideos)
# ----------------------------------------------------------------------
class ProductVideoInline(admin.TabularInline):
    """在 Product 编辑页内嵌展示产品视频"""
    model = ProductVideo
    fields = ('video_type', 'original_url', 'zipline_url', 'created_at')
    readonly_fields = ('created_at',)
    extra = 1

# ----------------------------------------------------------------------
# 3. 产品变体 (ProductVariations)
# ----------------------------------------------------------------------
class ProductVariationInline(admin.TabularInline):
    """在 Product 编辑页内嵌展示产品变体/SKU"""
    model = ProductVariation
    # fields 列表添加 'image_preview'
    fields = (
        'sku', 'stock', 'purchase_limit', 'final_price', 'currency',
        'image_original_url', 'image_preview', 'updated_at' # <-- 添加 image_preview
    )
    # readonly_fields 列表添加 'image_preview'
    readonly_fields = ('image_preview', 'updated_at',)
    extra = 1

    def image_preview(self, obj):
        """根据 image_zipline_url 生成图片预览，并添加 JavaScript 点击事件支持"""
        if obj.image_original_url:
            # 不再使用 <a> 标签
            return mark_safe(f'''
                <img 
                    src="{obj.image_original_url}" 
                    data-large-url="{obj.image_original_url}" 
                    class="image-clickable"
                    style="max-width: 100px; max-height: 100px; cursor: pointer;" 
                    title="点击查看大图"
                />
            ''')
        return "No Image"
    image_preview.short_description = 'Preview'
    # 可以通过设置 max_num 来限制变体的数量，这里不设置，保持可拓展性


# ----------------------------------------------------------------------
# 4. 产品评价 (ProductReviews)
# ----------------------------------------------------------------------

class ProductReviewInline(admin.TabularInline):
    """在 Product 编辑页内嵌展示产品评价"""
    model = ProductReview
    # 注意：images 和 zipline_images 是 JSONField，如果内容过大，可以不显示或使用定制 widget

    # === 关键修改 ===
    classes = ('collapse',)  # <-- 添加这一行，使其默认折叠
    # ================

    fields = (
        'reviewer_name', 'rating', 'review_date', 'review_text',
        'images', 'zipline_images', 'created_at'
    )
    readonly_fields = ('created_at',)
    extra = 0  # 评价通常是导入的，默认不提供额外空白行

    # 如果 review_text 过长，可以使用以下方式控制其显示：
    # formfield_overrides = {
    #     models.TextField: {'widget': forms.Textarea(attrs={'rows': 2, 'cols': 50})}
    # }



# ----------------------------------------------------------------------
# 核心类: 定制 Product 模型的管理界面 (CRUD)
# ----------------------------------------------------------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # --- 新增: 引用自定义表单 ---
    form = ProductAdminForm

    class Media:
        """
        引入自定义的静态文件。
        注意：Django Admin 默认会加载 jQuery。
        """
        css = {
            'all': ('admin/css/admin_image_modal.css',)
        }
        js = (
            'admin/js/admin_image_modal.js',
        )

    # ------------------------------------------------------------
    # 列表页自定义方法：产品缩略图（支持点击放大）
    # ------------------------------------------------------------
    def product_thumbnail(self, obj):
        """显示产品的第一张图片缩略图，并应用点击放大 JS 样式"""
        img_url = obj.first_image_original_url  # 调用 models.py 中定义的属性

        if img_url:
            # 使用我们在 Admin 中定义的图片点击放大样式 (class="image-clickable")
            return mark_safe(f'''
                <img 
                    src="{img_url}" 
                    data-large-url="{img_url}" 
                    class="image-clickable" 
                    style="max-width: 60px; max-height: 60px; cursor: pointer;" 
                    title="点击查看大图"
                />
            ''')
        return "N/A"

    # 新增显示 Store 名称的方法
    def store_name(self, obj):
        return obj.store.name if obj.store else "-"

    store_name.short_description = "Store"

    product_thumbnail.short_description = '图片'  # 列表页列名
    product_thumbnail.allow_tags = True

    # =========================================================
    # 列表页定制 (list view)
    # =========================================================

    # 1. 列表显示的字段 (要求 3.2: 查询)
    list_display = (
        'product_thumbnail',  # <-- 将缩略图放在第一列
        'source_id',
        'title_short',
        'store',
        'final_price',
        'sold',
        'available',
        'In_stock',
        'created_at'
    )

    # 2. 链接到编辑页的字段
    list_display_links = ('source_id', 'title_short')

    # 3. 快速关键词搜索 (要求 3.8: 快速搜索)
    # 配置搜索栏将根据哪些字段进行模糊查询 (LIKE)
    search_fields = (
        'source_id',
        'title',
        'category',
        'seller_id'
    )

    # 4. 多条件过滤搜索 (要求 3.9: 多条件过滤)
    # 配置侧边栏过滤器，允许用户根据这些字段筛选数据
    list_filter = (
        'store',
        #'In_stock',
        'category',
        #'currency',
        #'created_at',
        #'final_price'  # 价格范围过滤可能需要安装第三方库，这里先用默认过滤器
    )

    # 5. 列表页可编辑字段
    #list_editable = ('available', 'In_stock',)

    # 6. 每页显示数量
    list_per_page = 15

    # 7. 优化显示 title 字段
    def title_short(self, obj):
        """截取 title 字段，使其在列表页显示更简洁"""
        return obj.title[:50] + '...' if obj.title and len(obj.title) > 50 else obj.title

    title_short.short_description = 'Title'  # 定义列的标题

    # =========================================================
    # 详情页定制 (Change/Add view)
    # =========================================================

    # 1. 字段分组显示
    fieldsets = (
        ('Product Base Info', {
            'fields':(
                ('source_id', 'title', 'url', 'category', 'category_url', 'position'),
                ('colors', 'sizes', 'shipping_fee', 'specifications'),
            )
        }),
        ('Sell Status', {
            'fields': (
                ('available', 'In_stock'),
                ('sold',)
            ),
        }),
        ('Price Settings', {
            # 'classes': ('collapse',), # 默认折叠该部分
            'fields': (
                ('currency', 'initial_price', 'final_price', 'discount_percent'),
                ('initial_price_low', 'initial_price_high'),
                ('final_price_low', 'final_price_high'),
            ),
        }),
        ('Seller Info', {
            'fields': ('seller_id', 'shop_performance_metrics', 'store'),
        }),
        ('Descriptions', {
            'fields': ('description', 'description_1', 'description_2', 'desc_detail', 'desc_detail_1', 'desc_detail_2'),
            # 备注: 此处需要集成富文本编辑器 (如 TinyMCE) 来保留格式
        }),
        ('HTML Descriptions', {
            # 将方法字段和路径字段放在这里
            'fields': ('desc_html_link', 'desc_html_path',),
        }),
        ('JSON Raw Data', {
            'classes': ('collapse',),  # 默认折叠，减少页面冗余
            'fields': ('input', 'raw_json'),
        }),
    )

    def desc_html_link(self, obj):
        """
        在 Admin 详情页显示 HTML 文件链接。
        """
        if obj.desc_html_path:
            # 构造完整的 URL。由于文件保存在 BASE_DIR/data/html/，
            # 我们需要让 Django Web 服务器能够访问它。

            # 假设您已将 BASE_DIR/data/ 映射为 STATIC 或 MEDIA 路由，
            # 但最简单的方法是直接在开发环境下使用文件路径：

            # ⚠️ 注意: 在生产环境中，您需要配置 Web 服务器来托管 'data' 目录。
            # 在开发服务器中，直接使用相对路径，但在 Admin 中无法直接链接到 BASE_DIR。

            # 简化的解决方案 (Admin 链接到 Django URL):

            # 为了让 Django 正确服务这些文件，通常将它们放在 MEDIA_ROOT 下，
            # 但如果您坚持放在 data/html，最简单的做法是将其作为静态文件的一部分。

            # 假设：我们将其视为项目根目录下的可访问文件
            return format_html('<a href="/{}" target="_blank">View HTML</a>', obj.desc_html_path)

        return "N/A (HTML 文件未生成)"

    desc_html_link.short_description = "Desc html"

    # 2. 内联关联模型 (显示关联的图片、视频、变体)
    inlines = [
        ProductVariationInline,
        ProductImageInline,
        ProductVideoInline,
        ProductReviewInline,  # <-- 新增这一行
    ]

    # 3. 不允许修改的字段
    readonly_fields = ('source_id', 'desc_html_link', 'desc_html_path', 'created_at', 'updated_at')



    # =========================================================
    # 产品抓取定制页
    # =========================================================
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # 新增 /admin/product_fetch/ 路径
            path('product_fetch/', self.admin_site.admin_view(product_fetch_view), name='product_fetch'),
        ]
        return custom_urls + urls


# ----------------------------------------------------------------------
# 注册其他独立关联模型 (如果需要独立管理和搜索)
# ----------------------------------------------------------------------

# 尽管 ProductVariation 已内嵌，但最好也注册独立管理
@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'stock', 'final_price', 'updated_at')
    #list_filter = ('stock', 'final_price')
    list_filter = ()
    search_fields = ('sku', 'product__source_id')  # 支持跨模型搜索
    raw_id_fields = ('product',)  # 使用ID输入框选择产品，提升性能

# 尽管 ProductImages 已内嵌，但最好也注册独立管理
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('image_type', 'original_url', 'zipline_url')
    #list_filter = ('stock', 'final_price')
    list_filter = ()
    search_fields = ('image_type', 'original_url', 'zipline_url')  # 支持跨模型搜索
    raw_id_fields = ('product',)  # 使用ID输入框选择产品，提升性能


# ------------------------------------------------------------
# Store Admin
# ------------------------------------------------------------

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = [
        "store_id",
        "name",
        "num_of_items",
        "rating",
        "num_sold",
        "followers",
        "badge",
    ]

    search_fields = ["store_id", "name"]
    list_filter = ["rating"]  # 可根据需要调整

    ordering = ["store_id"]   # Store 没有 created_at/updated_at，因此用 store_id 排序