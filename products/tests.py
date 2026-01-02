import json
import os
from decimal import Decimal
from unittest import mock

import requests
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from django_q.models import Schedule

from .models import (
    Store,
    Product,
    ProductImage,
    ProductVideo,
    ProductVariation,
    ProductReview,
    ProductTagDefinition,
    AIContentItem,
)
from .serializers import (
    ProductSerializer,
    ProductImageSerializer,
    ProductVideoSerializer,
    ProductVariationSerializer,
)
from .tasks import (
    trigger_bright_data_task,
    poll_bright_data_result,
    save_snapshot_file,
)


# ----------------------------------------------------------------------
# 模拟响应类
# ----------------------------------------------------------------------
class MockResponse:
    def __init__(self, status_code, json_data=None, text_data=None):
        self.status_code = status_code
        self._json_data = json_data
        self._text_data = text_data
        self.text = text_data if text_data is not None else json.dumps(json_data)

    def json(self):
        if self._json_data is not None:
            return self._json_data
        raise json.JSONDecodeError("Mock JSON Decode Error", self.text, 0)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error")


# ----------------------------------------------------------------------
# 模拟数据库连接
# ----------------------------------------------------------------------
class MockCursor:
    def execute(self, sql, args=None):
        pass

    def fetchone(self):
        return (1,)

    def fetchall(self):
        return []


class MockConnection:
    def __init__(self, *args, **kwargs):
        pass

    def cursor(self):
        return MockCursor()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


# ----------------------------------------------------------------------
# 1. 模型测试
# ----------------------------------------------------------------------
class StoreModelTest(TestCase):
    """测试Store模型"""

    def setUp(self):
        self.store = Store.objects.create(
            store_id="test_store_001",
            name="测试店铺",
            url="https://example.com/shop",
            num_of_items=100,
            rating=4.5,
            num_sold=1000,
            followers=500,
            badge="官方认证",
        )

    def test_store_creation(self):
        """测试店铺创建"""
        self.assertEqual(self.store.store_id, "test_store_001")
        self.assertEqual(self.store.name, "测试店铺")
        self.assertEqual(self.store.rating, 4.5)
        self.assertEqual(self.store.num_sold, 1000)

    def test_store_str_representation(self):
        """测试店铺字符串表示"""
        expected = "测试店铺 (test_store_001)"
        self.assertEqual(str(self.store), expected)

    def test_store_unique_id(self):
        """测试店铺ID唯一性"""
        with self.assertRaises(Exception):
            Store.objects.create(store_id="test_store_001")


class ProductModelTest(TestCase):
    """测试Product模型"""

    def setUp(self):
        self.store = Store.objects.create(
            store_id="test_store_001",
            name="测试店铺",
        )
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
            url="https://example.com/product",
            available=True,
            In_stock=True,
            currency="USD",
            initial_price=Decimal("100.00"),
            final_price=Decimal("80.00"),
            discount_percent=Decimal("20.00"),
            sold=500,
            category="电子产品",
            seller_id="seller_001",
            store=self.store,
            desc_detail=[{"key": "value"}],
        )

    def test_product_creation(self):
        """测试产品创建"""
        self.assertEqual(self.product.source_id, "test_product_001")
        self.assertEqual(self.product.title, "测试产品")
        self.assertEqual(self.product.final_price, Decimal("80.00"))
        self.assertEqual(self.product.discount_percent, Decimal("20.00"))
        self.assertTrue(self.product.available)
        self.assertTrue(self.product.In_stock)

    def test_product_str_representation(self):
        """测试产品字符串表示"""
        expected = "test_product_001: 测试产品..."
        self.assertEqual(str(self.product), expected)

    def test_product_unique_source_id(self):
        """测试产品source_id唯一性"""
        with self.assertRaises(Exception):
            Product.objects.create(source_id="test_product_001", title="重复产品")

    def test_product_store_relationship(self):
        """测试产品与店铺的关系"""
        self.assertEqual(self.product.store, self.store)
        self.assertEqual(self.store.products.count(), 1)

    def test_product_json_fields(self):
        """测试JSON字段"""
        self.assertIsInstance(self.product.desc_detail, list)
        self.assertEqual(self.product.desc_detail, [{"key": "value"}])

    def test_product_price_fields(self):
        """测试价格字段"""
        self.assertEqual(self.product.initial_price, Decimal("100.00"))
        self.assertEqual(self.product.final_price, Decimal("80.00"))
        self.assertEqual(self.product.discount_percent, Decimal("20.00"))

    def test_product_tags_field(self):
        """测试tags字段"""
        self.product.tags = ["hot", "new"]
        self.product.save()
        self.assertEqual(self.product.tags, ["hot", "new"])


