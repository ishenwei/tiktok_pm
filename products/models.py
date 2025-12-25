# Create your models here.
from django.db.models.functions import Now
from .utils import json_to_html, save_html_file
from django.db import models
import uuid

# ----------------------------------------------------------------------
# Table: Store
# ----------------------------------------------------------------------

class Store(models.Model):
    store_id = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    url = models.CharField(max_length=500, null=True, blank=True)

    num_of_items = models.IntegerField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    num_sold = models.IntegerField(null=True, blank=True)
    followers = models.IntegerField(null=True, blank=True)
    badge = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = "stores"

    def __str__(self):
        return f"{self.name} ({self.store_id})"

# ----------------------------------------------------------------------
# Table: Products
# ----------------------------------------------------------------------

class Product(models.Model):
    """
    对应 tables.sql 中的 products 表。
    存储 TikTok 平台产品的核心信息。
    """
    store = models.ForeignKey(
        Store,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products"
    )

    # 基础信息
    # id BIGINT AUTO_INCREMENT PRIMARY KEY 已经由 Django 自动创建
    source_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,  # 确保查询效率
        verbose_name="TikTok Source ID"
    )

    url = models.TextField(blank=True, null=True)
    title = models.TextField(null=True, blank=True)
    available = models.BooleanField(default=True)

    description = models.TextField(null=True, blank=True)
    description_1 = models.TextField(blank=True, null=True)
    description_2 = models.TextField(blank=True, null=True)

    #desc_detail = models.TextField(blank=True, null=True)
    #desc_detail_1 = models.TextField(blank=True, null=True)
    #desc_detail_2 = models.TextField(blank=True, null=True)
    desc_detail = models.JSONField(blank=True, null=True, default=list)
    desc_detail_1 = models.JSONField(blank=True, null=True, default=list)
    desc_detail_2 = models.JSONField(blank=True, null=True, default=list)

    # 🌟 新增字段：用于存储生成的 HTML 文件的相对路径 🌟
    desc_html_path = models.CharField(max_length=255, blank=True, null=True)

    # 状态字段
    In_stock = models.BooleanField(blank=True, null=True)  # 字段名与SQL文件保持一致

    # 价格字段
    currency = models.CharField(max_length=16, blank=True, null=True)
    initial_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        db_index=True  # 对应 idx_price
    )
    discount_percent = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # 价格范围字段
    initial_price_low = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    initial_price_high = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    final_price_low = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    final_price_high = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # 销售和位置
    sold = models.IntegerField(blank=True, null=True, db_index=True)  # 对应 idx_sold
    position = models.IntegerField(blank=True, null=True)

    # JSON 字段 (存储复杂的结构化数据)
    colors = models.JSONField(blank=True, null=True)
    sizes = models.JSONField(blank=True, null=True)
    shipping_fee = models.JSONField(blank=True, null=True)
    specifications = models.JSONField(blank=True, null=True)
    videos = models.JSONField(blank=True, null=True)
    related_videos = models.JSONField(blank=True, null=True)

    # 视频链接
    video_link = models.TextField(blank=True, null=True)

    # 分类和卖家信息
    category = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # 对应 idx_category
    category_url = models.TextField(blank=True, null=True)
    seller_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)  # 对应 idx_seller

    # 评价和性能
    product_rating = models.JSONField(blank=True, null=True)
    promotion_items = models.JSONField(blank=True, null=True)
    shop_performance_metrics = models.JSONField(blank=True, null=True)

    # 导入时间戳和原始数据
    timestamp = models.DateTimeField(blank=True, null=True)
    input = models.JSONField(blank=True, null=True)
    raw_json = models.JSONField(blank=True, null=True)

    # Django 自动管理的时间戳
    #created_at = models.DateTimeField(auto_now_add=True, null=True)
    #updated_at = models.DateTimeField(auto_now=True, null=True)

    # 利用数据库管理的时间戳
    created_at = models.DateTimeField(blank=True, null=True, db_default=Now(),)
    updated_at = models.DateTimeField(blank=True, null=True, db_default=Now(),)

    #新增tags, 使用 JSONField 存储标签列表，例如 ["candidate", "hot"]
    tags = models.JSONField(default=list, blank=True, null=True)

    class Meta:
        # 定义模型的复数名称，让Admin后台显示更友好
        verbose_name = "TikTok Product"
        verbose_name_plural = "TikTok Products"
        # 显式指定使用的表名（如果和模型名不一致，可以配置）
        db_table = 'products'

    def __str__(self):
        """返回对象在Admin后台的显示名称"""
        return f"{self.source_id}: {self.title[:50]}..."

    # ------------------------------------------------------------
    # 新增属性：获取第一张图片的 Original URL (用于列表页展示)
    # ------------------------------------------------------------
    @property
    def first_image_original_url(self):
        """返回关联的第一张图片的加速 URL，如果存在的话。"""
        # 由于我们在 ProductImage 模型中使用了 related_name='product_images' (假设如此)
        # 我们按 id 或某个顺序字段获取第一张图片
        first_image = self.product_images.filter(image_type='main').order_by('id').first()
        if first_image and first_image.original_url:
            return first_image.original_url

        # 如果没有找到 'main' 类型的图片，尝试找任意一张
        first_image = self.product_images.order_by('id').first()
        if first_image and first_image.original_url:
            return first_image.original_url

        return None

    # ------------------------------------------------------------
    # 新增属性：获取第一张图片的 Zipline URL (用于列表页展示)
    # ------------------------------------------------------------
    @property
    def first_image_zipline_url(self):
        """返回关联的第一张图片的加速 URL，如果存在的话。"""
        # 由于我们在 ProductImage 模型中使用了 related_name='product_images' (假设如此)
        # 我们按 id 或某个顺序字段获取第一张图片
        first_image = self.product_images.filter(image_type='main').order_by('id').first()
        if first_image and first_image.zipline_url:
            return first_image.zipline_url

        # 如果没有找到 'main' 类型的图片，尝试找任意一张
        first_image = self.product_images.order_by('id').first()
        if first_image and first_image.zipline_url:
            return first_image.zipline_url

        return None

    def save(self, *args, **kwargs):
        """
                覆盖 save 方法，确保在每次保存时都重新生成 HTML 文件。
                """
        # 1. 在调用 super().save() 之前执行自定义逻辑
        self._generate_html()

        # 2. 调用父类的 save 方法，将对象存入数据库 (包括更新后的 desc_html_path)
        super().save(*args, **kwargs)

    def _generate_html(self):
        """内部方法：生成并保存 HTML 文件"""
        if self.desc_detail and self.source_id:
            html_content = json_to_html(self.desc_detail)

            # 使用 source_id 作为文件名
            relative_path = save_html_file(self.source_id, html_content)

            if relative_path:
                self.desc_html_path = relative_path


