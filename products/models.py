from django.db import models

# Create your models here.
from django.db import models
from django.db.models.functions import Now

class Product(models.Model):
    """
    对应 tables.sql 中的 products 表。
    存储 TikTok 平台产品的核心信息。
    """

    # 基础信息
    # id BIGINT AUTO_INCREMENT PRIMARY KEY 已经由 Django 自动创建
    source_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,  # 确保查询效率
        verbose_name="TikTok Source ID"
    )
    url = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)

    # 描述字段 (使用 TextField 对应 MySQL 的 LONGTEXT/TEXT)
    description = models.TextField(blank=True, null=True)
    description_1 = models.TextField(blank=True, null=True)
    description_2 = models.TextField(blank=True, null=True)
    desc_detail = models.TextField(blank=True, null=True)
    desc_detail_1 = models.TextField(blank=True, null=True)
    desc_detail_2 = models.TextField(blank=True, null=True)

    # 状态字段
    available = models.BooleanField(blank=True, null=True)
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
    store_name = models.CharField(max_length=255, blank=True, null=True)

    # 评价和性能
    prodct_rating = models.JSONField(blank=True, null=True)
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
# ------------------------------------------------------------
# 提示：其他关联表 (product_images, product_variations 等)
# 需要您参照此格式，继续在 models.py 文件中创建，并设置 ForeignKey 关联。
# ------------------------------------------------------------


# ------------------------------------------------------------
# 1. Table: product_images
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
# 2. Table: product_videos
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
# 3. Table: product_variations
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
# 新增模型: ProductReview
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