class ProductImageModelTest(TestCase):
    """测试ProductImage模型"""

    def setUp(self):
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
        )
        self.image = ProductImage.objects.create(
            product=self.product,
            image_type="main",
            original_url="https://example.com/image1.jpg",
            zipline_url="https://cdn.example.com/image1.jpg",
        )

    def test_image_creation(self):
        """测试图片创建"""
        self.assertEqual(self.image.product, self.product)
        self.assertEqual(self.image.image_type, "main")
        self.assertEqual(self.image.original_url, "https://example.com/image1.jpg")

    def test_image_product_relationship(self):
        """测试图片与产品的关系"""
        self.assertEqual(self.product.product_images.count(), 1)
        self.assertEqual(self.product.product_images.first(), self.image)


class ProductVideoModelTest(TestCase):
    """测试ProductVideo模型"""

    def setUp(self):
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
        )
        self.video = ProductVideo.objects.create(
            product=self.product,
            video_type="main",
            original_url="https://example.com/video1.mp4",
            zipline_url="https://cdn.example.com/video1.mp4",
        )

    def test_video_creation(self):
        """测试视频创建"""
        self.assertEqual(self.video.product, self.product)
        self.assertEqual(self.video.video_type, "main")
        self.assertEqual(self.video.original_url, "https://example.com/video1.mp4")

    def test_video_product_relationship(self):
        """测试视频与产品的关系"""
        self.assertEqual(self.product.product_videos.count(), 1)
        self.assertEqual(self.product.product_videos.first(), self.video)


class ProductVariationModelTest(TestCase):
    """测试ProductVariation模型"""

    def setUp(self):
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
        )
        self.variation = ProductVariation.objects.create(
            product=self.product,
            sku="SKU001",
            stock=100,
            purchase_limit=5,
            initial_price=Decimal("100.00"),
            final_price=Decimal("80.00"),
            currency="USD",
            discount_percent=Decimal("20.00"),
        )

    def test_variation_creation(self):
        """测试变体创建"""
        self.assertEqual(self.variation.product, self.product)
        self.assertEqual(self.variation.sku, "SKU001")
        self.assertEqual(self.variation.stock, 100)
        self.assertEqual(self.variation.final_price, Decimal("80.00"))

    def test_variation_product_relationship(self):
        """测试变体与产品的关系"""
        self.assertEqual(self.product.product_variations.count(), 1)
        self.assertEqual(self.product.product_variations.first(), self.variation)


class ProductReviewModelTest(TestCase):
    """测试ProductReview模型"""

    def setUp(self):
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
        )
        self.review = ProductReview.objects.create(
            product=self.product,
            reviewer_name="测试用户",
            rating=5,
            review_text="非常好的产品！",
            review_date=timezone.now(),
            images=["https://example.com/review1.jpg"],
            zipline_images=["https://cdn.example.com/review1.jpg"],
        )

    def test_review_creation(self):
        """测试评价创建"""
        self.assertEqual(self.review.product, self.product)
        self.assertEqual(self.review.reviewer_name, "测试用户")
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.review_text, "非常好的产品！")

    def test_review_product_relationship(self):
        """测试评价与产品的关系"""
        self.assertEqual(self.product.reviews.count(), 1)
        self.assertEqual(self.product.reviews.first(), self.review)

    def test_review_rating_boundary(self):
        """测试评分边界值"""
        review = ProductReview(
            product=self.product,
            reviewer_name="测试用户2",
            rating=6,
            review_text="评分过高",
        )
        with self.assertRaises(ValidationError):
            review.full_clean()


class AIContentItemModelTest(TestCase):
    """测试AIContentItem模型"""

    def setUp(self):
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
        )
        self.ai_item = AIContentItem.objects.create(
            product=self.product,
            ai_model="gpt-4o",
            content_type="desc",
            content_zh="这是一个很好的产品",
            content_en="This is a great product",
            option_index=1,
            status="draft",
        )

    def test_ai_item_creation(self):
        """测试AI内容项创建"""
        self.assertEqual(self.ai_item.product, self.product)
        self.assertEqual(self.ai_item.ai_model, "gpt-4o")
        self.assertEqual(self.ai_item.content_type, "desc")
        self.assertEqual(self.ai_item.content_zh, "这是一个很好的产品")

    def test_ai_item_product_relationship(self):
        """测试AI内容项与产品的关系"""
        self.assertEqual(self.product.ai_items.count(), 1)
        self.assertEqual(self.product.ai_items.first(), self.ai_item)

    def test_ai_item_content_type_choices(self):
        """测试内容类型选择"""
        valid_types = ["desc", "script", "voice", "img_prompt", "vid_prompt"]
        for content_type in valid_types:
            AIContentItem.objects.create(
                product=self.product,
                ai_model="gpt-4o",
                content_type=content_type,
                content_zh="测试内容",
                option_index=2,
            )


