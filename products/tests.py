# products/tests.py

from django.test import TestCase, override_settings
from unittest import mock
import json
import requests
import pymysql

# 假设您的 tasks.py 和 importer_wrapper.py 路径是正确的
from products.tasks import poll_bright_data_result, BRIGHT_DATA_DOWNLOAD_BASE_URL
from products.importer_wrapper import start_import_process

# 模拟一个成功下载的产品列表 (JSON Lines 格式，模拟真实场景)
MOCK_PRODUCT_DATA_LINES = (
    '{"id": "P1", "title": "Product A", "price": 10.0}\n'
    '{"id": "P2", "title": "Product B", "price": 20.0}\n'
    '{"id": "P3", "title": "Product C", "price": 30.0}'
)

# 模拟一个成功下载的产品列表 (JSON 数组格式)
MOCK_PRODUCT_DATA_ARRAY = [
    {"id": "P4", "title": "Product D", "price": 40.0},
    {"id": "P5", "title": "Product E", "price": 50.0},
]


# 模拟 requests.Response 对象
class MockResponse:
    def __init__(self, status_code, json_data=None, text_data=None):
        self.status_code = status_code
        self._json_data = json_data
        self._text_data = text_data
        self.text = text_data if text_data is not None else json.dumps(json_data)

    def json(self):
        if self._json_data is not None:
            return self._json_data
        # 如果 self._json_data 是 None，但我们尝试调用 json()，我们根据 text 模拟解析失败
        raise json.JSONDecodeError("Mock JSON Decode Error", self.text, 0)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error")


# 模拟 pymysql 连接对象
class MockCursor:
    def execute(self, sql, args=None):
        pass  # 模拟执行成功

    def fetchone(self):
        return (1,)  # 模拟返回一个 ID

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


# products/tests.py (继续)

# 覆盖 settings，使用一个模拟的数据库配置，确保它是 pymysql 风格
@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'tiktok_products_mock',
            'USER': 'root',
            'PASSWORD': 'abcd1234',
            'HOST': '192.168.3.17',
            'PORT': 3306,
        }
    }
)
class ProductImportTests(TestCase):

    # -------------------------------------------------------------------
    # 测试 1: 模拟 Bright Data 状态查询和 JSON Lines 数据导入
    # -------------------------------------------------------------------
    @mock.patch('products.importer_wrapper.pymysql.connect', return_value=MockConnection())
    @mock.patch('products.tasks.requests.get')
    @mock.patch('products.importer_wrapper.core.insert_product', return_value=123)
    def test_poll_and_import_with_json_lines(self, mock_insert_product, mock_requests_get, mock_pymysql_connect):
        snapshot_id = 'sd_mibdfnwodfw6xxkv1'

        # 1. 设置状态查询响应 (返回 finished)
        mock_status_response = MockResponse(
            status_code=200,
            json_data={'status': 'ready'}
        )

        # 2. 设置下载数据响应 (返回 JSON Lines 格式文本)
        mock_download_response = MockResponse(
            status_code=200,
            text_data=MOCK_PRODUCT_DATA_LINES
        )

        # 模拟 requests.get 调用：第一次查状态，第二次下载数据
        mock_requests_get.side_effect = [
            mock_status_response,
            mock_download_response
        ]

        # ACT (执行 poll_bright_data_result)
        result = poll_bright_data_result(snapshot_id)

        # ASSERT 1: 验证轮询任务成功结束
        self.assertTrue(result, "poll_bright_data_result 应该返回 True")

        # ASSERT 2: 验证 pymysql 连接被调用，证明连接配置正确
        self.assertTrue(mock_pymysql_connect.called, "pymysql.connect 应该被调用")

        # ASSERT 3: 验证 core.insert_product 被调用的次数 (MOCK_PRODUCT_DATA_LINES 有 3 个产品)
        expected_calls = 3
        actual_calls = mock_insert_product.call_count
        self.assertEqual(actual_calls, expected_calls, f"insert_product 应该被调用 {expected_calls} 次")

        # ASSERT 4: 验证 download URL 是否正确
        expected_download_url = f"{BRIGHT_DATA_DOWNLOAD_BASE_URL}{snapshot_id}?format=json"
        # 验证第二次 requests.get 的调用参数
        mock_requests_get.call_args_list[1].args[0] == expected_download_url

    # -------------------------------------------------------------------
    # 测试 2: 模拟 Bright Data 状态查询和 JSON 数组数据导入
    # -------------------------------------------------------------------
    @mock.patch('products.importer_wrapper.pymysql.connect', return_value=MockConnection())
    @mock.patch('products.tasks.requests.get')
    @mock.patch('products.importer_wrapper.core.insert_product', return_value=123)
    def test_poll_and_import_with_json_array(self, mock_insert_product, mock_requests_get, mock_pymysql_connect):
        snapshot_id = 'sd_mibdfnwodfw6xxkv1'

        # 1. 设置状态查询响应 (返回 finished)
        mock_status_response = MockResponse(
            status_code=200,
            json_data={'status': 'ready'}
        )

        # 2. 设置下载数据响应 (返回 JSON 数组数据)
        mock_download_response = MockResponse(
            status_code=200,
            json_data=MOCK_PRODUCT_DATA_ARRAY
        )

        # 模拟 requests.get 调用：第一次查状态，第二次下载数据
        mock_requests_get.side_effect = [
            mock_status_response,
            mock_download_response
        ]

        # ACT (执行 poll_bright_data_result)
        result = poll_bright_data_result(snapshot_id)

        # ASSERT 1: 验证轮询任务成功结束
        self.assertTrue(result, "poll_bright_data_result 应该返回 True")

        # ASSERT 2: 验证 core.insert_product 被调用的次数 (MOCK_PRODUCT_DATA_ARRAY 有 2 个产品)
        expected_calls = 2
        actual_calls = mock_insert_product.call_count
        self.assertEqual(actual_calls, expected_calls, f"insert_product 应该被调用 {expected_calls} 次")