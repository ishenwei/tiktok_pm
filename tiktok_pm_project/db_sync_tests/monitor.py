import time
import psutil
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading

class MonitorStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class DatabaseMetrics:
    connection_count: int = 0
    active_connections: int = 0
    query_count: int = 0
    slow_queries: int = 0
    uptime: int = 0
    database_size: float = 0.0
    table_count: int = 0
    status: MonitorStatus = MonitorStatus.UNKNOWN
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'connection_count': self.connection_count,
            'active_connections': self.active_connections,
            'query_count': self.query_count,
            'slow_queries': self.slow_queries,
            'uptime': self.uptime,
            'database_size': self.database_size,
            'table_count': self.table_count,
            'status': self.status.value
        }

@dataclass
class SyncMetrics:
    sync_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    total_rows_synced: int = 0
    avg_sync_duration: float = 0.0
    last_sync_time: Optional[datetime] = None
    last_sync_status: str = ""
    sync_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sync_count': self.sync_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'total_rows_synced': self.total_rows_synced,
            'avg_sync_duration': self.avg_sync_duration,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'last_sync_status': self.last_sync_status,
            'sync_errors': self.sync_errors
        }

@dataclass
class SystemMetrics:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_usage_percent: float = 0.0
    network_io_sent: int = 0
    network_io_recv: int = 0
    docker_container_status: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'disk_usage_percent': self.disk_usage_percent,
            'network_io_sent': self.network_io_sent,
            'network_io_recv': self.network_io_recv,
            'docker_container_status': self.docker_container_status
        }

class DatabaseMonitor:
    def __init__(self, db_config: Dict[str, Any], logger: logging.Logger):
        self.db_config = db_config
        self.logger = logger
        self.metrics_history: List[DatabaseMetrics] = []
        self.max_history_size = 100
    
    def get_current_metrics(self) -> DatabaseMetrics:
        metrics = DatabaseMetrics()
        
        try:
            import pymysql
            
            connection = pymysql.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 3306),
                user=self.db_config.get('user', 'root'),
                password=self.db_config.get('password', ''),
                database=self.db_config.get('database', 'information_schema')
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                result = cursor.fetchone()
                metrics.connection_count = int(result[1]) if result else 0
                
                cursor.execute("SHOW STATUS LIKE 'Threads_running'")
                result = cursor.fetchone()
                metrics.active_connections = int(result[1]) if result else 0
                
                cursor.execute("SHOW STATUS LIKE 'Questions'")
                result = cursor.fetchone()
                metrics.query_count = int(result[1]) if result else 0
                
                cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
                result = cursor.fetchone()
                metrics.slow_queries = int(result[1]) if result else 0
                
                cursor.execute("SHOW STATUS LIKE 'Uptime'")
                result = cursor.fetchone()
                metrics.uptime = int(result[1]) if result else 0
                
                cursor.execute("SHOW STATUS LIKE 'Table_locks_waited'")
                result = cursor.fetchone()
                table_locks = int(result[1]) if result else 0
                
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", 
                             (self.db_config.get('database'),))
                result = cursor.fetchone()
                metrics.table_count = int(result[0]) if result else 0
            
            connection.close()
            
            metrics.status = self._evaluate_status(metrics)
            
        except Exception as e:
            self.logger.error(f"获取数据库指标失败: {e}")
            metrics.status = MonitorStatus.CRITICAL
        
        self._add_to_history(metrics)
        return metrics
    
    def _evaluate_status(self, metrics: DatabaseMetrics) -> MonitorStatus:
        if metrics.connection_count > 100:
            return MonitorStatus.CRITICAL
        elif metrics.connection_count > 80:
            return MonitorStatus.WARNING
        elif metrics.slow_queries > 10:
            return MonitorStatus.WARNING
        else:
            return MonitorStatus.HEALTHY
    
    def _add_to_history(self, metrics: DatabaseMetrics):
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
    
    def get_metrics_history(self, minutes: int = 10) -> List[DatabaseMetrics]:
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m.status != MonitorStatus.UNKNOWN]

class SyncMonitor:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics = SyncMetrics()
        self.sync_history: List[Dict[str, Any]] = []
    
    def record_sync(self, result: Dict[str, Any]):
        self.metrics.sync_count += 1
        
        if result.get('success', False):
            self.metrics.success_count += 1
            self.metrics.last_sync_status = "SUCCESS"
        else:
            self.metrics.failed_count += 1
            self.metrics.last_sync_status = "FAILED"
            if result.get('errors'):
                self.metrics.sync_errors.extend([e.get('error', '未知错误') for e in result['errors']])
        
        self.metrics.total_rows_synced += result.get('total_rows', 0)
        
        duration = result.get('duration', 0)
        if self.metrics.sync_count > 0:
            self.metrics.avg_sync_duration = (
                (self.metrics.avg_sync_duration * (self.metrics.sync_count - 1) + duration) / 
                self.metrics.sync_count
            )
        
        self.metrics.last_sync_time = datetime.now()
        
        self.sync_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': result
        })
    
    def get_current_metrics(self) -> SyncMetrics:
        return self.metrics
    
    def get_success_rate(self) -> float:
        if self.metrics.sync_count == 0:
            return 0.0
        return (self.metrics.success_count / self.metrics.sync_count) * 100

