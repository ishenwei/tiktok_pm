# products/admin.py

from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django import forms
from django.db import models
from .utils import format_json_to_html

# 导入模型
from .models import (
    Product,
    ProductImage,
    ProductVideo,
    ProductVariation,
    ProductReview,
    Store,
    ProductTagDefinition  # <--- 别忘了导入这个新模型
)

# 导入视图和服务
from .views import product_fetch_view
from .services.product_media_downloader import download_all_product_images

# 🌟 从新文件导入表单 🌟
from .forms import ProductAdminForm


# ----------------------------------------------------------------------
# Tags 管理配置 (Tag Definition)
# ----------------------------------------------------------------------
@admin.register(ProductTagDefinition)
class ProductTagDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'color_preview')
    search_fields = ('name', 'code')

    def color_preview(self, obj):
        """在列表页显示颜色圆点预览"""
        return format_html(
            '<div style="width:20px; height:20px; background:{}; border-radius:50%; border:1px solid #ccc;"></div>',
            obj.color
        )

    color_preview.short_description = "Color"


# ----------------------------------------------------------------------
# Tags 过滤器 (用于 Product 列表页侧边栏)
# ----------------------------------------------------------------------
class TagListFilter(admin.SimpleListFilter):
    title = 'Tags'
    parameter_name = 'tags'

    def lookups(self, request, model_admin):
        # 侧边栏显示所有可用标签
        return [(tag.code, tag.name) for tag in ProductTagDefinition.objects.all()]

    def queryset(self, request, queryset):
        # 执行过滤：查找 JSON 数组包含该标签的产品
        if self.value():
            return queryset.filter(tags__contains=self.value())
        return queryset


# ----------------------------------------------------------------------
# Inline Classes (保持你原有的逻辑不变)
# ----------------------------------------------------------------------

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    fields = ('image_preview', 'image_type', 'original_url', 'zipline_url')
    readonly_fields = ('image_type', 'image_preview',)
    extra = 0

    # 3. 🌟 关键修改：重写控件样式 (Widget Overrides)
    # 这段代码会强制把 TextField (多行) 变成 TextInput (单行)，并限制宽度和高度
    formfield_overrides = {
        models.TextField: {
            'widget': forms.TextInput(attrs={
                'style': 'width: 250px; height: 26px; font-size: 13px; padding: 2px 5px;'
            })
        },
        models.URLField: {
            'widget': forms.TextInput(attrs={
                'style': 'width: 250px; height: 26px; font-size: 13px; padding: 2px 5px;'
            })
        },
        models.CharField: {
            'widget': forms.TextInput(attrs={
                'style': 'width: 150px; height: 26px; font-size: 13px;'
            })
        },
    }

    def image_preview(self, obj):
        if obj.original_url:
            return mark_safe(f'''
                <img src="{obj.original_url}" data-large-url="{obj.original_url}" 
                     class="image-clickable" style="max-width: 100px; max-height: 100px; cursor: pointer;" />
            ''')
        return "No Image"

    image_preview.short_description = 'Preview'


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    fields = ('video_type', 'original_url', 'zipline_url', 'created_at')
    readonly_fields = ('created_at',)
    extra = 1


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    fields = ('image_preview', 'sku', 'props_display', 'stock', 'final_price', 'currency', 'image_original_url',)
    readonly_fields = ('sku', 'props_display', 'image_preview','currency',)
    extra = 0

    # 3. 🌟 关键修改：重写控件样式 (Widget Overrides)
    # 这段代码会强制把 TextField (多行) 变成 TextInput (单行)，并限制宽度和高度
    formfield_overrides = {
        models.TextField: {
            'widget': forms.TextInput(attrs={
                'style': 'width: 250px; height: 26px; font-size: 13px; padding: 2px 5px;'
            })
        },
        models.URLField: {
            'widget': forms.TextInput(attrs={
                'style': 'width: 250px; height: 26px; font-size: 13px; padding: 2px 5px;'
            })
        },
        models.CharField: {
            'widget': forms.TextInput(attrs={
                'style': 'width: 150px; height: 26px; font-size: 13px;'
            })
        },
        models.IntegerField: {
            'widget': forms.TextInput(attrs={
                'style': 'width: 50px; height: 26px; font-size: 13px; padding: 2px 5px;'
            })
        },
    }

    def image_preview(self, obj):
        if obj.image_original_url:
            return mark_safe(f'''
                <img src="{obj.image_original_url}" data-large-url="{obj.image_original_url}" 
                     class="image-clickable" style="max-width: 100px; max-height: 100px; cursor: pointer;" />
            ''')
        return "No Image"

    image_preview.short_description = 'Preview'

    def props_display(self, obj):
        # 🌟 直接调用工具函数，代码极其简洁
        return format_json_to_html(obj.sku_sales_props)

    props_display.short_description = "Variations"

