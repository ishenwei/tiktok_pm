# products/utils.py

import json
import os
from django.conf import settings


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
        return f"<p style='color:red;'>数据格式错误: 必须是JSON字符串或列表。</p>"

    html_content = []

    for item in data:
        item_type = item.get('type')

        if item_type == 'image':
            # 找到 URL 列表中第一个 URL
            url_list = item.get('image', {}).get('url_list', [])
            image_url = url_list[0] if url_list else ""
            if image_url:
                # 注意：这里直接使用图片 URL，可能需要配置 CORS 或 CDN
                html_content.append(
                    f'<img src="{image_url}" style="max-width:100%; height:auto; display:block; margin: 10px auto;" loading="lazy">')

        elif item_type == 'text':
            text_content = item.get('text', '')
            # 使用 <p> 标签包裹文本
            html_content.append(f'<p style="font-size:14px; line-height:1.6;">{text_content}</p>')

        elif item_type == 'ul':
            list_items = item.get('content', [])
            # 使用 <ul> 标签包裹无序列表
            list_html = "<ul>" + "".join([f"<li>{li}</li>" for li in list_items]) + "</ul>"
            html_content.append(list_html)

    return '\n'.join(html_content)


def save_html_file(source_id, html_content):
    """
        将 HTML 内容保存到 MEDIA_ROOT/html 文件夹。
        返回相对于 MEDIA_ROOT 的相对路径。
        """
    # HTML_SUBDIR 是相对于 MEDIA_ROOT 的子目录
    HTML_SUBDIR = 'html'

    # 构造完整的保存目录：MEDIA_ROOT/html/
    save_dir = os.path.join(settings.MEDIA_ROOT, HTML_SUBDIR)
    os.makedirs(save_dir, exist_ok=True)

    filename = f'{source_id}.html'
    filepath = os.path.join(save_dir, filename)

    # 将内容写入文件
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
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
        media_prefix = settings.MEDIA_URL.strip('/')

        return os.path.join(media_prefix, HTML_SUBDIR, filename)
    except Exception as e:
        print(f"写入文件失败: {e}")
        return None