class SystemMonitor:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 100
    
    def get_current_metrics(self) -> SystemMetrics:
        metrics = SystemMetrics()
        
        try:
            metrics.cpu_percent = psutil.cpu_percent(interval=1)
            metrics.memory_percent = psutil.virtual_memory().percent
            metrics.disk_usage_percent = psutil.disk_usage('/').percent
            
            net_io = psutil.net_io_counters()
            metrics.network_io_sent = net_io.bytes_sent
            metrics.network_io_recv = net_io.bytes_recv
            
            metrics.docker_container_status = self._get_docker_container_status()
            
        except Exception as e:
            self.logger.error(f"获取系统指标失败: {e}")
        
        self._add_to_history(metrics)
        return metrics
    
    def _get_docker_container_status(self) -> Dict[str, str]:
        status = {}
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) == 2:
                            status[parts[0]] = parts[1]
        
        except Exception as e:
            self.logger.error(f"获取Docker容器状态失败: {e}")
        
        return status
    
    def _add_to_history(self, metrics: SystemMetrics):
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)

class RealTimeMonitor:
    def __init__(self, logger: logging.Logger, interval: int = 5):
        self.logger = logger
        self.interval = interval
        self.db_monitor: Optional[DatabaseMonitor] = None
        self.sync_monitor = SyncMonitor(logger)
        self.system_monitor = SystemMonitor(logger)
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable] = []
    
    def set_database_monitor(self, db_config: Dict[str, Any]):
        self.db_monitor = DatabaseMonitor(db_config, self.logger)
    
    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)
    
    def start(self):
        if self.is_monitoring:
            self.logger.warning("监控已经在运行")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info(f"实时监控已启动，间隔: {self.interval}秒")
    
    def stop(self):
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("实时监控已停止")
    
    def _monitor_loop(self):
        while self.is_monitoring:
            try:
                metrics = self.collect_metrics()
                
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        self.logger.error(f"回调执行失败: {e}")
                
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
            
            time.sleep(self.interval)
    
    def collect_metrics(self) -> Dict[str, Any]:
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': self.system_monitor.get_current_metrics().to_dict(),
            'sync': self.sync_monitor.get_current_metrics().to_dict()
        }
        
        if self.db_monitor:
            metrics['database'] = self.db_monitor.get_current_metrics().to_dict()
        
        return metrics
    
    def get_snapshot(self) -> Dict[str, Any]:
        return self.collect_metrics()

class AlertManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.alerts: List[Dict[str, Any]] = []
        self.alert_rules: List[Dict[str, Any]] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        self.alert_rules = [
            {
                'name': 'CPU使用率过高',
                'condition': lambda m: m['system']['cpu_percent'] > 80,
                'severity': 'HIGH',
                'message': 'CPU使用率超过80%'
            },
            {
                'name': '内存使用率过高',
                'condition': lambda m: m['system']['memory_percent'] > 85,
                'severity': 'HIGH',
                'message': '内存使用率超过85%'
            },
            {
                'name': '磁盘使用率过高',
                'condition': lambda m: m['system']['disk_usage_percent'] > 90,
                'severity': 'CRITICAL',
                'message': '磁盘使用率超过90%'
            },
            {
                'name': '数据库连接数过多',
                'condition': lambda m: m.get('database', {}).get('connection_count', 0) > 100,
                'severity': 'HIGH',
                'message': '数据库连接数超过100'
            },
            {
                'name': '同步失败率过高',
                'condition': lambda m: self._calculate_failure_rate(m) > 20,
                'severity': 'MEDIUM',
                'message': '同步失败率超过20%'
            }
        ]
    
    def _calculate_failure_rate(self, metrics: Dict[str, Any]) -> float:
        sync_metrics = metrics.get('sync', {})
        sync_count = sync_metrics.get('sync_count', 0)
        failed_count = sync_metrics.get('failed_count', 0)
        
        if sync_count == 0:
            return 0.0
        
        return (failed_count / sync_count) * 100
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        triggered_alerts = []
        
        for rule in self.alert_rules:
            try:
                if rule['condition'](metrics):
                    alert = {
                        'timestamp': datetime.now().isoformat(),
                        'rule_name': rule['name'],
                        'severity': rule['severity'],
                        'message': rule['message'],
                        'metrics': metrics
                    }
                    
                    triggered_alerts.append(alert)
                    self.alerts.append(alert)
                    
                    self.logger.warning(f"触发告警: {rule['name']} - {rule['message']}")
            
            except Exception as e:
                self.logger.error(f"检查告警规则失败: {e}")
        
        return triggered_alerts
    
    def get_recent_alerts(self, minutes: int = 30) -> List[Dict[str, Any]]:
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) >= cutoff_time
        ]
    
    def clear_alerts(self):
        self.alerts.clear()
        self.logger.info("告警记录已清空")