# ------------------------------------------------------------
# Table: product_images
# ------------------------------------------------------------
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,  # 对应 ON DELETE CASCADE
        related_name='product_images',  # 方便从 Product 对象反向查询所有图片：product.images.all()
        verbose_name="关联产品"
    )
    image_type = models.TextField(blank=True, null=True)
    original_url = models.TextField(blank=True, null=True)
    zipline_url = models.TextField(blank=True, null=True)

    #created_at = models.DateTimeField(auto_now_add=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, db_default=Now(),)

    class Meta:
        db_table = 'product_images'
        verbose_name_plural = "TikTok Product Images"

    def __str__(self):
        return f"Image for {self.product.source_id}"


# ------------------------------------------------------------
# Table: product_videos
# ------------------------------------------------------------
class ProductVideo(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,  # 对应 ON DELETE CASCADE
        related_name='product_videos',  # 注意：避免与 Product.videos (JSONField) 字段名冲突
        verbose_name="关联产品"
    )
    video_type = models.TextField(blank=True, null=True)
    original_url = models.TextField(blank=True, null=True)
    zipline_url = models.TextField(blank=True, null=True)

    #created_at = models.DateTimeField(auto_now_add=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, db_default=Now(),)

    class Meta:
        db_table = 'product_videos'
        verbose_name_plural = "TikTok Product Videos"

    def __str__(self):
        return f"Video for {self.product.source_id}"


