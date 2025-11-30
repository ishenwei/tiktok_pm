# products/importer_core.py
import json
from datetime import datetime
import requests
import mimetypes
from django.conf import settings  # 导入 settings 以获取配置
from products.utils import save_html_file
from products.utils import json_to_html
from urllib.parse import urlparse
from products.models import Store

# -----------------------------
# Helper Functions
# -----------------------------

def safe_get(d, key, default=None):
    """Safely extract key from dict"""
    return d.get(key, default)


def json_or_none(value):
    return json.dumps(value, ensure_ascii=False) if value is not None else None


def parse_datetime(value):
    """Convert ISO8601 timestamp to MySQL DATETIME format."""
    # (保持您原脚本中的解析逻辑不变)
    if not value:
        return None

    try:
        if value.endswith("Z"):
            value = value[:-1]

        if "." in value:
            dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

        return dt.strftime("%Y-%m-%d %H:%M:%S")

    except Exception:
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            print(f"Warning: Invalid timestamp format: {value}")
            return None


# -----------------------------------------
# Media Upload Helpers
# -----------------------------------------
def guess_mime(filename):
    # (保持您原脚本中的 guess_mime 逻辑不变)
    mime, _ = mimetypes.guess_type(filename)
    if mime:
        return mime
    # 简化版，用于演示
    ext = filename.lower().split(".")[-1]
    return {
        "jpg": "image/jpeg",
        "png": "image/png",
        "mp4": "video/mp4",
    }.get(ext, "application/octet-stream")


def upload_to_zipline(file_bytes, filename):
    """上传文件到 Zipline."""

    upload_url = settings.ZIPLINE_UPLOAD_URL
    api_key = settings.ZIPLINE_API_KEY

    if not upload_url or not api_key:
        print("❌ Zipline config missing. Skipping upload.")
        return None

    mime_type = guess_mime(filename)
    files = {"file": (filename, file_bytes, mime_type)}
    headers = {"Authorization": api_key}

    try:
        resp = requests.post(upload_url, headers=headers, files=files)
        resp.raise_for_status()
        data = resp.json()

        # (保持您原脚本中的 URL 提取逻辑不变)
        for key in ("url", "cdn_url", "file_url"):
            if key in data:
                return data[key]

        if isinstance(data, dict) and "files" in data and len(data["files"]) > 0:
            return data["files"][0].get("url")

        print("❌ No URL field found in Zipline response.")
        return None

    except Exception as e:
        print(f"❌ Zipline upload failed: {e}")
        return None


def download_media(url):
    """下载远程媒体文件."""
    try:
        resp = requests.get(url, stream=True, timeout=30)
        if resp.status_code != 200:
            print(f"  ❌ Download fail (Status: {resp.status_code})")
            return None, None

        img_bytes = resp.content
        ext = url.split("?")[0].split(".")[-1].lower()
        filename = f"tmp.{ext}"

        return img_bytes, filename
    except Exception as e:
        print(f"  ❌ Download error: {e}")
        return None, None


# -----------------------------
# Insert Functions (核心 SQL 逻辑)
# -----------------------------

