#!/usr/bin/env python3
import sys
import subprocess
import argparse
from pathlib import Path


class TestRunner:
    """测试运行器"""
    
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.reports_dir = self.project_root / 'test_reports'
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_command(self, cmd, cwd=None):
        """运行命令"""
        print(f"执行命令: {' '.join(cmd)}")
        print("-" * 80)
        
        result = subprocess.run(cmd, cwd=cwd or self.project_root, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result
    
    def run_db_sync_tests(self, test_type='all', test_name=None, output_dir=None, 
                          report_format='all', monitor=False, auto_fix=False, 
                          verbose=False, timeout=600):
        """运行数据库同步测试"""
        cmd = [
            sys.executable,
            'manage.py',
            'run_db_sync_tests',
            '--test-type', test_type,
            '--output-dir', output_dir or str(self.reports_dir),
            '--report-format', report_format,
            '--timeout', str(timeout)
        ]
        
        if test_name:
            cmd.extend(['--test-name', test_name])
        
        if monitor:
            cmd.append('--monitor')
        
        if auto_fix:
            cmd.append('--auto-fix')
        
        if verbose:
            cmd.append('--verbose')
        
        return self.run_command(cmd)
    
    def run_unit_tests(self, verbose=False):
        """运行单元测试"""
        cmd = [sys.executable, 'manage.py', 'test']
        if verbose:
            cmd.append('--verbosity=2')
        
        return self.run_command(cmd)
    
    def run_integration_tests(self, verbose=False):
        """运行集成测试"""
        cmd = [sys.executable, 'manage.py', 'test', '--tag=integration']
        if verbose:
            cmd.append('--verbosity=2')
        
        return self.run_command(cmd)
    
    def run_all_tests(self, verbose=False):
        """运行所有测试"""
        print("=" * 80)
        print("运行完整测试套件")
        print("=" * 80)
        
        results = {}
        
        print("\n1. 运行单元测试...")
        results['unit'] = self.run_unit_tests(verbose)
        
        print("\n2. 运行集成测试...")
        results['integration'] = self.run_integration_tests(verbose)
        
        print("\n3. 运行数据库同步测试...")
        results['db_sync'] = self.run_db_sync_tests(verbose=verbose)
        
        print("\n" + "=" * 80)
        print("测试结果汇总:")
        print("=" * 80)
        
        for test_type, result in results.items():
            status = "✓ 通过" if result.returncode == 0 else "✗ 失败"
            print(f"{test_type:20s}: {status}")
        
        return all(r.returncode == 0 for r in results.values())


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行测试套件')
    
    parser.add_argument('--type', type=str, 
                        choices=['unit', 'integration', 'db_sync', 'all'],
                        default='all',
                        help='测试类型')
    
    parser.add_argument('--test-name', type=str, help='运行特定的测试用例名称')
    parser.add_argument('--output-dir', type=str, help='测试报告输出目录')
    parser.add_argument('--report-format', type=str, 
                        choices=['html', 'json', 'markdown', 'all'],
                        default='all',
                        help='报告格式')
    parser.add_argument('--monitor', action='store_true', help='启用实时监控')
    parser.add_argument('--auto-fix', action='store_true', help='启用自动修复')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    parser.add_argument('--timeout', type=int, default=600, help='测试超时时间(秒)')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.type == 'unit':
        result = runner.run_unit_tests(args.verbose)
    elif args.type == 'integration':
        result = runner.run_integration_tests(args.verbose)
    elif args.type == 'db_sync':
        result = runner.run_db_sync_tests(
            test_name=args.test_name,
            output_dir=args.output_dir,
            report_format=args.report_format,
            monitor=args.monitor,
            auto_fix=args.auto_fix,
            verbose=args.verbose,
            timeout=args.timeout
        )
    else:
        result = runner.run_all_tests(args.verbose)
    
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
