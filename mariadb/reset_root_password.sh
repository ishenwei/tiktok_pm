#!/bin/bash
# MariaDB root 密码重置脚本 (改进版)
# 此脚本使用 --skip-grant-tables 模式启动 MariaDB 来重置 root 密码

echo "开始重置 MariaDB root 密码..."

# 1. 停止 MariaDB 容器
echo "1. 停止 MariaDB 容器..."
sudo docker compose stop mariadb

# 2. 启动容器并跳过权限检查
echo "2. 启动容器并跳过权限检查..."
sudo docker run --rm -d \
  --name mariadb_reset \
  -v tiktok_pm_mariadb_data:/var/lib/mysql \
  mariadb:10.11 \
  --skip-grant-tables \
  --skip-networking \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci

# 等待容器启动
echo "3. 等待容器启动..."
sleep 20

# 3. 重置 root 密码
echo "4. 重置 root 密码..."
sudo docker exec mariadb_reset mysql -u root -e "FLUSH PRIVILEGES;"
sudo docker exec mariadb_reset mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '!Abcde12345';"
sudo docker exec mariadb_reset mysql -u root -e "ALTER USER 'root'@'%' IDENTIFIED BY '!Abcde12345';"
sudo docker exec mariadb_reset mysql -u root -e "FLUSH PRIVILEGES;"

# 4. 停止临时容器
echo "5. 停止临时容器..."
sudo docker stop mariadb_reset

# 5. 重新启动 MariaDB 容器
echo "6. 重新启动 MariaDB 容器..."
sudo docker compose up -d mariadb

echo "密码重置完成！"
echo "等待数据库启动..."
sleep 15

echo "检查连接..."
sudo docker exec tiktok_pm_mariadb mysqladmin ping -h localhost -u root -p'!Abcde12345'

if [ $? -eq 0 ]; then
    echo "✓ 密码重置成功！"
else
    echo "✗ 密码重置失败，请检查日志"
fi