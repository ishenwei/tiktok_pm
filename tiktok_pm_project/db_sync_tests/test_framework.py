import os
import time
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TestSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TestResult:
    test_name: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    severity: TestSeverity = TestSeverity.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'message': self.message,
            'details': self.details,
            'errors': self.errors,
            'warnings': self.warnings,
            'severity': self.severity.value
        }

@dataclass
class TestReport:
    suite_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    results: List[TestResult] = field(default_factory=list)
    summary: str = ""
    environment: Dict[str, Any] = field(default_factory=dict)
    
    def add_result(self, result: TestResult):
        self.results.append(result)
        self.total_tests += 1
        if result.status == TestStatus.PASSED:
            self.passed_tests += 1
        elif result.status == TestStatus.FAILED:
            self.failed_tests += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped_tests += 1
    
    def calculate_duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def get_success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'suite_name': self.suite_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.calculate_duration(),
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'skipped_tests': self.skipped_tests,
            'success_rate': self.get_success_rate(),
            'results': [r.to_dict() for r in self.results],
            'summary': self.summary,
            'environment': self.environment
        }

class TestLogger:
    def __init__(self, log_dir: str = "test_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"test_run_{timestamp}.log")
        
        self.logger = logging.getLogger("TestLogger")
        self.logger.setLevel(logging.DEBUG)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.log_file = log_file
    
    def info(self, message: str):
        self.logger.info(message)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def critical(self, message: str):
        self.logger.critical(message)
    
    def test_start(self, test_name: str):
        self.info(f"{'='*60}")
        self.info(f"开始测试: {test_name}")
        self.info(f"{'='*60}")
    
    def test_end(self, test_name: str, status: str, duration: float):
        self.info(f"{'='*60}")
        self.info(f"结束测试: {test_name} - 状态: {status} - 耗时: {duration:.2f}秒")
        self.info(f"{'='*60}")

class BaseTest:
    def __init__(self, logger: TestLogger):
        self.logger = logger
        self.result: Optional[TestResult] = None
    
    def setup(self):
        pass
    
    def teardown(self):
        pass
    
    def run(self) -> TestResult:
        test_name = self.__class__.__name__
        self.logger.test_start(test_name)
        
        start_time = datetime.now()
        self.result = TestResult(
            test_name=test_name,
            status=TestStatus.RUNNING,
            start_time=start_time
        )
        
        try:
            self.setup()
            self.execute()
            self.result.status = TestStatus.PASSED
            self.result.message = "测试通过"
        except AssertionError as e:
            self.result.status = TestStatus.FAILED
            self.result.message = f"断言失败: {str(e)}"
            self.result.errors.append(str(e))
            self.logger.error(f"断言失败: {e}")
        except Exception as e:
            self.result.status = TestStatus.FAILED
            self.result.message = f"测试异常: {str(e)}"
            self.result.errors.append(str(e))
            self.logger.error(f"测试异常: {e}", exc_info=True)
        finally:
            try:
                self.teardown()
            except Exception as e:
                self.logger.error(f"清理失败: {e}")
                if self.result.status == TestStatus.PASSED:
                    self.result.status = TestStatus.FAILED
                    self.result.message = f"清理失败: {str(e)}"
            
            end_time = datetime.now()
            self.result.end_time = end_time
            self.result.duration = (end_time - start_time).total_seconds()
            
            self.logger.test_end(test_name, self.result.status.value, self.result.duration)
        
        return self.result
    
    def execute(self):
        raise NotImplementedError("子类必须实现execute方法")
    
    def assert_true(self, condition: bool, message: str = ""):
        if not condition:
            raise AssertionError(message or "条件不满足")
    
    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
        if actual != expected:
            raise AssertionError(message or f"期望: {expected}, 实际: {actual}")
    
    def assert_not_none(self, value: Any, message: str = ""):
        if value is None:
            raise AssertionError(message or "值不能为None")
    
    def assert_greater_than(self, actual: int, threshold: int, message: str = ""):
        if actual <= threshold:
            raise AssertionError(message or f"值 {actual} 必须大于 {threshold}")

class TestSuite:
    def __init__(self, suite_name: str, logger: TestLogger):
        self.suite_name = suite_name
        self.logger = logger
        self.tests: List[BaseTest] = []
        self.report = TestReport(
            suite_name=suite_name,
            start_time=datetime.now()
        )
    
    def add_test(self, test: BaseTest):
        self.tests.append(test)
    
    def run_all(self) -> TestReport:
        self.logger.info(f"开始执行测试套件: {self.suite_name}")
        self.logger.info(f"测试用例总数: {len(self.tests)}")
        
        for test in self.tests:
            try:
                result = test.run()
                self.report.add_result(result)
            except Exception as e:
                self.logger.error(f"测试执行异常: {e}", exc_info=True)
                error_result = TestResult(
                    test_name=test.__class__.__name__,
                    status=TestStatus.FAILED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    message=f"测试执行异常: {str(e)}"
                )
                error_result.errors.append(str(e))
                self.report.add_result(error_result)
        
        self.report.end_time = datetime.now()
        self._generate_summary()
        
        self.logger.info(f"测试套件完成: {self.suite_name}")
        self.logger.info(f"总计: {self.report.total_tests}, "
                        f"通过: {self.report.passed_tests}, "
                        f"失败: {self.report.failed_tests}, "
                        f"跳过: {self.report.skipped_tests}")
        self.logger.info(f"成功率: {self.report.get_success_rate():.2f}%")
        
        return self.report
    
    def _generate_summary(self):
        success_rate = self.report.get_success_rate()
        if success_rate == 100:
            self.report.summary = "所有测试用例通过"
        elif success_rate >= 80:
            self.report.summary = f"大部分测试用例通过 ({success_rate:.2f}%)"
        elif success_rate >= 50:
            self.report.summary = f"部分测试用例通过 ({success_rate:.2f}%)"
        else:
            self.report.summary = f"测试失败严重 ({success_rate:.2f}%)"
