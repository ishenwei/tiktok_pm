# products/importer_wrapper.py
import pymysql
import pymysql.cursors
from django.conf import settings
from . import importer_core as core  # 导入核心函数


def import_products_from_list(products_list):
    """
    建立数据库连接，并循环导入产品数据。

    :param products_list: 从 Bright Data 下载的产品字典列表。
    """

    # 1. 使用 settings.py 中定义的 pymysql 配置
    # 1. 确保获取的是 'default' 配置字典
    db_config = settings.DATABASES['default']
    # 🌟 关键修正 1：恢复端口号的类型转换和容错 🌟
    # 从 db_config 中获取 PORT，并确保它是 int 类型
    try:
        # 获取 PORT 字段，如果缺失则默认为 3306，并尝试转换为整数
        port_value = int(db_config.get('PORT', 3306))
    except ValueError:
        # 如果转换失败（例如配置为 'abc'），则回退到标准端口
        port_value = 3306

    # 🌟 关键修正：构造一个全新的字典，只包含 PyMySQL 接受的键 🌟
    pymysql_config = {
        # 键值对映射：key: db_config.get(DJANGO_KEY, DEFAULT_VALUE)
        'host': db_config.get('HOST', '127.0.0.1'),
        'user': db_config.get('USER', 'root'),
        'password': db_config.get('PASSWORD'),
        # Django 的 NAME 对应 pymysql 的 db
        'db': db_config.get('NAME'),
        'port': port_value,

        # 保持其他 pymysql 特有配置
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        # ⚠️ 注意：这里我们移除了所有非 PyMySQL 接受的键，如 'ENGINE', 'OPTIONS', 'TEST' 等
    }

    conn = None
    try:
        conn = pymysql.connect(**pymysql_config)
        cursor = conn.cursor()

        print(f"Found {len(products_list)} items to import...")

        for item in products_list:
            source_id = item.get('id', 'N/A')
            try:
                print(f"Importing product {source_id} ...")

                download_images_flag = getattr(settings, 'IMAGE_DOWNLOAD_FLAG', False)

                if download_images_flag:
                    print("🟢 配置：启用图片下载和 Zipline 上传服务。")
                else:
                    print("⚪ 配置：禁用图片下载，仅保留原始 URL。")

                # 核心导入逻辑
                product_id = core.insert_product(cursor, item)

                # 导入关联数据 (如果 core 中定义了这些函数)
                core.insert_images(cursor, product_id, item, download_images_flag)
                core.insert_videos(cursor, product_id, item)
                core.insert_reviews(cursor, product_id, item, download_images_flag)
                core.insert_variations(cursor, product_id, item, download_images_flag)

            except Exception as e:
                print(f"❌ ERROR on item {source_id}: {e}")
                conn.rollback()  # 出现错误时回滚事务
            else:
                conn.commit()  # 成功时提交事务
                print(f"✔ Imported product {source_id}")

    except Exception as e:
        print(f"致命错误：无法连接到数据库或发生未捕获的异常: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


# -------------------------------------------------------------
# 供 products/tasks.py 调用的入口函数
# -------------------------------------------------------------

def start_import_process(products_list):
    """
    这是 tasks.py 中 poll_bright_data_result 调用的实际入口。
    """
    import_products_from_list(products_list)