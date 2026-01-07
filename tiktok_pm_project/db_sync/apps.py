from django.apps import AppConfig


class DbSyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tiktok_pm_project.db_sync'
    verbose_name = '数据库同步'
