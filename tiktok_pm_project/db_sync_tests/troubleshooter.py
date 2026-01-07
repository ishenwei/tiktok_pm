import time
import subprocess
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

class IssueType(Enum):
    NETWORK = "network"
    DATABASE = "database"
    DOCKER = "docker"
    SYNC = "sync"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"

class IssueSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Issue:
    issue_type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    root_cause: str = ""
    suggested_solutions: List[str] = field(default_factory=list)
    auto_fix_available: bool = False
    auto_fix_command: Optional[str] = None
    timestamp: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'issue_type': self.issue_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'root_cause': self.root_cause,
            'suggested_solutions': self.suggested_solutions,
            'auto_fix_available': self.auto_fix_available,
            'auto_fix_command': self.auto_fix_command,
            'timestamp': self.timestamp,
            'details': self.details
        }

@dataclass
class FixResult:
    success: bool
    issue: Issue
    fix_attempted: bool
    fix_command: Optional[str] = None
    output: str = ""
    error: str = ""
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'issue': self.issue.to_dict(),
            'fix_attempted': self.fix_attempted,
            'fix_command': self.fix_command,
            'output': self.output,
            'error': self.error,
            'timestamp': self.timestamp
        }

class Troubleshooter:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.detected_issues: List[Issue] = []
        self.fix_history: List[FixResult] = []
        self._setup_diagnostic_rules()
    
    def _setup_diagnostic_rules(self):
        self.diagnostic_rules = [
            {
                'name': 'Docker容器未运行',
                'type': IssueType.DOCKER,
                'check': self._check_docker_containers,
                'severity': IssueSeverity.CRITICAL
            },
            {
                'name': '数据库连接失败',
                'type': IssueType.DATABASE,
                'check': self._check_database_connection,
                'severity': IssueSeverity.CRITICAL
            },
            {
                'name': '网络连接问题',
                'type': IssueType.NETWORK,
                'check': self._check_network_connectivity,
                'severity': IssueSeverity.HIGH
            },
            {
                'name': '磁盘空间不足',
                'type': IssueType.RESOURCE,
                'check': self._check_disk_space,
                'severity': IssueSeverity.HIGH
            },
            {
                'name': '内存不足',
                'type': IssueType.RESOURCE,
                'check': self._check_memory,
                'severity': IssueSeverity.HIGH
            },
            {
                'name': '同步配置错误',
                'type': IssueType.CONFIGURATION,
                'check': self._check_sync_configuration,
                'severity': IssueSeverity.MEDIUM
            },
            {
                'name': '同步表不存在',
                'type': IssueType.DATABASE,
                'check': self._check_sync_tables,
                'severity': IssueSeverity.HIGH
            },
            {
                'name': 'Django Q Worker未运行',
                'type': IssueType.DOCKER,
                'check': self._check_worker_status,
                'severity': IssueSeverity.HIGH
            }
        ]
    
    def diagnose(self, metrics: Optional[Dict[str, Any]] = None) -> List[Issue]:
        self.detected_issues.clear()
        
        for rule in self.diagnostic_rules:
            try:
                issues = rule['check'](metrics)
                if issues:
                    self.detected_issues.extend(issues)
            except Exception as e:
                self.logger.error(f"执行诊断规则失败: {rule['name']} - {e}")
        
        self._sort_issues_by_severity()
        return self.detected_issues
    
    def _sort_issues_by_severity(self):
        severity_order = {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.HIGH: 1,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 3
        }
        self.detected_issues.sort(key=lambda x: severity_order.get(x.severity, 4))
    
    def _check_docker_containers(self, metrics: Optional[Dict[str, Any]]) -> List[Issue]:
        issues = []
        
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                issues.append(Issue(
                    issue_type=IssueType.DOCKER,
                    severity=IssueSeverity.CRITICAL,
                    title="Docker服务未运行",
                    description="无法执行docker ps命令，Docker服务可能未启动",
                    root_cause="Docker守护进程未运行或权限不足",
                    suggested_solutions=[
                        "检查Docker服务状态: sudo systemctl status docker",
                        "启动Docker服务: sudo systemctl start docker",
                        "检查用户权限: 将用户添加到docker组"
                    ],
                    auto_fix_available=True,
                    auto_fix_command="sudo systemctl start docker"
                ))
                return issues
            
            running_containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            required_containers = ['tiktok_pm_mariadb', 'tiktok_pm_web', 'tiktok_pm_worker']
            
            for container in required_containers:
                if container not in running_containers:
                    issues.append(Issue(
                        issue_type=IssueType.DOCKER,
                        severity=IssueSeverity.CRITICAL,
                        title=f"容器{container}未运行",
                        description=f"必需的Docker容器{container}未在运行",
                        root_cause="容器可能已停止或启动失败",
                        suggested_solutions=[
                            f"查看容器日志: docker-compose logs {container}",
                            f"重启容器: docker-compose restart {container}",
                            "检查容器配置: docker-compose.yml"
                        ],
                        auto_fix_available=True,
                        auto_fix_command=f"docker-compose restart {container}"
                    ))
        
        except Exception as e:
            self.logger.error(f"检查Docker容器失败: {e}")
        
        return issues
    
    def _check_database_connection(self, metrics: Optional[Dict[str, Any]]) -> List[Issue]:
        issues = []
        
        try:
            import pymysql
            from django.conf import settings
            
            db_config = settings.DATABASES.get('default', {})
            
            connection = pymysql.connect(
                host=db_config.get('HOST'),
                port=db_config.get('PORT'),
                user=db_config.get('USER'),
                password=db_config.get('PASSWORD'),
                database=db_config.get('NAME'),
                connect_timeout=5
            )
            
            connection.close()
        
        except pymysql.Error as e:
            issues.append(Issue(
                issue_type=IssueType.DATABASE,
                severity=IssueSeverity.CRITICAL,
                title="数据库连接失败",
                description=f"无法连接到数据库: {str(e)}",
                root_cause="数据库服务未运行、网络不可达或认证失败",
                suggested_solutions=[
                    "检查数据库服务状态",
                    "验证数据库连接配置",
                    "检查网络连接",
                    "验证用户名和密码"
                ],
                auto_fix_available=False,
                details={'error': str(e)}
            ))
        except Exception as e:
            self.logger.error(f"检查数据库连接失败: {e}")
        
        return issues
    
    def _check_network_connectivity(self, metrics: Optional[Dict[str, Any]]) -> List[Issue]:
        issues = []
        
        try:
            from django.conf import settings
            
            db_config = settings.DATABASES.get('default', {})
            host = db_config.get('HOST', 'localhost')
            port = db_config.get('PORT', 3306)
            
            result = subprocess.run(
                ['nc', '-zv', host, str(port)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                issues.append(Issue(
                    issue_type=IssueType.NETWORK,
                    severity=IssueSeverity.HIGH,
                    title=f"无法连接到{host}:{port}",
                    description="数据库端口不可达",
                    root_cause="网络连接问题或防火墙阻止",
                    suggested_solutions=[
                        "检查网络连接",
                        "检查防火墙规则",
                        "验证主机名和端口配置",
                        "测试网络连通性: ping <host>"
                    ],
                    auto_fix_available=False
                ))
        
        except Exception as e:
            self.logger.error(f"检查网络连接失败: {e}")
        
        return issues
    
    def _check_disk_space(self, metrics: Optional[Dict[str, Any]]) -> List[Issue]:
        issues = []
        
        try:
            import shutil
            
            total, used, free = shutil.disk_usage('/')
            usage_percent = (used / total) * 100
            
            if usage_percent > 90:
                issues.append(Issue(
                    issue_type=IssueType.RESOURCE,
                    severity=IssueSeverity.CRITICAL,
                    title="磁盘空间严重不足",
                    description=f"磁盘使用率: {usage_percent:.1f}%",
                    root_cause="磁盘空间不足可能影响系统运行",
                    suggested_solutions=[
                        "清理不必要的文件",
                        "清理Docker镜像和容器: docker system prune -a",
                        "清理日志文件",
                        "扩展磁盘空间"
                    ],
                    auto_fix_available=True,
                    auto_fix_command="docker system prune -a -f",
                    details={'usage_percent': usage_percent, 'free_gb': free / (1024**3)}
                ))
            elif usage_percent > 80:
                issues.append(Issue(
                    issue_type=IssueType.RESOURCE,
                    severity=IssueSeverity.HIGH,
                    title="磁盘空间不足",
                    description=f"磁盘使用率: {usage_percent:.1f}%",
                    root_cause="磁盘空间不足可能影响系统运行",
                    suggested_solutions=[
                        "清理不必要的文件",
                        "清理Docker镜像和容器: docker system prune -a",
                        "清理日志文件"
                    ],
                    auto_fix_available=True,
                    auto_fix_command="docker system prune -a -f",
                    details={'usage_percent': usage_percent, 'free_gb': free / (1024**3)}
                ))
        
        except Exception as e:
            self.logger.error(f"检查磁盘空间失败: {e}")
        
        return issues
    
    def _check_memory(self, metrics: Optional[Dict[str, Any]]) -> List[Issue]:
        issues = []
        
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                issues.append(Issue(
                    issue_type=IssueType.RESOURCE,
                    severity=IssueSeverity.CRITICAL,
                    title="内存严重不足",
                    description=f"内存使用率: {memory.percent:.1f}%",
                    root_cause="内存不足可能导致系统崩溃",
                    suggested_solutions=[
                        "关闭不必要的进程",
                        "增加系统内存",
                        "优化应用程序内存使用",
                        "清理缓存"
                    ],
                    auto_fix_available=False,
                    details={'memory_percent': memory.percent, 'available_gb': memory.available / (1024**3)}
                ))
            elif memory.percent > 80:
                issues.append(Issue(
                    issue_type=IssueType.RESOURCE,
                    severity=IssueSeverity.HIGH,
                    title="内存不足",
                    description=f"内存使用率: {memory.percent:.1f}%",
                    root_cause="内存不足可能影响系统性能",
                    suggested_solutions=[
                        "关闭不必要的进程",
                        "增加系统内存",
                        "优化应用程序内存使用"
                    ],
                    auto_fix_available=False,
                    details={'memory_percent': memory.percent, 'available_gb': memory.available / (1024**3)}
                ))
        
        except Exception as e:
            self.logger.error(f"检查内存失败: {e}")
        
        return issues
    
    def _check_sync_configuration(self, metrics: Optional[Dict[str, Any]]) -> List[Issue]:
        issues = []
        
        try:
            from django.conf import settings
            
            sync_enabled = getattr(settings, 'DB_SYNC_ENABLED', False)
            
            if not sync_enabled:
                issues.append(Issue(
                    issue_type=IssueType.CONFIGURATION,
                    severity=IssueSeverity.LOW,
                    title="数据同步未启用",
                    description="DB_SYNC_ENABLED设置为False",
                    root_cause="数据同步功能被禁用",
                    suggested_solutions=[
                        "在.env文件中设置DB_SYNC_ENABLED=True",
                        "重启Django服务"
                    ],
                    auto_fix_available=False
                ))
            
            sync_interval = getattr(settings, 'DB_SYNC_INTERVAL', 60)
            if sync_interval < 5:
                issues.append(Issue(
                    issue_type=IssueType.CONFIGURATION,
                    severity=IssueSeverity.MEDIUM,
                    title="同步间隔过短",
                    description=f"同步间隔: {sync_interval}分钟",
                    root_cause="过短的同步间隔可能导致系统负载过高",
                    suggested_solutions=[
                        "增加同步间隔到合理值(建议30-120分钟)",
                        "在.env文件中设置DB_SYNC_INTERVAL=60"
                    ],
                    auto_fix_available=False
                ))
        
        except Exception as e:
            self.logger.error(f"检查同步配置失败: {e}")
        
        return issues
    
    def _check_sync_tables(self, metrics: Optional[Dict[str, Any]]) -> List[Issue]:
        issues = []
        
        try:
            import pymysql
            from django.conf import settings
            
            db_config = settings.DATABASES.get('default', {})
            
            connection = pymysql.connect(
                host=db_config.get('HOST'),
                port=db_config.get('PORT'),
                user=db_config.get('USER'),
                password=db_config.get('PASSWORD'),
                database=db_config.get('NAME')
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'db_sync_log'")
                if not cursor.fetchone():
                    issues.append(Issue(
                        issue_type=IssueType.DATABASE,
                        severity=IssueSeverity.HIGH,
                        title="同步日志表不存在",
                        description="db_sync_log表不存在",
                        root_cause="数据库初始化脚本未执行",
                        suggested_solutions=[
                            "执行数据库初始化脚本",
                            "重新启动MariaDB容器"
                        ],
                        auto_fix_available=True,
                        auto_fix_command="docker-compose restart mariadb"
                    ))
                
                cursor.execute("SHOW TABLES LIKE 'db_sync_config'")
                if not cursor.fetchone():
                    issues.append(Issue(
                        issue_type=IssueType.DATABASE,
                        severity=IssueSeverity.HIGH,
                        title="同步配置表不存在",
                        description="db_sync_config表不存在",
                        root_cause="数据库初始化脚本未执行",
                        suggested_solutions=[
                            "执行数据库初始化脚本",
                            "重新启动MariaDB容器"
                        ],
                        auto_fix_available=True,
                        auto_fix_command="docker-compose restart mariadb"
                    ))
            
            connection.close()
        
        except Exception as e:
            self.logger.error(f"检查同步表失败: {e}")
        
        return issues
    
    def _check_worker_status(self, metrics: Optional[Dict[str, Any]]) -> List[Issue]:
        issues = []
        
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=tiktok_pm_worker', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if not result.stdout.strip():
                issues.append(Issue(
                    issue_type=IssueType.DOCKER,
                    severity=IssueSeverity.HIGH,
                    title="Django Q Worker未运行",
                    description="tiktok_pm_worker容器未在运行",
                    root_cause="Worker容器已停止或启动失败",
                    suggested_solutions=[
                        "查看Worker日志: docker-compose logs worker",
                        "重启Worker: docker-compose restart worker",
                        "检查Worker配置"
                    ],
                    auto_fix_available=True,
                    auto_fix_command="docker-compose restart worker"
                ))
        
        except Exception as e:
            self.logger.error(f"检查Worker状态失败: {e}")
        
        return issues
    
    def auto_fix(self, issue: Issue) -> FixResult:
        from datetime import datetime
        
        fix_result = FixResult(
            success=False,
            issue=issue,
            fix_attempted=False,
            timestamp=datetime.now().isoformat()
        )
        
        if not issue.auto_fix_available or not issue.auto_fix_command:
            fix_result.error = "该问题不支持自动修复"
            return fix_result
        
        try:
            self.logger.info(f"尝试自动修复: {issue.title}")
            self.logger.info(f"执行命令: {issue.auto_fix_command}")
            
            result = subprocess.run(
                issue.auto_fix_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            fix_result.fix_attempted = True
            fix_result.fix_command = issue.auto_fix_command
            fix_result.output = result.stdout
            
            if result.returncode == 0:
                fix_result.success = True
                self.logger.info(f"自动修复成功: {issue.title}")
            else:
                fix_result.error = result.stderr or "命令执行失败"
                self.logger.error(f"自动修复失败: {issue.title} - {fix_result.error}")
        
        except subprocess.TimeoutExpired:
            fix_result.error = "命令执行超时"
            self.logger.error(f"自动修复超时: {issue.title}")
        except Exception as e:
            fix_result.error = str(e)
            self.logger.error(f"自动修复异常: {issue.title} - {e}")
        
        self.fix_history.append(fix_result)
        return fix_result
    
    def auto_fix_all(self) -> List[FixResult]:
        results = []
        
        for issue in self.detected_issues:
            if issue.auto_fix_available:
                result = self.auto_fix(issue)
                results.append(result)
                
                if result.success:
                    time.sleep(2)
        
        return results
    
    def get_diagnostic_report(self) -> Dict[str, Any]:
        return {
            'detected_issues': [issue.to_dict() for issue in self.detected_issues],
            'fix_history': [fix.to_dict() for fix in self.fix_history],
            'summary': {
                'total_issues': len(self.detected_issues),
                'critical_issues': len([i for i in self.detected_issues if i.severity == IssueSeverity.CRITICAL]),
                'high_issues': len([i for i in self.detected_issues if i.severity == IssueSeverity.HIGH]),
                'medium_issues': len([i for i in self.detected_issues if i.severity == IssueSeverity.MEDIUM]),
                'low_issues': len([i for i in self.detected_issues if i.severity == IssueSeverity.LOW]),
                'auto_fixable': len([i for i in self.detected_issues if i.auto_fix_available])
            }
        }
