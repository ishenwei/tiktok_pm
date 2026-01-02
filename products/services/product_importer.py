import logging
import mimetypes
from datetime import datetime

import requests
from django.conf import settings
from django.db import transaction
from django.utils.timezone import make_aware

# 引入你的模型
from products.models import (
    Product,
    ProductImage,
    ProductReview,
    ProductVariation,
    ProductVideo,
    Store,
)
from products.utils import json_to_html, save_html_file

logger = logging.getLogger(__name__)


# ==========================================
# 1. 媒体处理工具 (保留原逻辑)
# ==========================================


def guess_mime(filename):
    mime, _ = mimetypes.guess_type(filename)
    if mime:
        return mime
    ext = filename.lower().split(".")[-1]
    return {"jpg": "image/jpeg", "png": "image/png", "mp4": "video/mp4"}.get(
        ext, "application/octet-stream"
    )


def download_media(url):
    """下载远程媒体文件，返回二进制内容和文件名"""
    if not url:
        return None, None
    try:
        resp = requests.get(url, stream=True, timeout=30)
        if resp.status_code != 200:
            logger.warning(f"Download fail: {url} (Status: {resp.status_code})")
            return None, None

        # 提取文件名
        filename = url.split("?")[0].split("/")[-1]
        if not filename:
            filename = "temp_file"

        return resp.content, filename
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None, None


