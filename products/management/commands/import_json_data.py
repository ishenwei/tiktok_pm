import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path

# 假设您的导入逻辑在 products/importer_wrapper.py 文件中
# 我们需要确保能正确导入它。
from products.importer_wrapper import import_products_from_list


class Command(BaseCommand):
    # 命令行中使用的名称：python manage.py import_json_data
    help = 'Imports product data from JSON files located in the MEDIA_ROOT/temp_json directory and moves them to MEDIA_ROOT/json upon success.'

    def handle(self, *args, **options):
        # 定义源目录和目标目录
        source_subdir = 'temp_json'
        target_subdir = 'json'

        json_dir = Path(settings.MEDIA_ROOT) / source_subdir
        target_dir = Path(settings.MEDIA_ROOT) / target_subdir

        # 1. 检查源目录是否存在
        if not json_dir.exists():
            raise CommandError(f'JSON source directory does not exist: {json_dir}')

        # 2. 确保目标目录存在，如果不存在则创建
        target_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(self.style.NOTICE(f'Scanning directory: {json_dir}'))
        self.stdout.write(self.style.NOTICE(f'Target directory for completed files: {target_dir}'))

        success_count = 0
        failure_count = 0

        # 3. 遍历目录中的所有 JSON 文件
        for filename in os.listdir(json_dir):
            if filename.endswith('.json'):
                file_path = json_dir / filename
                self.stdout.write(f'Processing file: {filename}')

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 检查 JSON 数据结构
                    if not isinstance(data, list):
                        data = [data]

                    # 调用导入函数
                    import_products_from_list(data)

                    # ----------------------------------------------------
                    # 🌟 关键步骤：文件移动 🌟
                    # ----------------------------------------------------
                    target_file_path = target_dir / filename

                    # 使用 os.rename (或 shutil.move) 将文件移动到目标目录
                    # os.rename 可以用于跨目录的文件移动
                    os.rename(file_path, target_file_path)

                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully imported and moved {filename} to {target_subdir}/'))
                    success_count += 1

                except json.JSONDecodeError:
                    self.stderr.write(self.style.ERROR(f'Failed to decode JSON from {filename}. Skipping.'))
                    failure_count += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error importing {filename}: {e}'))
                    # 如果导入失败，文件保留在 temp_json 目录
                    failure_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n--- Import Finished ---'
        ))
        self.stdout.write(f'Total files processed: {success_count + failure_count}')
        self.stdout.write(self.style.SUCCESS(f'Successful imports and moves: {success_count}'))
        self.stdout.write(self.style.ERROR(f'Failed imports (files kept in source): {failure_count}'))