class ProductTagDefinitionModelTest(TestCase):
    """测试ProductTagDefinition模型"""

    def setUp(self):
        self.tag = ProductTagDefinition.objects.create(
            code="candidate",
            name="待发布",
            color="#FF5733",
        )

    def test_tag_creation(self):
        """测试标签定义创建"""
        self.assertEqual(self.tag.code, "candidate")
        self.assertEqual(self.tag.name, "待发布")
        self.assertEqual(self.tag.color, "#FF5733")

    def test_tag_unique_code(self):
        """测试标签code唯一性"""
        with self.assertRaises(Exception):
            ProductTagDefinition.objects.create(
                code="candidate",
                name="重复标签",
            )


# ----------------------------------------------------------------------
# 2. 序列化器测试
# ----------------------------------------------------------------------
class ProductSerializerTest(TestCase):
    """测试ProductSerializer"""

    def setUp(self):
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
            final_price=Decimal("80.00"),
            category="电子产品",
        )
        ProductImage.objects.create(
            product=self.product,
            image_type="main",
            original_url="https://example.com/image1.jpg",
        )

    def test_product_serializer_basic_fields(self):
        """测试基本字段序列化"""
        serializer = ProductSerializer(self.product)
        data = serializer.data
        self.assertEqual(data["source_id"], "test_product_001")
        self.assertEqual(data["title"], "测试产品")
        self.assertEqual(data["category"], "电子产品")

    def test_product_serializer_nested_images(self):
        """测试嵌套图片序列化"""
        serializer = ProductSerializer(self.product)
        data = serializer.data
        self.assertIn("images", data)
        self.assertEqual(len(data["images"]), 1)
        self.assertEqual(data["images"][0]["image_type"], "main")

    def test_product_serializer_excludes_raw_fields(self):
        """测试排除原始字段"""
        serializer = ProductSerializer(self.product)
        data = serializer.data
        self.assertNotIn("raw_json", data)
        self.assertNotIn("input", data)


class ProductImageSerializerTest(TestCase):
    """测试ProductImageSerializer"""

    def setUp(self):
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
        )
        self.image = ProductImage.objects.create(
            product=self.product,
            image_type="main",
            original_url="https://example.com/image1.jpg",
        )

    def test_image_serializer(self):
        """测试图片序列化"""
        serializer = ProductImageSerializer(self.image)
        data = serializer.data
        self.assertEqual(data["image_type"], "main")
        self.assertEqual(data["original_url"], "https://example.com/image1.jpg")


class ProductVariationSerializerTest(TestCase):
    """测试ProductVariationSerializer"""

    def setUp(self):
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
        )
        self.variation = ProductVariation.objects.create(
            product=self.product,
            sku="SKU001",
            final_price=Decimal("80.00"),
        )

    def test_variation_serializer(self):
        """测试变体序列化"""
        serializer = ProductVariationSerializer(self.variation)
        data = serializer.data
        self.assertEqual(data["sku"], "SKU001")
        self.assertEqual(str(data["final_price"]), "80.00")