def upload_to_zipline(file_bytes, filename):
    """上传到 Zipline 图床"""
    upload_url = getattr(settings, "ZIPLINE_UPLOAD_URL", None)
    api_key = getattr(settings, "ZIPLINE_API_KEY", None)

    if not upload_url or not api_key:
        return None

    mime_type = guess_mime(filename)
    files = {"file": (filename, file_bytes, mime_type)}
    headers = {"Authorization": api_key}

    try:
        resp = requests.post(upload_url, headers=headers, files=files, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # 尝试获取 URL
        if "files" in data and data["files"]:
            return data["files"][0].get("url")
        return data.get("url") or data.get("file_url")
    except Exception as e:
        logger.error(f"Zipline upload failed: {e}")
        return None


def process_media_url(original_url, download_flag):
    """统一处理媒体 URL：如果开启下载则上传到 Zipline，否则返回空字符串"""
    zipline_url = ""
    if download_flag and original_url:
        file_bytes, filename = download_media(original_url)
        if file_bytes:
            zipline_url = upload_to_zipline(file_bytes, filename)
            if zipline_url:
                logger.info(f"Zipline Uploaded: {zipline_url}")
    return zipline_url


# ==========================================
# 2. 数据清洗工具
# ==========================================


def _clean_price(value):
    if value is None or value == "":
        return None
    try:
        if isinstance(value, str):
            cleaned = value.replace("$", "").replace("£", "").replace(",", "").strip()
            return float(cleaned)
        return float(value)
    except (ValueError, TypeError):
        return None


def _clean_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _parse_datetime(value):
    """处理时间字符串"""
    if not value:
        return None
    try:
        # 处理带 Z 的 ISO 格式
        value = value.replace("Z", "")
        if "T" in value:
            dt = datetime.fromisoformat(value)
        else:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

        # 确保是 timezone aware 的时间（Django 推荐）
        return make_aware(dt)
    except Exception:
        return None


# ==========================================
# 3. 核心导入逻辑 (Django ORM 版)
# ==========================================


def import_products_from_list(products_list):
    """
    主入口：接收字典列表，使用 ORM 写入数据库
    """
    logger.info(f"开始导入 {len(products_list)} 个产品 (ORM Mode)...")

    download_flag = getattr(settings, "IMAGE_DOWNLOAD_FLAG", False)

    for item in products_list:
        source_id = item.get("id")
        if not source_id:
            continue

        try:
            # 开启事务原子性：确保一个产品的所有数据（图片、变体）要么全成功，要么全失败
            with transaction.atomic():
                logger.info(f"Processing: {source_id}")

                # --- 1. 处理 Store ---
                store = _handle_store(item)

                # --- 2. 生成 HTML 描述文件 ---
                desc_html_path = ""
                desc_detail = item.get("desc_detail")
                if desc_detail:
                    html_content = json_to_html(desc_detail)
                    desc_html_path = save_html_file(source_id, html_content)

                # --- 3. 处理 Product 本体 ---
                product = _handle_product(item, source_id, store, desc_html_path)

                # --- 4. 处理关联表 (先删除旧的，再插入新的，保持同步) ---

                # A. Images
                product.product_images.all().delete()
                images = item.get("images") or []
                for img_url in images:
                    if not img_url:
                        continue
                    zipline_url = process_media_url(img_url, download_flag)
                    ProductImage.objects.create(
                        product=product,
                        image_type="main",
                        original_url=img_url,
                        zipline_url=zipline_url,
                    )

                # B. Videos
                product.product_videos.all().delete()
                videos = item.get("videos") or []
                for vid_url in videos:
                    if not vid_url:
                        continue
                    zipline_url = process_media_url(vid_url, download_flag)  # 视频也可以尝试上传
                    ProductVideo.objects.create(
                        product=product,
                        video_type="main",
                        original_url=vid_url,
                        zipline_url=zipline_url,
                    )

                # C. Variations (SKUs)
                product.product_variations.all().delete()
                variations = item.get("variations") or []
                for var in variations:
                    var_img_url = var.get("image")
                    var_zipline = process_media_url(var_img_url, download_flag)

                    ProductVariation.objects.create(
                        product=product,
                        sku=var.get("sku"),
                        sku_sales_props=var.get("sku_sales_props"),  # JSON
                        stock=_clean_int(var.get("stock")),
                        purchase_limit=_clean_int(var.get("purchase_limit")),
                        initial_price=_clean_price(var.get("initial_price")),
                        final_price=_clean_price(var.get("final_price")),
                        currency=var.get("currency"),
                        discount_percent=_clean_price(var.get("discount_percent")),
                        image_original_url=var_img_url,
                        image_zipline_url=var_zipline,
                    )

                # D. Reviews
                product.reviews.all().delete()
                reviews = item.get("reviews") or []
                for r in reviews:
                    # 处理评论图片
                    r_images = r.get("images") or []
                    r_zipline_urls = []
                    if download_flag:
                        for r_img in r_images:
                            z_url = process_media_url(r_img, True)  # 强制下载评论图
                            if z_url:
                                r_zipline_urls.append(z_url)

                    ProductReview.objects.create(
                        product=product,
                        reviewer_name=r.get("name"),
                        rating=_clean_int(r.get("rating")),
                        review_text=r.get("review"),
                        review_date=_parse_datetime(r.get("date")),
                        images=r_images,  # JSONField
                        zipline_images=r_zipline_urls,  # JSONField
                    )

                logger.info(f"Success: {source_id}")

        except Exception as e:
            logger.error(f"Error importing {source_id}: {e}")
            # transaction.atomic 会自动回滚


# ==========================================
# 4. 内部 Helper (Models Mapping)
# ==========================================


def _handle_store(item):
    """处理店铺信息"""
    details = item.get("store_details") or {}
    url = details.get("url")
    if not url:
        return None

    # 从 URL 提取 ID
    try:
        store_id = url.strip("/").split("/")[-1]
    except (AttributeError, IndexError):
        return None

    store, _ = Store.objects.update_or_create(
        store_id=store_id,
        defaults={
            "name": details.get("name"),
            "url": url,
            "rating": _clean_price(details.get("rating")),
            "num_of_items": _clean_int(details.get("num_of_items")),
            "num_sold": _clean_int(details.get("num_sold")),
            "followers": _clean_int(details.get("followers")),
            "badge": details.get("badge"),
        },
    )
    return store


def _handle_product(item, source_id, store, desc_html_path):
    """处理产品本体映射"""
    defaults = {
        "store": store,
        "url": item.get("url"),
        "title": item.get("title"),
        "description": item.get("description"),
        "desc_detail": item.get("desc_detail"),  # JSONField
        "desc_html_path": desc_html_path,
        "available": bool(item.get("available")),
        "In_stock": bool(item.get("In_stock")),
        "currency": item.get("currency"),
        "initial_price": _clean_price(item.get("initial_price")),
        "final_price": _clean_price(item.get("final_price")),
        "discount_percent": _clean_price(item.get("discount_percent")),
        "initial_price_low": _clean_price(item.get("initial_price_low")),
        "initial_price_high": _clean_price(item.get("initial_price_high")),
        "final_price_low": _clean_price(item.get("final_price_low")),
        "final_price_high": _clean_price(item.get("final_price_high")),
        "sold": _clean_int(item.get("sold")),
        "position": _clean_int(item.get("position")),
        "colors": item.get("colors"),  # JSON
        "sizes": item.get("sizes"),  # JSON
        "shipping_fee": item.get("shipping_fee"),  # JSON
        "specifications": item.get("specifications"),  # JSON
        "videos": item.get("videos"),  # JSON 原始数据
        "related_videos": item.get("related_videos"),  # JSON
        "video_link": item.get("video_link"),
        "category": item.get("category"),
        "category_url": item.get("category_url"),
        "seller_id": item.get("seller_id"),
        # 注意: 这里使用你修正后的字段名 'product_rating'，而不是 'prodct_rating'
        # 如果数据库还没迁移，请确保 models.py 和数据库一致
        "product_rating": item.get("prodct_rating"),
        "promotion_items": item.get("promotion_items"),
        "shop_performance_metrics": item.get("Shop_performance_metrics"),
        "timestamp": _parse_datetime(item.get("timestamp")),
        "input": item.get("input"),
        "raw_json": item,
    }

    product, created = Product.objects.update_or_create(source_id=source_id, defaults=defaults)
    return product
