#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path


def run_command(cmd, cwd=None, capture_output=True):
    """运行命令"""
    print(f"执行命令: {' '.join(cmd)}")
    print("-" * 80)
    
    result = subprocess.run(
        cmd, 
        cwd=cwd or Path(__file__).parent.parent,
        capture_output=capture_output,
        text=True
    )
    
    if capture_output:
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
    
    return result


def clean_local_database():
    """清理本地数据库"""
    print("\n" + "=" * 80)
    print("步骤 1: 清理本地数据库")
    print("=" * 80)
    
    cmd = ['sudo', 'docker', 'exec', 'tiktok_pm_web', 
           'python3', 'scripts/db_tools/clean_database.py', 
           '--all', '--no-confirm']
    
    result = run_command(cmd)
    
    if result.returncode != 0:
        print("\n✗ 数据库清理失败")
        return False
    
    print("\n✓ 数据库清理成功")
    return True


def verify_clean():
    """验证清理结果"""
    print("\n" + "=" * 80)
    print("步骤 2: 验证清理结果")
    print("=" * 80)
    
    cmd = ['sudo', 'docker', 'exec', 'tiktok_pm_web', 
           'python3', 'scripts/db_tools/clean_database.py', 
           '--verify']
    
    result = run_command(cmd)
    
    if result.returncode != 0:
        print("\n✗ 验证失败")
        return False
    
    print("\n✓ 验证通过")
    return True


def run_full_sync():
    """执行完整同步"""
    print("\n" + "=" * 80)
    print("步骤 3: 执行完整数据同步")
    print("=" * 80)
    
    cmd = ['sudo', 'docker', 'exec', 'tiktok_pm_web', 
           'python3', 'manage.py', 'sync_db', 
           '--type', 'FULL']
    
    result = run_command(cmd)
    
    if result.returncode != 0:
        print("\n✗ 数据同步失败")
        return False
    
    print("\n✓ 数据同步成功")
    return True


def verify_sync():
    """验证同步结果"""
    print("\n" + "=" * 80)
    print("步骤 4: 验证同步结果")
    print("=" * 80)
    
    cmd = ['sudo', 'docker', 'exec', 'tiktok_pm_web', 
           'python3', 'scripts/sync_tools/config_manager.py', 
           '--show-counts']
    
    result = run_command(cmd)
    
    if result.returncode != 0:
        print("\n✗ 验证失败")
        return False
    
    print("\n✓ 验证通过")
    return True


def run_tests():
    """运行测试"""
    print("\n" + "=" * 80)
    print("步骤 5: 运行测试套件")
    print("=" * 80)
    
    cmd = ['sudo', 'docker', 'exec', 'tiktok_pm_web', 
           'python3', 'scripts/test_tools/run_tests.py', 
           '--type', 'all', '--verbose']
    
    result = run_command(cmd)
    
    if result.returncode != 0:
        print("\n✗ 测试失败")
        return False
    
    print("\n✓ 所有测试通过")
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='执行完整的数据库清理和同步流程')
    parser.add_argument('--skip-clean', action='store_true', help='跳过数据库清理')
    parser.add_argument('--skip-sync', action='store_true', help='跳过数据同步')
    parser.add_argument('--skip-tests', action='store_true', help='跳过测试')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("执行完整的数据库清理和同步流程")
    print("=" * 80)
    
    steps = []
    
    if not args.skip_clean:
        steps.append(('清理本地数据库', clean_local_database))
        steps.append(('验证清理结果', verify_clean))
    
    if not args.skip_sync:
        steps.append(('执行完整同步', run_full_sync))
        steps.append(('验证同步结果', verify_sync))
    
    if not args.skip_tests:
        steps.append(('运行测试套件', run_tests))
    
    results = {}
    for step_name, step_func in steps:
        results[step_name] = step_func()
        
        if not results[step_name]:
            print(f"\n✗ {step_name} 失败，终止流程")
            break
    
    print("\n" + "=" * 80)
    print("执行结果汇总")
    print("=" * 80)
    
    for step_name, success in results.items():
        status = "✓ 成功" if success else "✗ 失败"
        print(f"{step_name:20s}: {status}")
    
    all_success = all(results.values())
    
    print("\n" + "=" * 80)
    if all_success:
        print("✓ 所有步骤执行成功")
    else:
        print("✗ 部分步骤执行失败")
    print("=" * 80)
    
    return 0 if all_success else 1


if __name__ == '__main__':
    sys.exit(main())