# ----------------------------------------------------------------------
# 3. API视图测试
# ----------------------------------------------------------------------
class ProductViewSetTest(APITestCase):
    """测试ProductViewSet API"""

    def setUp(self):
        self.client = APIClient()
        self.product1 = Product.objects.create(
            source_id="product_001",
            title="手机",
            final_price=Decimal("1000.00"),
            category="电子产品",
            available=True,
            In_stock=True,
        )
        self.product2 = Product.objects.create(
            source_id="product_002",
            title="笔记本电脑",
            final_price=Decimal("2000.00"),
            category="电子产品",
            available=False,
            In_stock=False,
        )
        self.product3 = Product.objects.create(
            source_id="product_003",
            title="衣服",
            final_price=Decimal("100.00"),
            category="服装",
            available=True,
            In_stock=True,
        )

    def test_list_products(self):
        """测试获取产品列表"""
        url = reverse("product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_retrieve_product(self):
        """测试获取单个产品"""
        url = reverse("product-detail", kwargs={"pk": self.product1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["source_id"], "product_001")

    def test_create_product(self):
        """测试创建产品"""
        url = reverse("product-list")
        data = {
            "source_id": "product_004",
            "title": "新产品",
            "final_price": "500.00",
            "category": "测试",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.count(), 4)

    def test_update_product(self):
        """测试更新产品"""
        url = reverse("product-detail", kwargs={"pk": self.product1.pk})
        data = {
            "source_id": "product_001",
            "title": "更新后的手机",
            "final_price": "1200.00",
            "category": "电子产品",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.title, "更新后的手机")

    def test_delete_product(self):
        """测试删除产品"""
        url = reverse("product-detail", kwargs={"pk": self.product1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Product.objects.count(), 2)

    def test_search_by_source_id(self):
        """测试按source_id搜索"""
        url = reverse("product-list")
        response = self.client.get(url, {"search": "product_001"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["source_id"], "product_001")

    def test_search_by_title(self):
        """测试按标题搜索"""
        url = reverse("product-list")
        response = self.client.get(url, {"search": "手机"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_available(self):
        """测试按可用性过滤"""
        url = reverse("product-list")
        response = self.client.get(url, {"available": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_in_stock(self):
        """测试按库存过滤"""
        url = reverse("product-list")
        response = self.client.get(url, {"In_stock": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_category(self):
        """测试按分类过滤"""
        url = reverse("product-list")
        response = self.client.get(url, {"category": "电子产品"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_final_price(self):
        """测试按价格过滤"""
        url = reverse("product-list")
        response = self.client.get(url, {"final_price": "1000.00"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_multiple_filters(self):
        """测试多重过滤"""
        url = reverse("product-list")
        response = self.client.get(
            url, {"available": "true", "category": "电子产品"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class ProductVariationViewSetTest(APITestCase):
    """测试ProductVariationViewSet API"""

    def setUp(self):
        self.client = APIClient()
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
        )
        self.variation1 = ProductVariation.objects.create(
            product=self.product,
            sku="SKU001",
            stock=100,
            final_price=Decimal("80.00"),
        )
        self.variation2 = ProductVariation.objects.create(
            product=self.product,
            sku="SKU002",
            stock=50,
            final_price=Decimal("90.00"),
        )

    def test_list_variations(self):
        """测试获取变体列表"""
        url = reverse("productvariation-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_product(self):
        """测试按产品过滤变体"""
        url = reverse("productvariation-list")
        response = self.client.get(url, {"product": self.product.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_sku(self):
        """测试按SKU过滤"""
        url = reverse("productvariation-list")
        response = self.client.get(url, {"sku": "SKU001"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_stock(self):
        """测试按库存过滤"""
        url = reverse("productvariation-list")
        response = self.client.get(url, {"stock": "100"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


# ----------------------------------------------------------------------
# 4. 视图函数测试
# ----------------------------------------------------------------------
class ProductFetchViewTest(TestCase):
    """测试product_fetch_view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin",
            password="admin123",
        )
        self.client.login(username="admin", password="admin123")

    def test_get_product_fetch_view(self):
        """测试GET请求获取表单页面"""
        response = self.client.get("/api/fetch/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TikTok 产品数据抓取")

    def test_post_product_fetch_view_with_urls(self):
        """测试POST请求提交URL列表"""
        with mock.patch("products.views.async_task"):
            response = self.client.post(
                "/api/fetch/",
                {
                    "collection_mode": "url",
                    "product_urls": "https://example.com/product1\nhttps://example.com/product2",
                },
            )
            self.assertEqual(response.status_code, 302)

    def test_post_product_fetch_view_empty_urls(self):
        """测试POST请求提交空URL列表"""
        response = self.client.post(
            "/api/fetch/",
            {
                "collection_mode": "url",
                "product_urls": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "请输入至少一个有效的 URL")


class ExportProductJsonViewTest(TestCase):
    """测试export_product_json_view"""

    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
            final_price=Decimal("80.00"),
            category="电子产品",
        )

    def test_export_product_json(self):
        """测试导出产品JSON"""
        url = reverse("export_product_json", kwargs={"product_id": self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_export_nonexistent_product(self):
        """测试导出不存在的产品"""
        url = reverse("export_product_json", kwargs={"product_id": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class N8nAnalyzeViewTest(TestCase):
    """测试n8n_analyze_view"""

    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
            final_price=Decimal("80.00"),
            category="电子产品",
        )

    @override_settings(N8N_WEBHOOK_OPTIMIZE_PRODUCT_URL="http://example.com/webhook")
    @mock.patch("products.views.requests.post")
    def test_n8n_analyze_success(self, mock_post):
        """测试n8n分析成功"""
        mock_response = MockResponse(
            status_code=200,
            json_data={"desc_1": "优化后的描述1", "desc_2": "优化后的描述2"},
        )
        mock_post.return_value = mock_response

        url = reverse("n8n_analyze", kwargs={"product_id": self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.product.refresh_from_db()
        self.assertEqual(self.product.description_1, "优化后的描述1")
        self.assertEqual(self.product.description_2, "优化后的描述2")

    @override_settings(N8N_WEBHOOK_OPTIMIZE_PRODUCT_URL="http://example.com/webhook")
    @mock.patch("products.views.requests.post")
    def test_n8n_analyze_failure(self, mock_post):
        """测试n8n分析失败"""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        url = reverse("n8n_analyze", kwargs={"product_id": self.product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class UpdateProductAPITest(TestCase):
    """测试update_product_api"""

    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            source_id="test_product_001",
            title="测试产品",
            final_price=Decimal("80.00"),
        )

    @override_settings(N8N_API_SECRET="test_secret")
    def test_update_product_api_success(self):
        """测试更新产品API成功"""
        url = reverse("update_product_api")
        data = {
            "api_key": "test_secret",
            "product_id": "test_product_001",
            "model_name": "gpt-4o",
            "desc_zh": ["中文描述1", "中文描述2"],
            "desc_en": ["English description 1", "English description 2"],
            "script_zh": ["中文脚本"],
            "script_en": ["English script"],
        }
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        self.assertEqual(self.product.ai_items.count(), 3)

    @override_settings(N8N_API_SECRET="test_secret")
    def test_update_product_api_unauthorized(self):
        """测试更新产品API未授权"""
        url = reverse("update_product_api")
        data = {
            "api_key": "wrong_secret",
            "product_id": "test_product_001",
            "desc_zh": ["中文描述"],
        }
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(N8N_API_SECRET="test_secret")
    def test_update_product_api_product_not_found(self):
        """测试更新产品API产品不存在"""
        url = reverse("update_product_api")
        data = {
            "api_key": "test_secret",
            "product_id": "nonexistent_product",
            "desc_zh": ["中文描述"],
        }
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)


# ----------------------------------------------------------------------
# 5. 任务测试
# ----------------------------------------------------------------------
class TriggerBrightDataTaskTest(TestCase):
    """测试trigger_bright_data_task"""

    @override_settings(
        BRIGHT_DATA_API_KEY="test_api_key",
        BRIGHT_DATA_BASE_SCRAPE_URL="http://example.com/scrape",
        BRIGHT_DATA_DISCOVER_TYPE="discover/",
        BRIGHT_DATA_DISCOVER_BY_CATEGORY="category/",
        BRIGHT_DATA_DISCOVER_BY_SHOP="shop/",
        BRIGHT_DATA_DISCOVER_BY_KEYWORD="keyword/",
        BRIGHT_DATA_PARAM_LIMIT_PER_INPUT="?limit=10",
    )
    @mock.patch("products.tasks.requests.post")
    @mock.patch("products.tasks._schedule_delayed_poll")
    def test_trigger_task_url_mode(self, mock_schedule, mock_post):
        """测试URL模式触发任务"""
        mock_response = MockResponse(
            status_code=200,
            json_data={"snapshot_id": "test_snapshot_001"},
        )
        mock_post.return_value = mock_response

        urls = ["https://example.com/product1"]
        result = trigger_bright_data_task(urls, "url")

        self.assertTrue(result)
        self.assertTrue(mock_schedule.called)

    @override_settings(
        BRIGHT_DATA_API_KEY="test_api_key",
        BRIGHT_DATA_BASE_SCRAPE_URL="http://example.com/scrape",
        BRIGHT_DATA_DISCOVER_TYPE="discover/",
        BRIGHT_DATA_DISCOVER_BY_CATEGORY="category/",
        BRIGHT_DATA_DISCOVER_BY_SHOP="shop/",
        BRIGHT_DATA_DISCOVER_BY_KEYWORD="keyword/",
        BRIGHT_DATA_PARAM_LIMIT_PER_INPUT="?limit=10",
    )
    @mock.patch("products.tasks.requests.post")
    def test_trigger_task_category_mode(self, mock_post):
        """测试分类模式触发任务"""
        mock_response = MockResponse(
            status_code=200,
            json_data={"snapshot_id": "test_snapshot_002"},
        )
        mock_post.return_value = mock_response

        urls = ["https://example.com/category1"]
        result = trigger_bright_data_task(urls, "category")

        self.assertTrue(result)

    @override_settings(
        BRIGHT_DATA_API_KEY="test_api_key",
        BRIGHT_DATA_BASE_SCRAPE_URL="http://example.com/scrape",
        BRIGHT_DATA_DISCOVER_TYPE="discover/",
        BRIGHT_DATA_DISCOVER_BY_CATEGORY="category/",
        BRIGHT_DATA_DISCOVER_BY_SHOP="shop/",
        BRIGHT_DATA_DISCOVER_BY_KEYWORD="keyword/",
        BRIGHT_DATA_PARAM_LIMIT_PER_INPUT="?limit=10",
    )
    @mock.patch("products.tasks.requests.post")
    def test_trigger_task_shop_mode(self, mock_post):
        """测试店铺模式触发任务"""
        mock_response = MockResponse(
            status_code=200,
            json_data={"snapshot_id": "test_snapshot_003"},
        )
        mock_post.return_value = mock_response

        urls = ["https://example.com/shop1"]
        result = trigger_bright_data_task(urls, "shop")

        self.assertTrue(result)

    @override_settings(
        BRIGHT_DATA_API_KEY="test_api_key",
        BRIGHT_DATA_BASE_SCRAPE_URL="http://example.com/scrape",
        BRIGHT_DATA_DISCOVER_TYPE="discover/",
        BRIGHT_DATA_DISCOVER_BY_CATEGORY="category/",
        BRIGHT_DATA_DISCOVER_BY_SHOP="shop/",
        BRIGHT_DATA_DISCOVER_BY_KEYWORD="keyword/",
        BRIGHT_DATA_PARAM_LIMIT_PER_INPUT="?limit=10",
    )
    @mock.patch("products.tasks.requests.post")
    def test_trigger_task_keyword_mode(self, mock_post):
        """测试关键词模式触发任务"""
        mock_response = MockResponse(
            status_code=200,
            json_data={"snapshot_id": "test_snapshot_004"},
        )
        mock_post.return_value = mock_response

        urls = ["test_keyword"]
        result = trigger_bright_data_task(urls, "keyword")

        self.assertTrue(result)

    @override_settings(
        BRIGHT_DATA_API_KEY="test_api_key",
        BRIGHT_DATA_BASE_SCRAPE_URL="http://example.com/scrape",
    )
    @mock.patch("products.tasks.requests.post")
    def test_trigger_task_api_failure(self, mock_post):
        """测试API调用失败"""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        urls = ["https://example.com/product1"]
        result = trigger_bright_data_task(urls, "url")

        self.assertFalse(result)


class PollBrightDataResultTest(TestCase):
    """测试poll_bright_data_result"""

    @override_settings(
        BRIGHT_DATA_API_KEY="test_api_key",
        BRIGHT_DATA_STATUS_URL="http://example.com/status/",
        BRIGHT_DATA_DOWNLOAD_BASE_URL="http://example.com/download/",
    )
    @mock.patch("products.tasks.requests.get")
    @mock.patch("products.tasks.async_task")
    def test_poll_ready_status(self, mock_async_task, mock_get):
        """测试轮询到ready状态"""
        mock_status_response = MockResponse(
            status_code=200,
            json_data={"status": "ready"},
        )
        mock_download_response = MockResponse(
            status_code=200,
            json_data=[{"id": "1", "title": "Product 1"}],
        )
        mock_get.side_effect = [mock_status_response, mock_download_response]

        poll_bright_data_result(["test_snapshot_001"])

        self.assertTrue(mock_async_task.called)

    @override_settings(
        BRIGHT_DATA_API_KEY="test_api_key",
        BRIGHT_DATA_STATUS_URL="http://example.com/status/",
    )
    @mock.patch("products.tasks.requests.get")
    @mock.patch("products.tasks._schedule_delayed_poll")
    def test_poll_pending_status(self, mock_schedule, mock_get):
        """测试轮询到pending状态"""
        mock_response = MockResponse(
            status_code=200,
            json_data={"status": "pending"},
        )
        mock_get.return_value = mock_response

        poll_bright_data_result(["test_snapshot_001"])

        self.assertTrue(mock_schedule.called)

    @override_settings(
        BRIGHT_DATA_API_KEY="test_api_key",
        BRIGHT_DATA_STATUS_URL="http://example.com/status/",
    )
    @mock.patch("products.tasks.requests.get")
    @mock.patch("products.tasks._schedule_delayed_poll")
    def test_poll_running_status(self, mock_schedule, mock_get):
        """测试轮询到running状态"""
        mock_response = MockResponse(
            status_code=200,
            json_data={"status": "running"},
        )
        mock_get.return_value = mock_response

        poll_bright_data_result(["test_snapshot_001"])

        self.assertTrue(mock_schedule.called)

    @override_settings(
        BRIGHT_DATA_API_KEY="test_api_key",
        BRIGHT_DATA_STATUS_URL="http://example.com/status/",
    )
    @mock.patch("products.tasks.requests.get")
    @mock.patch("products.tasks._schedule_delayed_poll")
    def test_poll_collecting_status(self, mock_schedule, mock_get):
        """测试轮询到collecting状态"""
        mock_response = MockResponse(
            status_code=200,
            json_data={"status": "collecting"},
        )
        mock_get.return_value = mock_response

        poll_bright_data_result(["test_snapshot_001"])

        self.assertTrue(mock_schedule.called)


class SaveSnapshotFileTest(TestCase):
    """测试save_snapshot_file"""

    @override_settings(BASE_DIR="d:\\Python\\tiktok_pm")
    def test_save_snapshot_file(self):
        """测试保存快照文件"""
        snapshot_id = "test_snapshot_001"
        data = [{"id": "1", "title": "Product 1"}]

        save_snapshot_file(snapshot_id, data)

        expected_path = os.path.join(
            "d:\\Python\\tiktok_pm", "data", "json", f"snapshot_{snapshot_id}.json"
        )
        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data, data)

        os.remove(expected_path)


# ----------------------------------------------------------------------
# 6. 边界条件和异常测试
# ----------------------------------------------------------------------
class BoundaryConditionTests(TestCase):
    """边界条件和异常场景测试"""

    def test_product_price_zero(self):
        """测试价格为0"""
        product = Product.objects.create(
            source_id="test_product_001",
            title="免费产品",
            final_price=Decimal("0.00"),
        )
        self.assertEqual(product.final_price, Decimal("0.00"))

    def test_product_price_negative(self):
        """测试价格为负数"""
        product = Product(
            source_id="test_product_002",
            title="负价格产品",
            final_price=Decimal("-10.00"),
        )
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_product_title_very_long(self):
        """测试非常长的标题"""
        long_title = "A" * 10000
        product = Product.objects.create(
            source_id="test_product_003",
            title=long_title,
            final_price=Decimal("100.00"),
        )
        self.assertEqual(product.title, long_title)

    def test_product_empty_fields(self):
        """测试空字段"""
        product = Product.objects.create(
            source_id="test_product_004",
            title="",
            final_price=Decimal("100.00"),
        )
        self.assertEqual(product.title, "")

    def test_variation_stock_zero(self):
        """测试库存为0"""
        product = Product.objects.create(
            source_id="test_product_005",
            title="缺货产品",
        )
        variation = ProductVariation.objects.create(
            product=product,
            sku="SKU001",
            stock=0,
            final_price=Decimal("100.00"),
        )
        self.assertEqual(variation.stock, 0)

    def test_variation_stock_negative(self):
        """测试库存为负数"""
        product = Product.objects.create(
            source_id="test_product_006",
            title="负库存产品",
        )
        variation = ProductVariation.objects.create(
            product=product,
            sku="SKU002",
            stock=-10,
            final_price=Decimal("100.00"),
        )
        self.assertEqual(variation.stock, -10)

    def test_review_rating_boundary_low(self):
        """测试评分下边界"""
        product = Product.objects.create(
            source_id="test_product_007",
            title="测试产品",
        )
        review = ProductReview.objects.create(
            product=product,
            reviewer_name="测试用户",
            rating=1,
            review_text="最低评分",
        )
        self.assertEqual(review.rating, 1)

    def test_review_rating_boundary_high(self):
        """测试评分上边界"""
        product = Product.objects.create(
            source_id="test_product_008",
            title="测试产品",
        )
        review = ProductReview.objects.create(
            product=product,
            reviewer_name="测试用户",
            rating=5,
            review_text="最高评分",
        )
        self.assertEqual(review.rating, 5)

    def test_product_tags_empty_list(self):
        """测试空标签列表"""
        product = Product.objects.create(
            source_id="test_product_009",
            title="无标签产品",
            tags=[],
        )
        self.assertEqual(product.tags, [])

    def test_product_tags_multiple(self):
        """测试多个标签"""
        product = Product.objects.create(
            source_id="test_product_010",
            title="多标签产品",
            tags=["hot", "new", "sale"],
        )
        self.assertEqual(len(product.tags), 3)

    def test_json_fields_with_complex_data(self):
        """测试JSON字段存储复杂数据"""
        complex_data = {
            "key1": "value1",
            "key2": {"nested_key": "nested_value"},
            "key3": [1, 2, 3],
        }
        product = Product.objects.create(
            source_id="test_product_011",
            title="复杂数据产品",
            desc_detail=complex_data,
        )
        self.assertEqual(product.desc_detail, complex_data)


class ErrorHandlingTests(TestCase):
    """错误处理测试"""

    def test_product_duplicate_source_id(self):
        """测试重复的source_id"""
        Product.objects.create(
            source_id="duplicate_id",
            title="产品1",
        )
        with self.assertRaises(Exception):
            Product.objects.create(
                source_id="duplicate_id",
                title="产品2",
            )

    def test_variation_duplicate_sku_same_product(self):
        """测试同一产品下重复的SKU"""
        product = Product.objects.create(
            source_id="test_product_012",
            title="测试产品",
        )
        ProductVariation.objects.create(
            product=product,
            sku="duplicate_sku",
            final_price=Decimal("100.00"),
        )
        ProductVariation.objects.create(
            product=product,
            sku="duplicate_sku",
            final_price=Decimal("100.00"),
        )

    def test_product_cascade_delete(self):
        """测试产品级联删除"""
        product = Product.objects.create(
            source_id="test_product_013",
            title="测试产品",
        )
        ProductImage.objects.create(
            product=product,
            image_type="main",
            original_url="https://example.com/image.jpg",
        )
        ProductVideo.objects.create(
            product=product,
            video_type="main",
            original_url="https://example.com/video.mp4",
        )
        ProductVariation.objects.create(
            product=product,
            sku="SKU001",
            final_price=Decimal("100.00"),
        )
        ProductReview.objects.create(
            product=product,
            reviewer_name="测试用户",
            rating=5,
            review_text="好评",
        )

        product_id = product.pk
        product.delete()

        self.assertEqual(ProductImage.objects.filter(product_id=product_id).count(), 0)
        self.assertEqual(ProductVideo.objects.filter(product_id=product_id).count(), 0)
        self.assertEqual(ProductVariation.objects.filter(product_id=product_id).count(), 0)
        self.assertEqual(ProductReview.objects.filter(product_id=product_id).count(), 0)

    def test_api_invalid_json(self):
        """测试API无效JSON"""
        client = APIClient()
        url = reverse("product-list")
        response = self.client.post(
            url, data="invalid json", content_type="application/json"
        )
        self.assertIn(response.status_code, [400, 415])

    def test_api_missing_required_fields(self):
        """测试API缺少必填字段"""
        client = APIClient()
        url = reverse("product-list")
        data = {
            "title": "缺少source_id的产品",
        }
        response = client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)


# ----------------------------------------------------------------------
# 7. 性能测试
# ----------------------------------------------------------------------
class PerformanceTests(TestCase):
    """性能测试"""

    def test_large_product_list_query(self):
        """测试大量产品列表查询性能"""
        for i in range(100):
            Product.objects.create(
                source_id=f"product_{i:04d}",
                title=f"产品 {i}",
                final_price=Decimal(str(i * 10)),
                category="测试",
            )

        client = APIClient()
        url = reverse("product-list")

        import time

        start_time = time.time()
        response = client.get(url)
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 100)
        self.assertLess(end_time - start_time, 2.0)

    def test_product_with_many_relations_query(self):
        """测试产品与多个关联关系的查询性能"""
        product = Product.objects.create(
            source_id="test_product_014",
            title="多关联产品",
        )
        for i in range(10):
            ProductImage.objects.create(
                product=product,
                image_type="main",
                original_url=f"https://example.com/image{i}.jpg",
            )
            ProductVideo.objects.create(
                product=product,
                video_type="main",
                original_url=f"https://example.com/video{i}.mp4",
            )
            ProductVariation.objects.create(
                product=product,
                sku=f"SKU{i:03d}",
                final_price=Decimal(str(i * 10)),
            )

        client = APIClient()
        url = reverse("product-detail", kwargs={"pk": product.pk})

        import time

        start_time = time.time()
        response = client.get(url)
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)


# ----------------------------------------------------------------------
# 8. 集成测试
# ----------------------------------------------------------------------
class IntegrationTests(TestCase):
    """集成测试"""

    def test_complete_product_workflow(self):
        """测试完整的产品工作流"""
        client = APIClient()

        data = {
            "source_id": "workflow_product_001",
            "title": "工作流测试产品",
            "final_price": "100.00",
            "category": "测试",
        }

        create_response = client.post(reverse("product-list"), data, format="json")
        self.assertEqual(create_response.status_code, 201)

        product_id = create_response.data["id"]

        retrieve_response = client.get(
            reverse("product-detail", kwargs={"pk": product_id})
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.data["title"], "工作流测试产品")

        update_data = {
            "source_id": "workflow_product_001",
            "title": "更新后的工作流测试产品",
            "final_price": "120.00",
            "category": "测试",
        }
        update_response = client.put(
            reverse("product-detail", kwargs={"pk": product_id}),
            update_data,
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)

        delete_response = client.delete(
            reverse("product-detail", kwargs={"pk": product_id})
        )
        self.assertEqual(delete_response.status_code, 204)

        self.assertEqual(Product.objects.count(), 0)

    def test_product_with_variations_workflow(self):
        """测试产品与变体的完整工作流"""
        client = APIClient()

        product_data = {
            "source_id": "variation_product_001",
            "title": "变体测试产品",
            "final_price": "100.00",
            "category": "测试",
        }
        product_response = client.post(
            reverse("product-list"), product_data, format="json"
        )
        product_id = product_response.data["id"]

        for i in range(3):
            variation_data = {
                "product": product_id,
                "sku": f"VAR{i:03d}",
                "final_price": str(100 + i * 10),
                "stock": 10 + i,
            }
            client.post(reverse("productvariation-list"), variation_data, format="json")

        product = Product.objects.get(pk=product_id)
        self.assertEqual(product.product_variations.count(), 3)