class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    classes = ('collapse',)
    fields = ('reviewer_name', 'rating', 'review_date', 'review_text', 'images', 'zipline_images', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0


# ----------------------------------------------------------------------
# Main Product Admin
# ----------------------------------------------------------------------

class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm  # 使用 forms.py 中定义的带 Tags 的表单
    change_form_template = "admin/products/product/change_form.html"

    # 🌟 关键：引入 Select2 资源和自定义 CSS/JS 🌟
    # 🌟 修改 Media 类：添加 jquery CDN，并调整顺序 🌟
    class Media:
        css = {
            'all': (
                'admin/css/admin_image_modal.css',
                '//cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
                'admin/css/product_tags.css',
            )
        }
        js = (
            # 1. 必须最先加载标准 jQuery (Select2 依赖它)
            '//code.jquery.com/jquery-3.6.0.min.js',

            # 2. 然后是 Select2
            '//cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',

            # 3. 你的自定义脚本
            'admin/js/admin_image_modal.js',
            'admin/js/product_tags.js',
        )

    # --- 列表页显示 Tags ---
    def tags_display(self, obj):
        """列表页：将 JSON tags 渲染为彩色胶囊"""
        if not obj.tags or not isinstance(obj.tags, list):
            return "-"

        # 简单缓存优化：获取所有 tag 定义
        # 生产环境中如果 tag 很多，建议使用 cache 或 request 级缓存
        tag_defs = {t.code: t for t in ProductTagDefinition.objects.all()}

        html = []
        for tag_code in obj.tags:
            tag_def = tag_defs.get(tag_code)

            # --- 核心修改点 ---
            # 1. white-space: nowrap; -> 禁止文字换行
            # 2. display: inline-block; -> 保证胶囊形状完整，不会被截断
            # 3. margin-bottom: 4px; -> 如果标签太多自动换行到了下一行，增加一点垂直间距

            common_style = "white-space: nowrap; display: inline-block; padding: 3px 8px; border-radius: 10px; font-size: 11px; margin-right: 4px; margin-bottom: 4px;"

            if tag_def:
                # 使用定义的颜色
                style = f"background-color: {tag_def.color}; color: #fff; padding: 3px 8px; border-radius: 10px; font-size: 11px; margin-right: 4px; font-weight:bold; {common_style}"
                html.append(f'<span style="{style}">{tag_def.name}</span>')
            else:
                # 未定义颜色的 Tag (灰色兜底)
                style = f"background-color: #999; color: #fff; padding: 3px 8px; border-radius: 10px; font-size: 11px; margin-right: 4px; {common_style}"
                html.append(f'<span style="{style}">{tag_code}</span>')

        return mark_safe("".join(html))

    tags_display.short_description = "Tags"

    # --- 自定义字段显示 ---
    def product_thumbnail(self, obj):
        img_url = obj.first_image_original_url
        if img_url:
            return mark_safe(f'''
                <img src="{img_url}" data-large-url="{img_url}" 
                     class="image-clickable" style="max-width: 60px; max-height: 60px; cursor: pointer;" />
            ''')
        return "N/A"

    product_thumbnail.short_description = '图片'
    product_thumbnail.allow_tags = True

    def store_name(self, obj):
        return obj.store.name if obj.store else "-"

    store_name.short_description = "Store"

    def desc_html_link(self, obj):
        if obj.desc_html_path:
            return format_html('<a href="/{}" target="_blank">View HTML</a>', obj.desc_html_path)
        return "N/A"

    desc_html_link.short_description = "Desc html"

    def title_short(self, obj):
        return obj.title[:50] + '...' if obj.title and len(obj.title) > 50 else obj.title

    title_short.short_description = 'Title'

    # ============================================================
    # 🌟 新增：产品图画廊 (Gallery) 显示方法
    # ============================================================
    def product_images_gallery(self, obj):
        if not obj or not obj.pk:
            return "请先保存产品以查看图片。"

        # 获取关联的所有图片 (根据你的模型，related_name='product_images')
        # 如果只想显示 'main' 类型的图片，可以加上 .filter(image_type='main')
        images = obj.product_images.all().order_by('id')

        if not images.exists():
            return "暂无图片"

        # 构建 HTML：使用 Flex 布局让图片横向排列
        html_content = ['<div style="display: flex; flex-wrap: wrap; gap: 10px;">']

        for img in images:
            if img.original_url:
                # 使用 image-clickable 类来复用点击放大功能
                img_tag = f'''
                        <div style="border: 1px solid #ddd; padding: 2px; border-radius: 4px;">
                            <img src="{img.original_url}" 
                                 data-large-url="{img.original_url}" 
                                 class="image-clickable" 
                                 title="{img.image_type or ''}"
                                 style="height: 100px; width: auto; object-fit: cover; cursor: pointer; display: block;" 
                            />
                        </div>
                    '''
                html_content.append(img_tag)

        html_content.append('</div>')
        return mark_safe("".join(html_content))

    product_images_gallery.short_description = "Gallery Preview"
    product_images_gallery.allow_tags = True

    # ============================================================
    # 🌟 新增：视频画廊 (Video Gallery)
    # ============================================================
    def product_videos_gallery(self, obj):
        if not obj or not obj.pk:
            return "-"

        # 获取关联视频
        videos = obj.product_videos.all().order_by('id')

        if not videos.exists():
            return "暂无视频"

        html_content = ['<div style="display: flex; flex-wrap: wrap; gap: 15px;">']

        for vid in videos:
            # 优先使用 Zipline 加速地址，如果没有则用原始地址
            video_url = vid.zipline_url or vid.original_url

            if video_url:
                # 构建 HTML：
                # 1. 使用 <video> 标签作为缩略图 (muted, preload=metadata)
                # 2. 添加 class="video-clickable" 供 JS 识别
                # 3. 添加 data-video-url 存储真实播放地址
                # 4. 叠加一个 CSS 绘制的播放按钮 (▶) 提升可点击感
                html_content.append(f'''
                        <div style="position: relative; cursor: pointer; border: 1px solid #ddd; border-radius: 4px; overflow: hidden;"
                             class="video-clickable-wrapper"
                             data-video-url="{video_url}">

                            <video src="{video_url}" 
                                   style="height: 120px; width: auto; display: block; background: #000;" 
                                   preload="metadata" muted>
                            </video>

                            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                                        background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;">
                                <span style="color: white; font-size: 30px; opacity: 0.9;">▶</span>
                            </div>
                        </div>
                    ''')

        html_content.append('</div>')
        return mark_safe("".join(html_content))

    product_videos_gallery.short_description = "Video Gallery"
    product_videos_gallery.allow_tags = True

    # ============================================================
    # 🌟 新增：批量定义 JSON 格式化显示方法
    # ============================================================

    def colors_display(self, obj):
        return format_json_to_html(obj.colors)

    colors_display.short_description = "Colors"

    def sizes_display(self, obj):
        return format_json_to_html(obj.sizes)

    sizes_display.short_description = "Sizes"

    def specifications_display(self, obj):
        return format_json_to_html(obj.specifications)

    specifications_display.short_description = "Specifications"

    def metrics_display(self, obj):
        return format_json_to_html(obj.shop_performance_metrics)

    metrics_display.short_description = "Shop Performance Metrics"

    # === 配置列表页 ===
    list_display = (
        'product_thumbnail',
        'source_id',
        'title_short',
        'tags_display',  # <--- 新增 Tag 列
        'store',
        'final_price',
        'sold',
        'available',
        'In_stock',
        'created_at'
    )

    list_display_links = ('source_id', 'title_short')
    search_fields = ('source_id', 'title', 'category', 'seller_id')

    # === 配置过滤器 ===
    list_filter = (
        TagListFilter,  # <--- 新增 Tag 过滤器
        'category',
    )

    list_per_page = 15

    # ============================================================
    # 🌟 配置：更新 Fieldsets 布局
    # ============================================================
    fieldsets = (
        ('Product Base Info', {
            'fields': (
                ('source_id', 'title', 'tags_selector'),
                ('url', 'category', 'category_url', 'position'),

                # --- 修改开始：使用 display 字段替换原始字段 ---
                # 将 Colors 和 Sizes 并排显示
                ('colors_display', 'sizes_display'),
                # Specifications 通常较长，独占一行
                'specifications_display',
                # 运费保持原始或也格式化 (这里暂时保留原始)
                'shipping_fee',
            )
        }),

        ('Product Images', {
            'fields': ('product_images_gallery',),
        }),

        # --- 新增 Video Section ---
        ('Product Videos', {
            'fields': ('product_videos_gallery',),
        }),
        # -------------------------

        ('Sell Status', {
            'fields': (('available', 'In_stock'), ('sold',)),
        }),

        ('Price Settings', {
            'fields': (
                ('currency', 'initial_price', 'final_price', 'discount_percent'),
                ('initial_price_low', 'initial_price_high'),
                ('final_price_low', 'final_price_high'),
            ),
        }),

        ('Seller Info', {
            # --- 修改：替换 shop_performance_metrics ---
            'fields': ('seller_id', 'metrics_display', 'store'),
        }),

        ('Descriptions', {
            'fields': ('description', 'description_1', 'description_2', 'desc_detail', 'desc_detail_1',
                       'desc_detail_2'),
        }),
        ('HTML Descriptions', {
            'fields': ('desc_html_link', 'desc_html_path',),
        }),

        # 原始数据区域 (建议保留原始字段以便调试)
        ('JSON Raw Data', {
            'classes': ('collapse',),
            'fields': ('input', 'raw_json', 'tags', 'colors', 'sizes', 'specifications', 'shop_performance_metrics'),
        }),
    )

    inlines = [ProductVariationInline, ProductImageInline, ProductVideoInline, ProductReviewInline]
    # ============================================================
    # 🌟 配置：添加到只读字段列表 (必须！)
    # ============================================================
    readonly_fields = (
        'source_id',
        'desc_html_link',
        'desc_html_path',
        'created_at',
        'updated_at',
        'product_images_gallery',
        'product_videos_gallery',
        # 新增的格式化字段
        'colors_display',
        'sizes_display',
        'specifications_display',
        'metrics_display',
    )

    # === 自定义 Actions 和 URLs (保持你原有的逻辑) ===
    def get_urls(self):
        urls = super().get_urls()
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        base_name = f'{app_label}_{model_name}'

        custom_urls = [
            path(
                "<int:product_id>/download-images/",
                self.admin_site.admin_view(self.download_images),
                name=f"{base_name}_download-images",
            ),
            path(
                "product_fetch/",
                self.admin_site.admin_view(product_fetch_view),
                name=f"{base_name}_fetch",
            ),
        ]
        return custom_urls + urls

    def download_images(self, request, product_id):
        product = Product.objects.get(pk=product_id)
        target_dir, summary = download_all_product_images(product)
        messages.success(
            request,
            f"下载完成：商品图片 {summary['product_images']} 张，SKU 图片 {summary['variation_images']} 张，详情图片 {summary['desc_images']} 张。"
        )
        return redirect(request.META.get("HTTP_REFERER"))


# ------------------------------------------------------------
# 其他 Admin 注册 (保持不变)
# ------------------------------------------------------------

@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'stock', 'final_price', 'updated_at')
    search_fields = ('sku', 'product__source_id')
    raw_id_fields = ('product',)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('image_type', 'original_url', 'zipline_url')
    search_fields = ('image_type', 'original_url', 'zipline_url')
    raw_id_fields = ('product',)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    # 1. 引入与 ProductAdmin 相同的静态文件，支持弹窗放大功能
    class Media:
        css = {
            'all': ('admin/css/admin_image_modal.css',)
        }
        js = ('admin/js/admin_image_modal.js',)

    # 2. 定义 Badge 预览方法
    def badge_preview(self, obj):
        # 假设 badge 字段存储的是 URL 字符串
        if obj.badge:
            return mark_safe(f'''
                    <img src="{obj.badge}" 
                         data-large-url="{obj.badge}" 
                         class="image-clickable" 
                         style="max-width: 50px; max-height: 50px; cursor: pointer; border-radius: 50%; border: 1px solid #ddd;" />
                ''')
        return "-"

    badge_preview.short_description = "Badge"

    # 3. 将 badge_preview 添加到列表显示的最前面
    list_display = ["badge_preview", "store_id", "name", "num_of_items", "rating", "num_sold", "followers"]
    # 🌟 核心修改：指定哪些字段作为详情页的链接 🌟
    # 这里我们指定 store_id 和 name 都可以点击
    list_display_links = ("store_id", "name")

    search_fields = ["store_id", "name"]
    list_filter = ["rating"]
    ordering = ["store_id"]

    # =========================================================
    # 🌟 核心修改：配置详情页显示 🌟
    # =========================================================

    # 1. 声明 badge_preview 为只读字段
    readonly_fields = ("badge_preview",)

    # 2. 定义详情页的字段顺序 (将 badge_preview 放在最前面或合适的位置)
    fields = (
        "badge_preview",  # 显示图片
        "store_id",
        "name",
        "badge",  # 显示原始 URL 文本 (可选)
        "url",
        "rating",
        "num_of_items",
        "num_sold",
        "followers"
    )


admin.site.register(Product, ProductAdmin)