# ------------------------------------------------------------
# Table: product_variations
# ------------------------------------------------------------
class ProductVariation(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,  # 对应 ON DELETE CASCADE
        related_name='product_variations',  # 方便从 Product 对象反向查询所有变体：product.variations.all()
        verbose_name="关联产品"
    )

    sku = models.CharField(max_length=128, blank=True, null=True, db_index=True)  # 对应 idx_variation_sku
    sku_sales_props = models.JSONField(blank=True, null=True)

    stock = models.IntegerField(blank=True, null=True)
    purchase_limit = models.IntegerField(blank=True, null=True)

    initial_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=16, blank=True, null=True)
    discount_percent = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    image_original_url = models.TextField(blank=True, null=True)
    image_zipline_url = models.TextField(blank=True, null=True)

    #created_at = models.DateTimeField(auto_now_add=True, null=True)
    # auto_now=True 对应 ON UPDATE CURRENT_TIMESTAMP
    #updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, db_default=Now(),)
    updated_at = models.DateTimeField(blank=True, null=True, db_default=Now(),)

    class Meta:
        db_table = 'product_variations'
        verbose_name_plural = "TikTok Product Variations"

    def __str__(self):
        return f"Variation SKU: {self.sku} ({self.product.source_id})"


# ----------------------------------------------------------------------
# Table: product_reviews
# ----------------------------------------------------------------------

class ProductReview(models.Model):
    # 关联到 Product 表
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'  # 定义反向关联名称
    )

    # 评价人信息
    reviewer_name = models.CharField( max_length=255, blank=True, null=True, verbose_name='评价人昵称')
    # 评分 (TINYINT 对应 SmallIntegerField 或 IntegerField)
    rating = models.SmallIntegerField(blank=True, null=True, verbose_name='评分 (1-5)')
    # 评价内容 (TEXT 对应 TextField)
    review_text = models.TextField(blank=True, null=True, verbose_name='评价内容')
    # 评价日期
    review_date = models.DateTimeField(blank=True, null=True, verbose_name='评价发生日期')
    # 原始图片 URL (JSON 对应 JSONField)
    images = models.JSONField(blank=True, null=True,verbose_name='原始图片JSON')
    # Zipline 加速后图片 URL (JSON 对应 JSONField)
    zipline_images = models.JSONField(blank=True,null=True,verbose_name='加速图片JSON')

    # 创建时间 (对应 TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    # 采用之前针对 MySQL DDL 的解决方案：依赖数据库的 DEFAULT
    created_at = models.DateTimeField(blank=True, null=True, db_default=Now(),)

    class Meta:
        verbose_name = 'TikTok Product Review'
        verbose_name_plural = 'TikTok Product Reviews'
        db_table = 'product_reviews'  # 确保表名与您 DDL 中的名称一致
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.source_id} - {self.reviewer_name} ({self.rating}星)'

# ----------------------------------------------------------------------
# Table: product_tag_definition
# ----------------------------------------------------------------------
class ProductTagDefinition(models.Model):
    code = models.SlugField(max_length=50, unique=True, help_text="存入数据库的唯一标识，如 'candidate'")
    name = models.CharField(max_length=100, help_text="显示给用户的名称，如 '待发布'")
    color = models.CharField(max_length=20, default="#666666", help_text="十六进制颜色，如 #FF5733")
    # 创建时间 (对应 TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    # 采用之前针对 MySQL DDL 的解决方案：依赖数据库的 DEFAULT
    created_at = models.DateTimeField(blank=True, null=True, db_default=Now(),)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tag Definition'
        verbose_name_plural = 'Tag Definitions'
        db_table = 'product_tags'




# ----------------------------------------------------------------------
# Table: ai content item
# ----------------------------------------------------------------------
class AIContentItem(models.Model):
    TYPE_CHOICES = [
        ('desc', '产品描述优化'),
        ('script', '视频拍摄脚本'),
        ('voice', '视频配音文案'),
        ('img_prompt', '图片生成提示词'),
        ('vid_prompt', '视频制作提示词'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ai_items')

    # 新增：AI 模型类型字段
    # 示例值: 'gemini-2.0-flash', 'gpt-4o', 'claude-3-5-sonnet'
    ai_model = models.CharField(max_length=50, verbose_name="生成模型", db_index=True)

    content_type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    content_zh = models.TextField(verbose_name="中文内容", blank=True)
    content_en = models.TextField(verbose_name="英文内容", blank=True)

    option_index = models.IntegerField(default=1)
    status = models.CharField(max_length=20, default='draft', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', 'content_type', 'option_index']
        # 增加复合索引，提高查询特定产品下特定模型生成的脚本的速度
        indexes = [
            models.Index(fields=['product', 'ai_model', 'content_type']),
        ]
        db_table = 'ai_content_items'

    def __str__(self):
        return f"[{self.ai_model}] {self.get_content_type_display()} - {self.option_index}"