# n8n回调API调试指南

## 问题分析

### 问题描述
调用n8n进行AI优化后，返回的JSON数据中，`voice_en`, `voice_zh`, `img_p_en`, `img_p_zh` 字段没有被存储到 `ai_content_items` 表中。

### 根本原因

1. **JSON结构不匹配**
   - n8n返回的格式：`[{"output": {...}}]`
   - 代码直接从 `data` 获取字段，而不是从 `data[0]["output"]` 获取
   - 导致 `data.get("voice_zh")` 等返回 `None`

2. **代码逻辑错误**
   - 虽然在277-291行添加了提取 `output_data` 的代码
   - 但在338-342行调用 `create_items` 时，仍然使用的是 `data` 而不是 `output_data`

## 解决方案

### 修复内容

#### 1. 添加详细的调试日志
```python
logger.debug(f"output_data keys: {output_data.keys() if output_data else 'None'}")
logger.debug(f"desc_zh: {output_data.get('desc_zh')}")
logger.debug(f"desc_en: {output_data.get('desc_en')}")
logger.debug(f"script_zh: {output_data.get('script_zh')}")
logger.debug(f"script_en: {output_data.get('script_en')}")
logger.debug(f"voice_zh: {output_data.get('voice_zh')}")
logger.debug(f"voice_en: {output_data.get('voice_en')}")
logger.debug(f"img_p_zh: {output_data.get('img_p_zh')}")
logger.debug(f"img_p_en: {output_data.get('img_p_en')}")
```

#### 2. 修正字段获取逻辑
```python
# 修复前（错误）
create_items(data.get("desc_zh"), data.get("desc_en"), "desc")
create_items(data.get("script_zh"), data.get("script_en"), "script")
create_items(data.get("voice_zh"), data.get("voice_en"), "voice")
create_items(data.get("img_p_zh"), data.get("img_p_en"), "img_prompt")
create_items(data.get("vid_p_zh"), data.get("vid_p_en"), "vid_prompt")

# 修复后（正确）
create_items(output_data.get("desc_zh"), output_data.get("desc_en"), "desc")
create_items(output_data.get("script_zh"), output_data.get("script_en"), "script")
create_items(output_data.get("voice_zh"), output_data.get("voice_en"), "voice")
create_items(output_data.get("img_p_zh"), output_data.get("img_p_en"), "img_prompt")
create_items(output_data.get("vid_p_zh"), output_data.get("vid_p_en"), "vid_prompt")
```

#### 3. 增强create_items函数的日志
```python
def create_items(data_list_zh, data_list_en, type_key):
    # 添加详细日志
    logger.debug(f"create_items called - Type: {type_key}")
    logger.debug(f"  data_list_zh type: {type(data_list_zh)}, value: {data_list_zh}")
    logger.debug(f"  data_list_en type: {type(data_list_en)}, value: {data_list_en}")

    # ... 处理逻辑 ...

    for i in range(length):
        created_item = AIContentItem.objects.create(...)
        logger.debug(f"Created AIContentItem - ID: {created_item.id}, Type: {type_key}, Index: {i + 1}")
```

## 测试步骤

### 1. 启动Django服务器
```bash
python manage.py runserver
```

### 2. 运行测试脚本
```bash
python test_n8n_callback.py
```

### 3. 查看日志输出
在Django控制台中查看详细的调试日志，应该能看到：
- `output_data keys` 显示所有可用的字段
- 每个字段的值
- `create_items called` 显示每次调用
- `Created AIContentItem` 显示创建的记录

### 4. 验证数据库
```python
from products.models import AIContentItem, Product

# 查询某个产品的所有AI内容
product = Product.objects.get(source_id="123456789")
items = AIContentItem.objects.filter(product=product)

# 按类型分组查看
for item in items:
    print(f"Type: {item.content_type}, Index: {item.option_index}")
    print(f"  ZH: {item.content_zh[:50]}...")
    print(f"  EN: {item.content_en[:50]}...")
    print("-" * 80)
```

## 预期结果

修复后，应该能看到以下类型的AI内容都被正确存储：
- `desc` - 产品描述
- `script` - 视频脚本
- `voice` - 语音文案
- `img_prompt` - 图片提示词
- `vid_prompt` - 视频提示词

每种类型都应该有中文和英文两个版本。

## 常见问题排查

### 问题1：仍然没有存储voice和img

**检查清单：**
1. 确认n8n返回的JSON格式正确
2. 检查日志中 `output_data keys` 是否包含 `voice_zh`, `voice_en`, `img_p_zh`, `img_p_en`
3. 确认这些字段的值不为空
4. 检查数据库中是否有 `status="draft"` 的旧记录被删除

### 问题2：日志显示字段值为None

**可能原因：**
1. n8n返回的字段名不匹配
2. JSON结构解析错误
3. 字段在n8n工作流中未正确配置

**解决方案：**
1. 检查n8n工作流的输出节点
2. 确认字段名与代码期望的一致
3. 使用日志输出完整的 `output_data` 进行对比

### 问题3：数据库记录创建失败

**检查清单：**
1. 确认 `product` 对象存在
2. 检查数据库连接是否正常
3. 查看是否有数据库约束冲突
4. 检查 `AIContentItem` 模型的字段验证

## 调试技巧

### 1. 使用Django shell测试
```python
python manage.py shell

from products.views import update_product_api
from django.test import RequestFactory
import json

# 创建模拟请求
factory = RequestFactory()
request_data = {
    "api_key": "your-api-secret",
    "product_id": "123456789",
    "model_name": "gpt-4",
    "output": {
        "desc_zh": "测试描述",
        "desc_en": "Test description",
        "voice_zh": "测试语音",
        "voice_en": "Test voice",
        "img_p_zh": "测试图片提示",
        "img_p_en": "Test image prompt"
    }
}

request = factory.post('/api/update_product/', 
                      json.dumps(request_data),
                      content_type='application/json')

# 调用视图函数
response = update_product_api(request)
print(response.content)
```

### 2. 查看SQL查询
在settings.py中添加：
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

### 3. 使用Postman或curl测试
```bash
curl -X POST http://localhost:8000/api/update_product/ \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-secret",
    "product_id": "123456789",
    "model_name": "gpt-4",
    "output": {
      "desc_zh": "测试描述",
      "desc_en": "Test description",
      "voice_zh": "测试语音",
      "voice_en": "Test voice",
      "img_p_zh": "测试图片提示",
      "img_p_en": "Test image prompt"
    }
  }'
```

## 总结

问题的核心在于：
1. **数据源错误**：使用了 `data` 而不是 `output_data`
2. **缺少日志**：难以追踪问题所在

修复后：
1. 正确从 `output_data` 获取字段
2. 添加了详细的调试日志
3. 可以清楚地看到每个字段的处理过程

建议在开发过程中保持详细的日志记录，以便快速定位和解决问题。
