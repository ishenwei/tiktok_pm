#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.db_tools.base import SyncConfigTool


def show_sync_config():
    """显示同步配置"""
    print("=" * 80)
    print("数据库同步配置")
    print("=" * 80)
    SyncConfigTool.print_sync_config()


def show_table_structure(table_name, use_remote=False):
    """显示表结构"""
    print("=" * 80)
    print(f"表结构: {table_name}")
    print("=" * 80)
    SyncConfigTool.print_table_structure(table_name, use_remote=use_remote)


def compare_table_structure(table_name):
    """比较本地和远程表结构"""
    print("=" * 80)
    print(f"比较表结构: {table_name}")
    print("=" * 80)
    
    print("\n本地表结构:")
    SyncConfigTool.print_table_structure(table_name, use_remote=False)
    
    print("\n远程表结构:")
    SyncConfigTool.print_table_structure(table_name, use_remote=True)
    
    print("\n比较结果:")
    local_structure = SyncConfigTool.get_table_structure(table_name, use_remote=False)
    remote_structure = SyncConfigTool.get_table_structure(table_name, use_remote=True)
    
    if len(local_structure) != len(remote_structure):
        print(f"✗ 字段数量不一致: 本地 {len(local_structure)}, 远程 {len(remote_structure)}")
        return False
    
    all_match = True
    for local_col, remote_col in zip(local_structure, remote_structure):
        if local_col[1] != remote_col[1]:
            print(f"✗ 字段 {local_col[0]} 类型不一致: 本地 {local_col[1]}, 远程 {remote_col[1]}")
            all_match = False
    
    if all_match:
        print("✓ 所有字段类型一致")
    return all_match


def show_table_counts():
    """显示所有表的行数"""
    print("=" * 80)
    print("数据库表行数统计")
    print("=" * 80)
    
    config = SyncConfigTool.get_sync_config()
    print(f"{'表名':30s} | {'本地行数':10s} | {'远程行数':10s} | {'状态':10s}")
    print("-" * 80)
    
    for row in config:
        table_name = row[1]
        local_count = SyncConfigTool.get_row_count(table_name, use_remote=False)
        remote_count = SyncConfigTool.get_row_count(table_name, use_remote=True)
        
        if local_count == remote_count:
            status = "✓ 一致"
        else:
            status = f"✗ 差异: {abs(local_count - remote_count)}"
        
        print(f"{table_name:30s} | {local_count:10d} | {remote_count:10d} | {status}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='同步配置工具')
    parser.add_argument('--show-config', action='store_true', help='显示同步配置')
    parser.add_argument('--table-structure', type=str, help='显示指定表结构')
    parser.add_argument('--compare-structure', type=str, help='比较本地和远程表结构')
    parser.add_argument('--show-counts', action='store_true', help='显示所有表行数')
    
    args = parser.parse_args()
    
    if args.show_config:
        show_sync_config()
    elif args.table_structure:
        show_table_structure(args.table_structure)
    elif args.compare_structure:
        compare_table_structure(args.compare_structure)
    elif args.show_counts:
        show_table_counts()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
