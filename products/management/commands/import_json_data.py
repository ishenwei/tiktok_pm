import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path

# 🌟 关键修改：将导入路径改为新的 ORM 服务层 🌟
# 旧: from products.importer_wrapper import import_products_from_list
# 新:
from products.services.product_importer import import_products_from_list


class Command(BaseCommand):
    # 命令行中使用的名称：python manage.py import_json_data
    help = 'Imports product data from JSON files located in the MEDIA_ROOT/temp_json directory and moves them to MEDIA_ROOT/json upon success.'

    def handle(self, *args, **options):
        # 定义源目录和目标目录
        source_subdir = 'temp_json'
        target_subdir = 'json'

        # 确保路径拼接正确
        json_dir = Path(settings.MEDIA_ROOT) / source_subdir
        target_dir = Path(settings.MEDIA_ROOT) / target_subdir

        # 1. 检查源目录是否存在
        if not json_dir.exists():
            # 这里的提示稍微友好一点，如果目录不存在，可以提示用户创建或放入文件
            self.stdout.write(self.style.WARNING(f'Directory {json_dir} not found. Creating it...'))
            json_dir.mkdir(parents=True, exist_ok=True)
            self.stdout.write(
                self.style.NOTICE(f'Please put your JSON files into {json_dir} and run this command again.'))
            return

        # 2. 确保目标目录存在，如果不存在则创建
        target_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(self.style.NOTICE(f'Scanning directory: {json_dir}'))
        self.stdout.write(self.style.NOTICE(f'Target directory for completed files: {target_dir}'))

        success_count = 0
        failure_count = 0

        files = [f for f in os.listdir(json_dir) if f.endswith('.json')]

        if not files:
            self.stdout.write(self.style.WARNING("No JSON files found."))
            return

        # 3. 遍历目录中的所有 JSON 文件
        for filename in files:
            file_path = json_dir / filename
            self.stdout.write(f'Processing file: {filename} ...')

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 检查 JSON 数据结构，确保是列表
                if isinstance(data, dict):
                    # 如果 JSON 根节点是字典（单个产品），包裹成列表
                    data = [data]
                elif not isinstance(data, list):
                    raise ValueError("JSON content must be a list or a dict")

                # 调用新的 ORM 导入函数
                import_products_from_list(data)

                # ----------------------------------------------------
                # 文件移动逻辑
                # ----------------------------------------------------
                target_file_path = target_dir / filename

                # 如果目标目录已有同名文件，先删除目标文件（覆盖逻辑），防止 Windows 下报错
                if target_file_path.exists():
                    os.remove(target_file_path)

                os.rename(file_path, target_file_path)

                self.stdout.write(
                    self.style.SUCCESS(f'✔ Successfully imported and moved {filename}'))
                success_count += 1

            except json.JSONDecodeError:
                self.stderr.write(self.style.ERROR(f'❌ Failed to decode JSON from {filename}. Skipping.'))
                failure_count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'❌ Error importing {filename}: {e}'))
                # 如果导入失败，文件保留在 temp_json 目录
                failure_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n--- Import Finished ---'))
        self.stdout.write(f'Total files processed: {success_count + failure_count}')
        self.stdout.write(self.style.SUCCESS(f'Successful: {success_count}'))
        self.stdout.write(self.style.ERROR(f'Failed (kept in source): {failure_count}'))