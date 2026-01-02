# products/utils.py

import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


def json_to_html(json_data):
    """
    将产品描述 JSON 结构转换成 HTML 字符串。
    """
    if not json_data:
        return ""

    # 如果 desc_detail 已经是字符串，需要先解析
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return f"<p style='color:red;'>JSON 解析错误: {json_data}</p>"
    elif isinstance(json_data, list):
        data = json_data
    else:
        return "<p style='color:red;'>数据格式错误: 必须是JSON字符串或列表。</p>"

    html_content = []

    for item in data:
        item_type = item.get("type")

        if item_type == "image":
            # 找到 URL 列表中第一个 URL
            url_list = item.get("image", {}).get("url_list", [])
            image_url = url_list[0] if url_list else ""
            if image_url:
                # 注意：这里直接使用图片 URL，可能需要配置 CORS 或 CDN
                html_content.append(
                    f'<img src="{image_url}" style="max-width:100%; height:auto; display:block; margin: 10px auto;" loading="lazy">'
                )

        elif item_type == "text":
            text_content = item.get("text", "")
            # 使用 <p> 标签包裹文本
            html_content.append(f'<p style="font-size:14px; line-height:1.6;">{text_content}</p>')

        elif item_type == "ul":
            list_items = item.get("content", [])
            # 使用 <ul> 标签包裹无序列表
            list_html = "<ul>" + "".join([f"<li>{li}</li>" for li in list_items]) + "</ul>"
            html_content.append(list_html)

    return "\n".join(html_content)


def save_html_file(source_id, html_content):
    """
    将 HTML 内容保存到 MEDIA_ROOT/html 文件夹。
    返回相对于 MEDIA_ROOT 的相对路径。
    """
    # HTML_SUBDIR 是相对于 MEDIA_ROOT 的子目录
    HTML_SUBDIR = "html"

    # 构造完整的保存目录：MEDIA_ROOT/html/
    save_dir = os.path.join(settings.MEDIA_ROOT, HTML_SUBDIR)
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{source_id}.html"
    filepath = os.path.join(save_dir, filename)

    # 将内容写入文件
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            # 写入完整的 HTML 结构以便浏览器正确渲染
            full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>产品描述 - {source_id}</title>
    <meta charset="UTF-8">
</head>
<body>
{html_content}
</body>
</html>
"""
            f.write(full_html)

        # 🌟 关键：返回相对于 MEDIA_ROOT 的相对路径 🌟
        media_prefix = settings.MEDIA_URL.strip("/")

        return os.path.join(media_prefix, HTML_SUBDIR, filename)
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        return None


# products/utils.py

import json

from django.utils.safestring import mark_safe

# ... (保留你原有的 save_html_file 等函数) ...


def format_json_to_html(data_input):
    """
    通用工具：将 JSON 数据格式化为 HTML 字符串。
    支持格式：
    1. List of Dicts (TikTok Style): [{"name": "Color", "value": "Red"}, ...]
    2. Simple Dict: {"Color": "Red", "Size": "XL"}

    效果：
    Key: Value (不换行)
    Key: Value (不换行)
    """
    if not data_input:
        return "-"

    data = data_input

    # 1. 如果是字符串，尝试解析为 JSON 对象
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            # 解析失败，直接返回原字符串
            return data_input

    lines = []

    # 2. 处理 List 类型 (例如: [{"name": "Color", "value": "Red"}])
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # 优先尝试获取 TikTok 标准的 name/value 键
                k = item.get("name") or item.get("key")
                v = item.get("value") or item.get("val")

                if k is not None and v is not None:
                    lines.append(f"{k}: {v}")
                else:
                    # 如果不是 name/value 结构，则把字典里的每一对都打出来
                    for sub_k, sub_v in item.items():
                        lines.append(f"{sub_k}: {sub_v}")
            else:
                # 列表里是纯字符串等
                lines.append(str(item))

    # 3. 处理 Dict 类型 (例如: {"Color": "Red", "Weight": "1kg"})
    elif isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"{k}: {v}")

    # 4. 其他类型直接转字符串
    else:
        lines.append(str(data))

    # 5. HTML 渲染：包裹 span 防止文字换行，用 <br> 连接各行
    if not lines:
        return "-"

    formatted_html = []
    for line in lines:
        # white-space: nowrap 保证单行内容不折行
        # display: inline-block 保证结构完整
        span = f'<span style="white-space: nowrap; display: inline-block; margin-right: 5px;">{line}</span>'
        formatted_html.append(span)

    return mark_safe("<br>".join(formatted_html))
