import os
import sys
import time
import argparse
from datetime import datetime
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from db_sync_tests.test_framework import TestSuite, TestLogger, TestStatus
from db_sync_tests.monitor import RealTimeMonitor, DatabaseMonitor, SyncMonitor, SystemMonitor
from db_sync_tests.troubleshooter import Troubleshooter
from db_sync_tests.report_generator import ReportGenerator

from db_sync_tests.test_deployment import (
    DatabaseDeploymentTest,
    DatabaseEnvironmentSwitchTest,
    DatabasePerformanceTest
)

from db_sync_tests.test_sync import (
    FullSyncTest,
    IncrementalSyncTest,
    BidirectionalSyncTest,
    SyncLogTest
)

from db_sync_tests.test_boundary import (
    NetworkFluctuationTest,
    DataConflictTest,
    AbnormalInterruptionTest,
    ConcurrentSyncTest,
    LargeDataSyncTest
)


class Command(BaseCommand):
    help = '运行数据库同步测试套件'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['deployment', 'sync', 'boundary', 'all'],
            default='all',
            help='测试类型: deployment(部署测试), sync(同步测试), boundary(边界测试), all(全部测试)'
        )
        
        parser.add_argument(
            '--test-name',
            type=str,
            help='运行特定的测试用例名称'
        )
        
        parser.add_argument(
            '--output-dir',
            type=str,
            default='test_reports',
            help='测试报告输出目录'
        )
        
        parser.add_argument(
            '--report-format',
            type=str,
            choices=['html', 'json', 'markdown', 'all'],
            default='all',
            help='报告格式: html, json, markdown, all'
        )
        
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='启用实时监控'
        )
        
        parser.add_argument(
            '--auto-fix',
            action='store_true',
            help='启用自动修复'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='详细输出'
        )
        
        parser.add_argument(
            '--timeout',
            type=int,
            default=600,
            help='测试超时时间(秒)'
        )

    def handle(self, *args, **options):
        test_type = options['test_type']
        test_name = options['test_name']
        output_dir = options['output_dir']
        report_format = options['report_format']
        enable_monitor = options['monitor']
        enable_auto_fix = options['auto_fix']
        verbose = options['verbose']
        timeout = options['timeout']
        
        self.stdout.write(self.style.SUCCESS(f'开始运行数据库同步测试套件'))
        self.stdout.write(f'测试类型: {test_type}')
        self.stdout.write(f'输出目录: {output_dir}')
        self.stdout.write(f'报告格式: {report_format}')
        self.stdout.write(f'实时监控: {"启用" if enable_monitor else "禁用"}')
        self.stdout.write(f'自动修复: {"启用" if enable_auto_fix else "禁用"}')
        self.stdout.write(f'详细输出: {"启用" if verbose else "禁用"}')
        self.stdout.write(f'超时时间: {timeout}秒')
        self.stdout.write('-' * 60)
        
        start_time = datetime.now()
        
        try:
            test_suite = self._create_test_suite(test_type, test_name, verbose)
            
            monitor = None
            troubleshooter = None
            
            if enable_monitor:
                monitor = self._setup_monitor(test_suite.logger)
                monitor.start()
                self.stdout.write(self.style.SUCCESS('实时监控已启动'))
            
            if enable_auto_fix:
                troubleshooter = Troubleshooter(test_suite.logger)
                self.stdout.write(self.style.SUCCESS('自动修复已启用'))
            
            results = test_suite.run_all()
            
            if monitor:
                monitor.stop()
                self.stdout.write(self.style.SUCCESS('实时监控已停止'))
            
            if troubleshooter:
                self._auto_fix_issues(troubleshooter, monitor)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self._print_summary(results, duration)
            
            report_generator = ReportGenerator(output_dir)
            report_data = self._generate_report_data(results, duration)
            
            self._generate_reports(report_generator, report_data, report_format)
            
            self.stdout.write('-' * 60)
            self.stdout.write(self.style.SUCCESS(f'测试完成，总耗时: {duration:.2f}秒'))
            
            if results['failed'] > 0:
                raise CommandError(f'有 {results["failed"]} 个测试失败')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'测试执行失败: {str(e)}'))
            raise CommandError(str(e))
    
    def _create_test_suite(self, test_type: str, test_name: Optional[str], verbose: bool) -> TestSuite:
        logger = TestLogger(verbose=verbose)
        test_suite = TestSuite(logger)
        
        if test_type == 'all' or test_type == 'deployment':
            test_suite.add_test(DatabaseDeploymentTest(logger))
            test_suite.add_test(DatabaseEnvironmentSwitchTest(logger))
            test_suite.add_test(DatabasePerformanceTest(logger))
        
        if test_type == 'all' or test_type == 'sync':
            test_suite.add_test(FullSyncTest(logger))
            test_suite.add_test(IncrementalSyncTest(logger))
            test_suite.add_test(BidirectionalSyncTest(logger))
            test_suite.add_test(SyncLogTest(logger))
        
        if test_type == 'all' or test_type == 'boundary':
            test_suite.add_test(NetworkFluctuationTest(logger))
            test_suite.add_test(DataConflictTest(logger))
            test_suite.add_test(AbnormalInterruptionTest(logger))
            test_suite.add_test(ConcurrentSyncTest(logger))
            test_suite.add_test(LargeDataSyncTest(logger))
        
        if test_name:
            filtered_tests = [t for t in test_suite.tests if t.__class__.__name__ == test_name]
            if not filtered_tests:
                raise CommandError(f'未找到测试用例: {test_name}')
            test_suite.tests = filtered_tests
        
        return test_suite
    
    def _setup_monitor(self, logger) -> RealTimeMonitor:
        monitor = RealTimeMonitor(logger, interval=5)
        
        db_config = {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': settings.LOCAL_DB_NAME,
            'USER': settings.LOCAL_DB_USER,
            'PASSWORD': settings.LOCAL_DB_PASSWORD,
            'HOST': settings.LOCAL_DB_HOST,
            'PORT': settings.LOCAL_DB_PORT,
        }
        
        monitor.set_database_monitor(db_config)
        
        def monitor_callback(metrics):
            logger.info(f'监控指标 - 数据库连接: {metrics.get("database", {}).get("connection_pool", {}).get("active", 0)}, '
                       f'CPU: {metrics.get("system", {}).get("cpu_percent", 0)}%, '
                       f'内存: {metrics.get("system", {}).get("memory_percent", 0)}%')
        
        monitor.add_callback(monitor_callback)
        
        return monitor
    
    def _auto_fix_issues(self, troubleshooter: Troubleshooter, monitor: Optional[RealTimeMonitor]):
        logger = troubleshooter.logger
        logger.info('开始自动修复检测到的问题')
        
        metrics = None
        if monitor:
            metrics = monitor.collect_metrics()
        
        issues = troubleshooter.diagnose(metrics)
        
        if not issues:
            logger.info('未检测到需要修复的问题')
            return
        
        logger.info(f'检测到 {len(issues)} 个问题')
        
        for issue in issues:
            logger.info(f'问题: {issue.title} ({issue.severity.value})')
            
            if issue.auto_fix_available:
                fix_result = troubleshooter.auto_fix(issue)
                
                if fix_result.success:
                    logger.info(f'自动修复成功: {issue.title}')
                else:
                    logger.error(f'自动修复失败: {issue.title} - {fix_result.error}')
            else:
                logger.warning(f'问题不支持自动修复: {issue.title}')
                logger.info(f'建议解决方案: {issue.recommended_action}')
    
    def _print_summary(self, results: dict, duration: float):
        total = results['total']
        passed = results['passed']
        failed = results['failed']
        skipped = results['skipped']
        
        self.stdout.write('-' * 60)
        self.stdout.write('测试结果摘要:')
        self.stdout.write(f'  总计: {total}')
        self.stdout.write(f'  通过: {passed}')
        self.stdout.write(f'  失败: {failed}')
        self.stdout.write(f'  跳过: {skipped}')
        self.stdout.write(f'  总耗时: {duration:.2f}秒')
        self.stdout.write(f'  成功率: {(passed/total*100):.1f}%' if total > 0 else '  成功率: 0%')
        self.stdout.write('-' * 60)
        
        if failed > 0:
            self.stdout.write(self.style.ERROR('失败的测试:'))
            for result in results['results']:
                if result['status'] == 'failed':
                    self.stdout.write(f'  - {result["test_name"]}: {result["message"]}')
                    if result['errors']:
                        for error in result['errors']:
                            self.stdout.write(f'    错误: {error}')
    
    def _generate_report_data(self, results: dict, duration: float) -> dict:
        return {
            'test_summary': {
                'total': results['total'],
                'passed': results['passed'],
                'failed': results['failed'],
                'skipped': results['skipped'],
                'duration': duration,
                'success_rate': (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
            },
            'test_results': results['results'],
            'start_time': results['start_time'].isoformat() if results.get('start_time') else None,
            'end_time': results['end_time'].isoformat() if results.get('end_time') else None,
            'environment': {
                'python_version': sys.version,
                'django_version': settings.VERSION,
                'database': {
                    'ENGINE': settings.DATABASES['default']['ENGINE'],
                    'NAME': settings.DATABASES['default']['NAME'],
                    'HOST': settings.DATABASES['default']['HOST'],
                    'PORT': settings.DATABASES['default']['PORT'],
                }
            }
        }
    
    def _generate_reports(self, report_generator: ReportGenerator, report_data: dict, report_format: str):
        self.stdout.write('生成测试报告...')
        
        generated_files = []
        
        if report_format in ['html', 'all']:
            html_file = report_generator.generate_html_report(report_data)
            generated_files.append(html_file)
            self.stdout.write(self.style.SUCCESS(f'HTML报告: {html_file}'))
        
        if report_format in ['json', 'all']:
            json_file = report_generator.generate_json_report(report_data)
            generated_files.append(json_file)
            self.stdout.write(self.style.SUCCESS(f'JSON报告: {json_file}'))
        
        if report_format in ['markdown', 'all']:
            md_file = report_generator.generate_markdown_report(report_data)
            generated_files.append(md_file)
            self.stdout.write(self.style.SUCCESS(f'Markdown报告: {md_file}'))
        
        if generated_files:
            self.stdout.write(f'共生成 {len(generated_files)} 个报告文件')
