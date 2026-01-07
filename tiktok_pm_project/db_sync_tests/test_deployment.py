import time
import subprocess
import pymysql
from typing import Dict, Any
from .test_framework import BaseTest, TestResult

class DatabaseDeploymentTest(BaseTest):
    def execute(self):
        self.logger.info("开始测试数据库部署")
        
        self._test_docker_service()
        self._test_mariadb_container()
        self._test_database_connection()
        self._test_database_initialization()
        self._test_sync_tables()
        self._test_database_configuration()
        
        self.logger.info("数据库部署测试完成")
    
    def _test_docker_service(self):
        self.logger.info("测试Docker服务状态")
        
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        self.assert_true(
            result.returncode == 0,
            f"Docker未安装或无法运行: {result.stderr}"
        )
        
        self.result.details['docker_version'] = result.stdout.strip()
        self.logger.info(f"Docker版本: {result.stdout.strip()}")
    
    def _test_mariadb_container(self):
        self.logger.info("测试MariaDB容器状态")
        
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=tiktok_pm_mariadb', '--format', '{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        self.assert_true(
            result.returncode == 0,
            f"无法查询Docker容器状态: {result.stderr}"
        )
        
        self.assert_true(
            result.stdout.strip() != '',
            "MariaDB容器未运行"
        )
        
        self.result.details['mariadb_status'] = result.stdout.strip()
        self.logger.info(f"MariaDB容器状态: {result.stdout.strip()}")
    
    def _test_database_connection(self):
        self.logger.info("测试数据库连接")
        
        from django.conf import settings
        
        db_config = settings.DATABASES.get('default', {})
        
        try:
            connection = pymysql.connect(
                host=db_config.get('HOST'),
                port=db_config.get('PORT'),
                user=db_config.get('USER'),
                password=db_config.get('PASSWORD'),
                database=db_config.get('NAME'),
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.assert_true(result[0] == 1, "数据库查询失败")
            
            connection.close()
            
            self.result.details['database_connection'] = 'success'
            self.logger.info("数据库连接成功")
        
        except Exception as e:
            self.assert_true(False, f"数据库连接失败: {str(e)}")
    
    def _test_database_initialization(self):
        self.logger.info("测试数据库初始化")
        
        from django.conf import settings
        
        db_config = settings.DATABASES.get('default', {})
        
        try:
            connection = pymysql.connect(
                host=db_config.get('HOST'),
                port=db_config.get('PORT'),
                user=db_config.get('USER'),
                password=db_config.get('PASSWORD'),
                database=db_config.get('NAME')
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES LIKE %s", (db_config.get('NAME'),))
                result = cursor.fetchone()
                self.assert_true(result is not None, "数据库未创建")
                
                cursor.execute("SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME "
                             "FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
                             (db_config.get('NAME'),))
                result = cursor.fetchone()
                self.assert_true(
                    result is not None and result[0] == 'utf8mb4',
                    "数据库字符集配置不正确"
                )
            
            connection.close()
            
            self.result.details['database_initialization'] = 'success'
            self.logger.info("数据库初始化检查通过")
        
        except Exception as e:
            self.assert_true(False, f"数据库初始化检查失败: {str(e)}")
    
    def _test_sync_tables(self):
        self.logger.info("测试同步表创建")
        
        from django.conf import settings
        
        db_config = settings.DATABASES.get('default', {})
        
        try:
            connection = pymysql.connect(
                host=db_config.get('HOST'),
                port=db_config.get('PORT'),
                user=db_config.get('USER'),
                password=db_config.get('PASSWORD'),
                database=db_config.get('NAME')
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'db_sync_log'")
                result = cursor.fetchone()
                self.assert_true(result is not None, "db_sync_log表不存在")
                
                cursor.execute("DESCRIBE db_sync_log")
                columns = [row[0] for row in cursor.fetchall()]
                required_columns = ['id', 'sync_type', 'direction', 'status', 'start_time', 'end_time']
                for col in required_columns:
                    self.assert_true(col in columns, f"db_sync_log表缺少列: {col}")
                
                cursor.execute("SHOW TABLES LIKE 'db_sync_config'")
                result = cursor.fetchone()
                self.assert_true(result is not None, "db_sync_config表不存在")
                
                cursor.execute("DESCRIBE db_sync_config")
                columns = [row[0] for row in cursor.fetchall()]
                required_columns = ['id', 'table_name', 'sync_enabled', 'sync_type', 'sync_direction']
                for col in required_columns:
                    self.assert_true(col in columns, f"db_sync_config表缺少列: {col}")
            
            connection.close()
            
            self.result.details['sync_tables'] = 'success'
            self.logger.info("同步表检查通过")
        
        except Exception as e:
            self.assert_true(False, f"同步表检查失败: {str(e)}")
    
    def _test_database_configuration(self):
        self.logger.info("测试数据库配置")
        
        from django.conf import settings
        
        db_config = settings.DATABASES.get('default', {})
        
        self.assert_true('ENGINE' in db_config, "数据库配置缺少ENGINE")
        self.assert_true('HOST' in db_config, "数据库配置缺少HOST")
        self.assert_true('PORT' in db_config, "数据库配置缺少PORT")
        self.assert_true('NAME' in db_config, "数据库配置缺少NAME")
        self.assert_true('USER' in db_config, "数据库配置缺少USER")
        self.assert_true('PASSWORD' in db_config, "数据库配置缺少PASSWORD")
        
        self.assert_true(
            db_config['ENGINE'] == 'django.db.backends.mysql',
            "数据库引擎配置不正确"
        )
        
        self.result.details['database_configuration'] = 'success'
        self.logger.info("数据库配置检查通过")

class DatabaseEnvironmentSwitchTest(BaseTest):
    def execute(self):
        self.logger.info("开始测试数据库环境切换")
        
        self._test_environment_variable()
        self._test_remote_database_config()
        self._test_local_database_config()
        self._test_environment_switch()
        
        self.logger.info("数据库环境切换测试完成")
    
    def _test_environment_variable(self):
        self.logger.info("测试环境变量配置")
        
        from django.conf import settings
        
        db_env = getattr(settings, 'DB_ENV', None)
        self.assert_true(db_env is not None, "DB_ENV环境变量未设置")
        self.assert_true(
            db_env in ['remote', 'local'],
            f"DB_ENV值不正确: {db_env}"
        )
        
        self.result.details['current_db_env'] = db_env
        self.logger.info(f"当前数据库环境: {db_env}")
    
    def _test_remote_database_config(self):
        self.logger.info("测试远程数据库配置")
        
        from django.conf import settings
        
        remote_host = getattr(settings, 'DB_REMOTE_HOST', None)
        remote_port = getattr(settings, 'DB_REMOTE_PORT', None)
        remote_name = getattr(settings, 'DB_REMOTE_NAME', None)
        remote_user = getattr(settings, 'DB_REMOTE_USER', None)
        remote_password = getattr(settings, 'DB_REMOTE_PASSWORD', None)
        
        self.assert_true(remote_host is not None, "DB_REMOTE_HOST未设置")
        self.assert_true(remote_port is not None, "DB_REMOTE_PORT未设置")
        self.assert_true(remote_name is not None, "DB_REMOTE_NAME未设置")
        self.assert_true(remote_user is not None, "DB_REMOTE_USER未设置")
        self.assert_true(remote_password is not None, "DB_REMOTE_PASSWORD未设置")
        
        self.result.details['remote_db_config'] = {
            'host': remote_host,
            'port': remote_port,
            'name': remote_name,
            'user': remote_user
        }
        self.logger.info("远程数据库配置检查通过")
    
    def _test_local_database_config(self):
        self.logger.info("测试本地数据库配置")
        
        from django.conf import settings
        
        local_host = getattr(settings, 'DB_LOCAL_HOST', None)
        local_port = getattr(settings, 'DB_LOCAL_PORT', None)
        local_name = getattr(settings, 'DB_LOCAL_NAME', None)
        local_user = getattr(settings, 'DB_LOCAL_USER', None)
        local_password = getattr(settings, 'DB_LOCAL_PASSWORD', None)
        
        self.assert_true(local_host is not None, "DB_LOCAL_HOST未设置")
        self.assert_true(local_port is not None, "DB_LOCAL_PORT未设置")
        self.assert_true(local_name is not None, "DB_LOCAL_NAME未设置")
        self.assert_true(local_user is not None, "DB_LOCAL_USER未设置")
        self.assert_true(local_password is not None, "DB_LOCAL_PASSWORD未设置")
        
        self.result.details['local_db_config'] = {
            'host': local_host,
            'port': local_port,
            'name': local_name,
            'user': local_user
        }
        self.logger.info("本地数据库配置检查通过")
    
    def _test_environment_switch(self):
        self.logger.info("测试环境切换功能")
        
        from django.conf import settings
        
        db_env = getattr(settings, 'DB_ENV', None)
        db_config = settings.DATABASES.get('default', {})
        
        if db_env == 'local':
            expected_host = getattr(settings, 'DB_LOCAL_HOST', None)
            expected_port = getattr(settings, 'DB_LOCAL_PORT', None)
        else:
            expected_host = getattr(settings, 'DB_REMOTE_HOST', None)
            expected_port = getattr(settings, 'DB_REMOTE_PORT', None)
        
        self.assert_equal(db_config.get('HOST'), expected_host, "数据库主机配置不匹配")
        self.assert_equal(db_config.get('PORT'), expected_port, "数据库端口配置不匹配")
        
        self.result.details['environment_switch'] = 'success'
        self.logger.info("环境切换功能检查通过")

class DatabasePerformanceTest(BaseTest):
    def execute(self):
        self.logger.info("开始测试数据库性能")
        
        self._test_connection_speed()
        self._test_query_performance()
        self._test_concurrent_connections()
        
        self.logger.info("数据库性能测试完成")
    
    def _test_connection_speed(self):
        self.logger.info("测试数据库连接速度")
        
        from django.conf import settings
        
        db_config = settings.DATABASES.get('default', {})
        
        connection_times = []
        
        for i in range(5):
            start_time = time.time()
            
            try:
                connection = pymysql.connect(
                    host=db_config.get('HOST'),
                    port=db_config.get('PORT'),
                    user=db_config.get('USER'),
                    password=db_config.get('PASSWORD'),
                    database=db_config.get('NAME'),
                    connect_timeout=5
                )
                connection.close()
                
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
            
            except Exception as e:
                self.assert_true(False, f"数据库连接失败: {str(e)}")
        
        avg_connection_time = sum(connection_times) / len(connection_times)
        self.assert_true(
            avg_connection_time < 2.0,
            f"平均连接时间过长: {avg_connection_time:.2f}秒"
        )
        
        self.result.details['avg_connection_time'] = avg_connection_time
        self.result.details['connection_times'] = connection_times
        self.logger.info(f"平均连接时间: {avg_connection_time:.2f}秒")
    
    def _test_query_performance(self):
        self.logger.info("测试数据库查询性能")
        
        from django.conf import settings
        
        db_config = settings.DATABASES.get('default', {})
        
        try:
            connection = pymysql.connect(
                host=db_config.get('HOST'),
                port=db_config.get('PORT'),
                user=db_config.get('USER'),
                password=db_config.get('PASSWORD'),
                database=db_config.get('NAME')
            )
            
            with connection.cursor() as cursor:
                start_time = time.time()
                cursor.execute("SELECT COUNT(*) FROM db_sync_config")
                result = cursor.fetchone()
                query_time = time.time() - start_time
                
                self.assert_true(
                    query_time < 1.0,
                    f"查询时间过长: {query_time:.2f}秒"
                )
                
                self.result.details['query_time'] = query_time
                self.logger.info(f"查询时间: {query_time:.2f}秒")
            
            connection.close()
        
        except Exception as e:
            self.assert_true(False, f"查询性能测试失败: {str(e)}")
    
    def _test_concurrent_connections(self):
        self.logger.info("测试并发连接")
        
        from django.conf import settings
        import threading
        
        db_config = settings.DATABASES.get('default', {})
        connection_count = 10
        results = []
        
        def test_connection():
            try:
                connection = pymysql.connect(
                    host=db_config.get('HOST'),
                    port=db_config.get('PORT'),
                    user=db_config.get('USER'),
                    password=db_config.get('PASSWORD'),
                    database=db_config.get('NAME'),
                    connect_timeout=5
                )
                time.sleep(1)
                connection.close()
                results.append(True)
            except Exception as e:
                results.append(False)
        
        threads = []
        for i in range(connection_count):
            thread = threading.Thread(target=test_connection)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        success_count = sum(results)
        self.assert_true(
            success_count >= connection_count * 0.8,
            f"并发连接成功率过低: {success_count}/{connection_count}"
        )
        
        self.result.details['concurrent_connections'] = {
            'total': connection_count,
            'success': success_count,
            'rate': success_count / connection_count
        }
        self.logger.info(f"并发连接测试: {success_count}/{connection_count} 成功")
