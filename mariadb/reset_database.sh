#!/bin/bash
# MariaDB 数据库重置脚本
# 此脚本会删除并重新创建数据库卷（会丢失所有数据）

echo "警告：此操作将删除所有数据库数据！"
echo "请确认您已备份重要数据。"
read -p "是否继续？(y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "操作已取消。"
    exit 0
fi

echo "开始重置 MariaDB 数据库..."

# 1. 停止并删除容器
echo "1. 停止并删除容器..."
sudo docker compose down

# 2. 删除数据库卷
echo "2. 删除数据库卷..."
sudo docker volume rm tiktok_pm_mariadb_data

# 3. 重新启动容器
echo "3. 重新启动容器..."
sudo docker compose up -d

echo "等待数据库初始化..."
sleep 30

echo "检查连接..."
sudo docker exec tiktok_pm_mariadb mysqladmin ping -h localhost -u root -p'!Abcde12345'

if [ $? -eq 0 ]; then
    echo "✓ 数据库重置成功！"
    echo "数据库已使用新密码初始化。"
else
    echo "✗ 数据库重置失败，请检查日志"
fi