def insert_product(cursor, item):
    # (保持您原脚本中的 insert_product 逻辑不变)
    # ... 您的 SQL 和参数字典 ...
    store_obj = insert_store(cursor, item)
    store_id_value = store_obj.id if store_obj else None
    print(store_id_value)

    desc_detail = safe_get(item, "desc_detail")
    id = safe_get(item, "id")
    desc_html_path = ""

    print(" → → → Start to generate description html")

    if desc_detail and id:
        print(" → → → Generate description html")
        html_content = json_to_html(desc_detail)
        # 使用 source_id 作为文件名
        desc_html_path = save_html_file(id, html_content)
        print(" → → → Generated description html"+ desc_html_path)

    sql = """
          INSERT INTO products (source_id, url, title, description, desc_detail, desc_html_path, \
                                available, In_stock, currency, initial_price, final_price, \
                                discount_percent, initial_price_low, initial_price_high, \
                                final_price_low, final_price_high, sold, position, \
                                colors, sizes, shipping_fee, specifications, \
                                videos, related_videos, video_link, category, category_url, \
                                seller_id, store_id, prodct_rating, promotion_items, \
                                shop_performance_metrics, timestamp, input, raw_json)
          VALUES (%(source_id)s, %(url)s, %(title)s, %(description)s, %(desc_detail)s, %(desc_html_path)s, \
                  %(available)s, %(In_stock)s, %(currency)s, %(initial_price)s, %(final_price)s, \
                  %(discount_percent)s, %(initial_price_low)s, %(initial_price_high)s, \
                  %(final_price_low)s, %(final_price_high)s, %(sold)s, %(position)s, \
                  %(colors)s, %(sizes)s, %(shipping_fee)s, %(specifications)s, \
                  %(videos)s, %(related_videos)s, %(video_link)s, %(category)s, %(category_url)s, \
                  %(seller_id)s, %(store_id)s, %(prodct_rating)s, %(promotion_items)s, \
                  %(shop_performance_metrics)s, %(timestamp)s, %(input)s, %(raw_json)s); \
          """

    cursor.execute(sql, {
        "source_id": safe_get(item, "id"),
        "url": safe_get(item, "url"),
        "title": safe_get(item, "title"),
        "description": safe_get(item, "description"),
        "desc_detail": safe_get(item, "desc_detail"),
        "desc_html_path": desc_html_path,
        "available": 1 if safe_get(item, "available") else 0,
        "In_stock": 1 if safe_get(item, "In_stock") else 0,
        "currency": safe_get(item, "currency"),
        "initial_price": safe_get(item, "initial_price"),
        "final_price": safe_get(item, "final_price"),
        "discount_percent": safe_get(item, "discount_percent"),
        "initial_price_low": safe_get(item, "initial_price_low"),
        "initial_price_high": safe_get(item, "initial_price_high"),
        "final_price_low": safe_get(item, "final_price_low"),
        "final_price_high": safe_get(item, "final_price_high"),
        "sold": safe_get(item, "sold"),
        "position": safe_get(item, "position"),
        "colors": json_or_none(safe_get(item, "colors")),
        "sizes": json_or_none(safe_get(item, "sizes")),
        "shipping_fee": json_or_none(safe_get(item, "shipping_fee")),
        "specifications": json_or_none(safe_get(item, "specifications")),
        "videos": json_or_none(safe_get(item, "videos")),
        "related_videos": json_or_none(safe_get(item, "related_videos")),
        "video_link": safe_get(item, "video_link"),
        "category": safe_get(item, "category"),
        "category_url": safe_get(item, "category_url"),
        "seller_id": safe_get(item, "seller_id"),
        "store_id": store_id_value,
        "prodct_rating": json_or_none(safe_get(item, "prodct_rating")),
        "promotion_items": json_or_none(safe_get(item, "promotion_items")),
        "shop_performance_metrics": json_or_none(safe_get(item, "Shop_performance_metrics")),
        "timestamp": parse_datetime(safe_get(item, "timestamp")),
        "input": json_or_none(safe_get(item, "input")),
        "raw_json": json_or_none(item),
        # 移除 description_1/2 和 desc_detail_1/2 字段，因为原脚本中它们是 None
    })

    return cursor.lastrowid


# (其余的 insert_images, insert_videos, insert_variations, insert_reviews 函数保持原脚本逻辑，
# 确保它们使用 download_media 和 upload_to_zipline)
# ... 请将 insert_images 等函数逻辑复制到此处 ...
# ... (为节省篇幅，省略了这些重复的 SQL 函数)
# ...

def insert_images(cursor, product_id, item, download_images_flag):
    images = safe_get(item, "images") or []
    for idx, img in enumerate(images):

        original_url = img
        zipline_url = ""
        if download_images_flag:
            img_bytes, filename = download_media(original_url)

            if img_bytes is None:
                print("  ❌ Skip due to download failure")
            else:
                zipline_url = upload_to_zipline(img_bytes, filename)
                print(" → → → Replacement URL:", zipline_url)

        image_type = "product"
        cursor.execute("""
            INSERT INTO product_images (
                product_id, image_type, original_url, zipline_url
            ) VALUES (%s, %s, %s, %s);
        """, (
            product_id,
            image_type,
            original_url,
            zipline_url,
        ))


