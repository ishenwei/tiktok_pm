#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.db_tools.base import DatabaseInfoTool


def check_local_database():
    """检查本地数据库连接"""
    print("=" * 80)
    print("检查本地数据库连接")
    print("=" * 80)
    
    try:
        DatabaseInfoTool.print_database_info(use_remote=False)
        print("\n✓ 本地数据库连接成功")
        return True
    except Exception as e:
        print(f"\n✗ 本地数据库连接失败: {e}")
        return False


def check_remote_database():
    """检查远程数据库连接"""
    print("\n" + "=" * 80)
    print("检查远程数据库连接")
    print("=" * 80)
    
    try:
        DatabaseInfoTool.print_database_info(use_remote=True)
        print("\n✓ 远程数据库连接成功")
        return True
    except Exception as e:
        print(f"\n✗ 远程数据库连接失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='检查数据库连接')
    parser.add_argument('--remote', action='store_true', help='检查远程数据库')
    parser.add_argument('--local', action='store_true', help='检查本地数据库')
    parser.add_argument('--all', action='store_true', help='检查所有数据库')
    
    args = parser.parse_args()
    
    if args.all or (not args.local and not args.remote):
        check_local_database()
        check_remote_database()
    elif args.local:
        check_local_database()
    elif args.remote:
        check_remote_database()


if __name__ == '__main__':
    main()
