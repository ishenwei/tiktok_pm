# TikTok Product Management System

一个基于Django的TikTok产品数据管理和AI内容优化系统，提供产品数据抓取、管理、导出和AI智能优化功能。

## 项目概述与背景

本项目旨在为电商从业者提供一个高效的TikTok产品数据管理平台。通过自动化数据抓取、智能内容生成和便捷的管理界面，帮助用户快速收集、整理和优化TikTok平台的产品信息，提升电商运营效率。

### 主要应用场景

- **产品数据采集**：从TikTok平台批量抓取产品信息
- **智能内容优化**：利用AI技术生成和优化产品描述
- **数据管理**：集中管理产品、店铺、分类等核心数据
- **API集成**：提供RESTful API支持第三方系统集成
- **异步处理**：支持大规模数据处理的异步任务队列

## 核心功能与特性

### 1. 产品数据管理

- **产品信息管理**：完整的CRUD操作，支持产品标题、描述、价格、库存等字段管理
- **多维度分类**：支持产品分类、标签、店铺等多维度组织
- **图片和视频管理**：支持产品图片、视频的存储和管理
- **产品变体**：支持SKU级别的产品变体管理
- **评论管理**：收集和管理产品评论数据

### 2. 数据采集功能

- **多种采集模式**：
  - URL采集：通过产品链接单个采集
  - 分类采集：通过分类链接批量发现产品
  - 店铺采集：通过店铺链接获取店铺产品
  - 关键词采集：通过关键词搜索相关产品
- **异步任务处理**：使用django-q实现后台异步任务，支持大规模数据采集
- **任务状态跟踪**：实时监控采集任务状态和进度

### 3. AI内容优化

- **智能描述生成**：集成n8n工作流，利用AI生成优化的产品描述
- **多语言支持**：支持中英文内容生成
- **版本管理**：AI生成内容支持草稿和发布状态管理
- **内容对比**：保留原始内容和AI优化内容，便于对比选择

### 4. 数据导出

- **JSON导出**：支持单个产品数据的JSON格式导出
- **结构化数据**：导出包含产品、图片、变体等完整信息
- **API接口**：提供RESTful API支持程序化访问

### 5. 管理后台

- **Django Admin集成**：基于Django Admin构建的管理界面
- **自定义视图**：产品采集、AI优化等专用管理页面
- **图片预览**：支持产品图片的模态框预览
- **标签管理**：可视化的产品标签管理界面

### 6. API接口

- **RESTful API**：基于Django REST Framework的标准化API
- **产品查询**：支持搜索、过滤、排序等多种查询方式
- **变体管理**：产品变体的独立API接口
- **Webhook支持**：接收n8n等外部系统的回调

## 技术栈与架构说明

### 后端技术栈

- **Web框架**：Django 5.2.8
- **API框架**：Django REST Framework 3.16.1
- **数据库**：MySQL（通过PyMySQL 1.1.0）
- **任务队列**：django-q2（异步任务处理）
- **HTTP客户端**：requests
- **环境管理**：python-dotenv

### 前端技术

- **模板引擎**：Django Template
- **富文本编辑器**：django-tinymce 5.0.0
- **静态资源**：CSS/JavaScript自定义管理界面

### 开发工具

- **代码格式化**：Black
- **导入排序**：isort
- **代码检查**：flake8
- **容器化**：Docker & Docker Compose
- **Web服务器**：Gunicorn（生产环境）

### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                         用户界面层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Django Admin │  │ REST API     │  │ 自定义视图   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                         业务逻辑层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Views        │  │ Serializers  │  │ Forms        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Tasks        │  │ Services     │  │ Utils        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                         数据访问层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Models       │  │ Migrations   │  │ QuerySet     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                         外部服务层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ MySQL        │  │ Redis        │  │ n8n Webhook  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 数据库模型

- **Product**：产品核心信息
- **ProductImage**：产品图片
- **ProductVideo**：产品视频
- **ProductVariation**：产品变体
- **ProductReview**：产品评论
- **Store**：店铺信息
- **AIContentItem**：AI生成内容
- **ProductTagDefinition**：产品标签定义

## 环境配置与安装步骤

### 系统要求

- Python 3.13+
- MySQL 8.0+
- Redis 6.0+（用于django-q）
- Docker & Docker Compose（可选，用于容器化部署）

### 本地开发环境搭建

#### 1. 克隆项目

```bash
git clone https://github.com/ishenwei/tiktok_pm.git
cd tiktok_pm
```

#### 2. 创建虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

创建 `.env` 文件：

```env
# Django配置
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置
DB_NAME=tiktok_products_dev
DB_USER=root
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=3306

# Redis配置（用于django-q）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Bright Data配置
BRIGHT_DATA_API_URL=https://api.brightdata.com
BRIGHT_DATA_DOWNLOAD_BASE_URL=https://download.brightdata.com
BRIGHT_DATA_API_KEY=your-bright-data-api-key

# n8n配置
N8N_WEBHOOK_OPTIMIZE_PRODUCT_URL=https://your-n8n-instance.com/webhook/optimize-product
N8N_API_SECRET=your-n8n-api-secret
```

