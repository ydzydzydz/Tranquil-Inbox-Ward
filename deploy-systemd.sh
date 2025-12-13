#!/bin/bash

# Tranquil Inbox Ward Systemd 部署脚本
# 使用方法: sudo ./deploy-systemd.sh

set -e

echo "========================================"
echo "Tranquil Inbox Ward Systemd 部署脚本"
echo "========================================"

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    echo "请使用sudo运行此脚本: sudo $0"
    exit 1
fi

# 配置变量
APP_NAME="tranquil-inbox-ward"
INSTALL_DIR=$(pwd)
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"
LOG_DIR="/var/log/$APP_NAME"
VENV_NAME="Tranquil-Inbox-Ward"

echo "1. 检查当前目录..."
echo "   安装目录: $INSTALL_DIR"
echo "   项目名称: $APP_NAME"

echo "2. 创建日志目录..."
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

echo "3. 设置Python虚拟环境..."
if [ ! -d "$VENV_NAME" ]; then
    python3 -m venv "$VENV_NAME"
    echo "  已创建虚拟环境: $VENV_NAME"
else
    echo "  虚拟环境已存在: $VENV_NAME"
fi

echo "4. 安装Python依赖..."
source "$VENV_NAME/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo "5. 生成systemd服务文件..."
# 读取模板并替换路径
sed "s|{INSTALL_DIR}|$INSTALL_DIR|g; s|{VENV_NAME}|$VENV_NAME|g" "$INSTALL_DIR/tranquil-inbox-ward.service.template" > "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

echo "6. 检查Ollama服务..."
if ! systemctl is-active --quiet ollama 2>/dev/null; then
    echo "  警告: Ollama服务未运行。请确保已安装并启动Ollama:"
    echo "  - 安装: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  - 启动: systemctl start ollama"
    echo "  - 启用: systemctl enable ollama"
    echo "  - 拉取模型: ollama pull mollysama/rwkv-7-g1a:0.4b"
fi

echo "7. 重新加载systemd配置..."
systemctl daemon-reload

echo "8. 启用并启动服务..."
systemctl enable "$APP_NAME.service"
systemctl start "$APP_NAME.service"

echo "9. 检查服务状态..."
sleep 2
systemctl status "$APP_NAME.service" --no-pager

echo "========================================"
echo "部署完成!"
echo "========================================"
echo ""
echo "管理命令:"
echo "  sudo systemctl start $APP_NAME     # 启动服务"
echo "  sudo systemctl stop $APP_NAME      # 停止服务"
echo "  sudo systemctl restart $APP_NAME   # 重启服务"
echo "  sudo systemctl status $APP_NAME    # 查看状态"
echo "  sudo journalctl -u $APP_NAME -f    # 查看日志"
echo ""
echo "服务文件位置: $SERVICE_FILE"
echo "应用安装目录: $INSTALL_DIR"
echo "虚拟环境: $INSTALL_DIR/$VENV_NAME"
echo "日志目录: $LOG_DIR"
echo ""
echo "请确保:"
echo "1. Ollama服务正在运行 (systemctl status ollama)"
echo "2. 模型已下载 (ollama pull mollysama/rwkv-7-g1a:0.4b)"
echo "3. 检查应用日志: journalctl -u $APP_NAME -f"
echo "========================================"
