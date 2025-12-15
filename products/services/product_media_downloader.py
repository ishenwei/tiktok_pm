import os
import re
import requests
from urllib.parse import urlparse
from django.conf import settings
from pathlib import Path
from typing import Dict, Any, Set, List  # 导入类型提示

# 用于匹配图片扩展名的正则表达式
IMG_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp|gif)", re.I)
# Windows 非法字符
ILLEGAL_CHARS = r'[<>:"/\\|?*]'


def _safe_filename(url: str) -> str:
    """从 URL 中提取安全的文件名部分，移除查询参数"""
    parsed = urlparse(url)
    name = os.path.basename(parsed.path)
    return name.split("?")[0] or "image.jpg"


# ----------------------------------------------------------------------
# 辅助函数：核心下载逻辑 (已修复路径拼接)
# ----------------------------------------------------------------------
def _download(url: str, save_directory: str, filename: str):
    """
    下载文件到指定的目录和文件名。
    """
    if not url:
        return

    # 构造完整的目标路径
    target_path = Path(save_directory) / filename
    target_path_str = str(target_path)

    os.makedirs(os.path.dirname(target_path_str), exist_ok=True)

    if os.path.exists(target_path_str):
        return  # 避免重复下载

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    with open(target_path_str, "wb") as f:
        f.write(resp.content)


# ----------------------------------------------------------------------
# 辅助函数：从嵌套结构中提取图片 URL
# ----------------------------------------------------------------------
def extract_images_from_desc_detail(desc_detail: Dict[str, Any]) -> Set[str]:
    """
    递归遍历 desc_detail (JSON/Dict) 结构，提取图片 URL。
    """
    urls = set()

    if not desc_detail:
        return urls

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, str):
            # 检查字符串是否匹配图片扩展名
            if IMG_EXT_RE.search(obj):
                urls.add(obj)

    walk(desc_detail)
    return urls


# ----------------------------------------------------------------------
# 核心函数：下载所有产品图片
# ----------------------------------------------------------------------
def download_all_product_images(product) -> (str, Dict[str, int]):
    """
    下载一个产品的所有图片（产品图、SKU图、详情图），并使用 <product_id>_<index> 格式重命名。
    """
    # 确保 product_id 是字符串，用于路径和文件名
    product_id = str(product.source_id)
    store_name = str(product.store.name)

    # 1. 确定保存的基础目录
    #base_save_dir = Path(settings.MEDIA_ROOT) / 'downloaded_media' / product_id
    #base_save_dir.mkdir(parents=True, exist_ok=True)
    base_download_root = settings.PRODUCT_MEDIA_DOWNLOAD_ROOT
    base_save_dir = Path(base_download_root) / store_name / product_id

    # 2. 初始化计数器和汇总数据
    global_image_counter = 1
    summary = {
        'product_images': 0,
        'variation_images': 0,
        'desc_images': 0
    }

    # 用于存放所有需要下载的 URL，按收集顺序排列
    urls_to_download: List[str] = []

    # --- 收集 URL ---

    # A. 收集产品图片 (ProductImage)
    # 使用正确的反向关联名称 'product_images'
    product_images = product.product_images.all().order_by('id')
    product_urls = [img.original_url for img in product_images if img.original_url]
    urls_to_download.extend(product_urls)
    summary['product_images'] = len(product_urls)

    # B. 收集 SKU 图片 (ProductVariation)
    # 使用正确的反向关联名称 'product_variations'
    variation_images = product.product_variations.all().order_by('id')
    variation_urls = [v.image_original_url for v in variation_images if v.image_original_url]
    urls_to_download.extend(variation_urls)
    summary['variation_images'] = len(variation_urls)

    # C. 收集详情图 (Desc Detail Images)
    desc_urls: Set[str] = set()
    if product.desc_detail:
        desc_urls = extract_images_from_desc_detail(product.desc_detail)
        urls_to_download.extend(list(desc_urls))
        summary['desc_images'] = len(desc_urls)

    # 3. 去重并下载

    # 移除重复的 URL，保持收集时的顺序
    unique_urls = list(dict.fromkeys(urls_to_download))

    for url in unique_urls:
        # 1. 构造新的标准化文件名 (保留原始扩展名或使用 .jpeg)
        safe_name = _safe_filename(url)
        ext = os.path.splitext(safe_name)[-1].lower()

        # 如果扩展名无效或缺失，则使用 .jpeg
        if not IMG_EXT_RE.search(ext):
            ext = '.jpeg'

        new_filename = f"{product_id}_{global_image_counter}{ext}"
        current_save_dir = base_save_dir

        try:
            # 2. 调用下载辅助函数
            _download(url, str(current_save_dir), new_filename)

            # 3. 更新计数器
            global_image_counter += 1

        except Exception as e:
            # 打印下载失败信息
            print(f"下载失败 URL: {url}, 错误: {e}")
            # 继续下一个 URL

    return str(base_save_dir), summary


# ----------------------------------------------------------------------
# 辅助函数：清理文件名（已不再用于最终文件名，但保留以防不时之需）
# ----------------------------------------------------------------------

def clean_filename(original_filename):
    """清理文件名中的非法字符 (现在主要通过顺序重命名来避免)"""
    cleaned_name = re.sub(ILLEGAL_CHARS, '_', original_filename)
    return cleaned_name.strip()