#### 5. 数据库初始化

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE tiktok_products_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 运行迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 导入初始数据（可选）
python manage.py import_json_data
```

#### 6. 启动服务

```bash
# 启动Django开发服务器
python manage.py runserver

# 启动django-q worker（新终端）
python manage.py qcluster
```

### Docker部署

#### 1. 使用Docker Compose

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 2. 单独构建Docker镜像

```bash
docker build -t tiktok_pm .
docker run -p 8000:8000 --env-file .env tiktok_pm
```

### 代码规范配置

项目已配置以下代码规范工具：

- **Black**：代码格式化
- **isort**：导入排序
- **flake8**：代码质量检查

运行代码检查：

```bash
# 格式化代码
black .
isort .

# 检查代码质量
flake8 .
```

## 使用指南与操作示例

### 管理后台使用

#### 1. 访问管理后台

启动服务后，访问 `http://localhost:8000/admin/`，使用超级用户账号登录。

#### 2. 产品数据采集

1. 进入"Products"应用
2. 点击"TikTok产品数据抓取"
3. 选择采集模式：
   - URL采集：输入产品链接
   - 分类采集：输入分类链接
   - 店铺采集：输入店铺链接
   - 关键词采集：输入关键词
4. 点击"提交采集任务"
5. 系统将创建异步任务，后台自动抓取数据

#### 3. AI内容优化

1. 在产品列表中选择要优化的产品
2. 点击"n8n分析"按钮
3. 系统将：
   - 生成产品JSON数据
   - 发送到n8n工作流
   - 接收AI优化的描述内容
   - 自动更新产品的description_1和description_2字段

#### 4. 导出产品数据

1. 在产品详情页点击"导出JSON"
2. 系统将下载包含产品完整信息的JSON文件

### API使用示例

#### 1. 获取产品列表

```bash
# 基础查询
curl http://localhost:8000/api/products/

# 搜索产品
curl "http://localhost:8000/api/products/?search=keyword"

# 过滤产品
curl "http://localhost:8000/api/products/?available=true&category=electronics"

# 排序
curl "http://localhost:8000/api/products/?ordering=-final_price"
```

#### 2. 获取单个产品

```bash
curl http://localhost:8000/api/products/1/
```

#### 3. 创建产品

```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "123456789",
    "title": "示例产品",
    "description": "产品描述",
    "final_price": 99.99,
    "available": true
  }'
```

#### 4. 更新产品

```bash
curl -X PUT http://localhost:8000/api/products/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的产品标题",
    "final_price": 89.99
  }'
```

#### 5. 删除产品

```bash
curl -X DELETE http://localhost:8000/api/products/1/
```

#### 6. 产品变体操作

```bash
# 获取产品变体
curl http://localhost:8000/api/variations/

# 创建变体
curl -X POST http://localhost:8000/api/variations/ \
  -H "Content-Type: application/json" \
  -d '{
    "product": 1,
    "sku": "VAR-001",
    "final_price": 99.99,
    "stock": 100
  }'
```

### 命令行工具

#### 1. 导入JSON数据

```bash
python manage.py import_json_data
```

#### 2. 运行测试

```bash
# 运行所有测试
python manage.py test

# 运行特定应用的测试
python manage.py test products

# 运行特定测试类
python manage.py test products.tests.ProductModelTest

# 保持测试数据库
python manage.py test --keepdb

# 显示详细输出
python manage.py test --verbosity=2
```

#### 3. Django系统检查

```bash
python manage.py check
```

### 异步任务监控

django-q任务监控：

```bash
# 查看任务状态
python manage.py qmonitor

# 清理已完成的任务
python manage.py qclean
```

## API文档

### 认证

当前API使用Django Admin的session认证，需要先登录管理后台。

### 产品API (Products)

#### GET /api/products/

获取产品列表，支持搜索、过滤和排序。

**查询参数：**

- `search`：搜索关键词（支持source_id、title、description）
- `available`：可用状态过滤
- `In_stock`：库存状态过滤
- `category`：分类过滤
- `seller_id`：卖家ID过滤
- `final_price`：价格过滤
- `ordering`：排序字段（支持`-`前缀降序）

