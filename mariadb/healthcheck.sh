#!/bin/bash
# MariaDB 健康检查脚本
mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD}"