def insert_videos(cursor, product_id, item):
    videos = safe_get(item, "videos") or []
    for vid in videos:

        original_url = vid
        zipline_url = ""
        vid_bytes, filename = download_media(original_url)

        if vid_bytes is None:
            print("  ❌ Skip due to download failure")
        else:
            zipline_url = upload_to_zipline(vid_bytes, filename)
            print(" → → → Replacement URL:", zipline_url)

        video_type= "product"

        cursor.execute("""
            INSERT INTO product_videos (
                product_id, video_type, original_url, zipline_url
            ) VALUES (%s, %s, %s, %s);
        """, (
            product_id,
            video_type,
            original_url,
            zipline_url
        ))


def insert_variations(cursor, product_id, item, download_images_flag):
    variations = safe_get(item, "variations") or []

    for var in variations:
        original_url = var.get("image")
        zipline_url = ""
        print(" → → → Original URL:", original_url)

        if download_images_flag:
            img_bytes, filename = download_media(original_url)

            if img_bytes is None:
                print("  ❌ Skip due to download failure")
            else:
                zipline_url = upload_to_zipline(img_bytes, filename)
                print(" → → → Replacement URL:", zipline_url)

        cursor.execute("""
            INSERT INTO product_variations (
                product_id, sku, sku_sales_props, stock, purchase_limit,
                initial_price, final_price, currency, discount_percent, 
                image_original_url, image_zipline_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            product_id,
            var.get("sku"),
            json_or_none(var.get("sku_sales_props")),
            var.get("stock"),
            var.get("purchase_limit"),
            var.get("initial_price"),
            var.get("final_price"),
            var.get("currency"),
            var.get("discount_percent"),
            original_url,
            zipline_url,
        ))


def insert_reviews(cursor, product_id, item, download_images_flag):
    reviews = item.get("reviews") or []

    for r in reviews:
        reviewer_name = r.get("name")
        rating = int(r.get("rating", 0))
        review_text = r.get("review")
        review_date = r.get("date")
        if review_date:
            # 转为 MySQL DATETIME 格式
            review_date = datetime.fromisoformat(review_date.replace("Z", "+00:00"))
        images = r.get("images") or []
        zipline_image_urls = []

        if download_images_flag:
            for idx, img in enumerate(images):
                original_url = img
                img_bytes, filename = download_media(original_url)

                if img_bytes is None:
                    print("  ❌ Skip due to download failure")
                else:
                    zipline_url = upload_to_zipline(img_bytes, filename)
                    print(" → → → Replacement URL:", zipline_url)
                    zipline_image_urls.append(zipline_url)

        images_json = json.dumps(images) if images else None
        zipline_image_json = json.dumps(zipline_image_urls) if zipline_image_urls else None

        cursor.execute("""
            INSERT INTO product_reviews (
                product_id, reviewer_name, rating, review_text, review_date, images, zipline_images
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            product_id,
            reviewer_name,
            rating,
            review_text,
            review_date,
            images_json,
            zipline_image_json,
        ))

def insert_store(cursor, item):
    """创建或获取店铺记录，返回 Store ORM 对象"""

    details = item.get("store_details") or {}
    store_url = details.get("url")
    store_name = details.get("name")
    rating = details.get("rating")
    num_of_items = details.get("num_of_items")
    num_sold = details.get("num_sold")
    followers = details.get("followers")
    badge = details.get("badge")

    store_id = extract_last_segment(store_url)

    if not store_id:
        print("❌ Store URL invalid, skip store creation")
        return None

    store, created = Store.objects.update_or_create(
        store_id=store_id,
        defaults={
            "name": store_name,
            "url": store_url,
            "rating": rating,
            "num_of_items": num_of_items,
            "num_sold": num_sold,
            "followers": followers,
            "badge": badge,
        }
    )

    if created:
        print(f"✅ Created new store: {store_id} ({store_name})")
    else:
        print(f"✔️ Store exists: {store_id}")

    return store


def extract_last_segment(url: str) -> str:
    """
    从 TikTok 店铺 URL 中提取最后一个路径字段。
    例如：
      https://www.tiktok.com/shop/store/kuangcao-shop/7494162489761105528
    返回：
      7494162489761105528
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")        # 去掉左右两边的 "/"
    segments = path.split("/")           # 按路径层级分割
    return segments[-1] if segments else None