**响应示例：**

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "source_id": "123456789",
      "title": "示例产品",
      "description": "产品描述",
      "final_price": 99.99,
      "available": true,
      "images": [
        {
          "id": 1,
          "original_url": "https://example.com/image.jpg",
          "image_type": "main"
        }
      ],
      "variations": [
        {
          "id": 1,
          "sku": "VAR-001",
          "final_price": 99.99,
          "stock": 100
        }
      ]
    }
  ]
}
```

#### GET /api/products/{id}/

获取单个产品详情。

**响应示例：**

```json
{
  "id": 1,
  "source_id": "123456789",
  "title": "示例产品",
  "description": "产品描述",
  "description_1": "AI优化的描述1",
  "description_2": "AI优化的描述2",
  "final_price": 99.99,
  "initial_price": 129.99,
  "discount_percent": 23.08,
  "available": true,
  "In_stock": true,
  "category": "electronics",
  "seller_id": "seller123",
  "images": [...],
  "variations": [...],
  "videos": [...],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-02T00:00:00Z"
}
```

#### POST /api/products/

创建新产品。

**请求体：**

```json
{
  "source_id": "123456789",
  "title": "新产品",
  "description": "产品描述",
  "final_price": 99.99,
  "available": true
}
```

#### PUT /api/products/{id}/

更新产品信息。

#### DELETE /api/products/{id}/

删除产品。

### 产品变体API (Variations)

#### GET /api/variations/

获取产品变体列表。

**查询参数：**

- `product`：产品ID过滤
- `sku`：SKU过滤
- `stock`：库存过滤
- `search`：搜索（支持sku、product__source_id）

#### POST /api/variations/

创建产品变体。

**请求体：**

```json
{
  "product": 1,
  "sku": "VAR-001",
  "final_price": 99.99,
  "stock": 100
}
```

### 专用API端点

#### POST /api/update_product/

接收n8n回调，更新产品AI内容。

**请求头：**

- `Content-Type: application/json`

**请求体：**

```json
{
  "api_key": "your-n8n-api-secret",
  "product_id": "123456789",
  "model_name": "gpt-4",
  "desc_1_zh": "中文描述1",
  "desc_1_en": "English description 1",
  "desc_2_zh": "中文描述2",
  "desc_2_en": "English description 2"
}
```

**响应：**

```json
{
  "status": "success",
  "message": "产品更新成功",
  "product_id": "123456789"
}
```

#### GET /api/export/{product_id}/

导出产品JSON数据。

**响应：**

```json
{
  "id": "123456789",
  "title": "示例产品",
  "category": "electronics",
  "url": "https://tiktok.com/product/123456789",
  "price": "99.99",
  "description": "产品描述",
  "description_detail": "详细描述",
  "specifications": "规格参数",
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ]
}
```

#### POST /api/n8n-analyze/{product_id}/

触发n8n分析流程。

**响应：**

成功时重定向到产品详情页，并在页面显示操作结果。

### 错误响应

所有API在出错时返回标准错误格式：

```json
{
  "status": "error",
  "message": "错误描述",
  "details": {}
}
```

常见HTTP状态码：

- `200 OK`：请求成功
- `201 Created`：资源创建成功
- `400 Bad Request`：请求参数错误
- `403 Forbidden`：权限不足
- `404 Not Found`：资源不存在
- `500 Internal Server Error`：服务器内部错误

## 测试

### 测试覆盖

项目包含完整的测试套件，覆盖以下方面：

- **模型测试**：验证数据模型的创建、验证和关系
- **序列化器测试**：验证数据序列化和反序列化
- **视图测试**：验证API端点的功能和响应
- **任务测试**：验证异步任务的执行
- **边界条件测试**：验证极端情况下的系统行为
- **错误处理测试**：验证异常情况的处理
- **性能测试**：验证系统性能指标
- **集成测试**：验证各组件的集成

### 运行测试

```bash
# 运行所有测试
python manage.py test

# 运行特定测试
python manage.py test products.tests.ProductModelTest

# 查看测试覆盖率（需要安装coverage）
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### 测试结果

当前测试套件包含85个测试用例，全部通过：

```
Ran 85 tests in 5.401s
OK
```

## 贡献规范

### 贡献流程

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 提交规范

遵循[Conventional Commits](https://www.conventionalcommits.org/)规范：

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 重构（既不是新功能也不是修复）
- `test`: 添加测试
- `chore`: 构建过程或辅助工具的变动

示例：

```
feat: 添加产品批量导入功能

- 支持CSV文件导入
- 添加数据验证
- 实现导入进度显示
```

### 代码规范

- 遵循PEP 8代码风格
- 使用Black进行代码格式化
- 使用isort进行导入排序
- 使用flake8进行代码检查
- 为新功能添加测试用例
- 保持测试覆盖率在80%以上

### Pull Request要求

- 清晰描述PR的目的和变更内容
- 所有测试通过
- 代码通过flake8检查
- 更新相关文档
- 解决所有代码审查意见

## 许可协议

本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。

## 联系方式与问题反馈

### 项目维护者

- **GitHub**: [ishenwei](https://github.com/ishenwei)

### 问题反馈

如果您遇到问题或有建议，请通过以下方式反馈：

1. **GitHub Issues**: [提交Issue](https://github.com/ishenwei/tiktok_pm/issues)
   - 报告bug
   - 提出新功能建议
   - 提出改进意见

2. **Pull Requests**: 欢迎提交PR来改进项目

### 获取帮助

- 查看项目文档和API文档
- 搜索已有的Issues
- 在Issue中提供详细的问题描述和复现步骤

### 社区

欢迎加入项目讨论，共同改进这个系统。

---

**注意**: 本项目仅用于学习和研究目的，请遵守TikTok平台的使用条款和相关法律法规。
