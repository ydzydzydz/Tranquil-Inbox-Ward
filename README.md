# Tranquil-Inbox-Ward

静域信驿（Tranquil Inbox Ward），专为 pmail 设计的关键词增强型垃圾邮件分类服务（规则 + LLM 混合）。

## 仓库
https://github.com/AXFOX/Tranquil-Inbox-Ward

## 说明（部署与依赖）
- 本项目使用本地 Ollama 模型服务进行 LLM 推理，默认模型：mollysama/rwkv-7-g1a:0.4b
## Ollama（本地模型服务）
- 请先参考 Ollama 官方文档安装 Ollama 并运行服务。
- 下载/拉取模型（示例）：
```bash
ollama pull mollysama/rwkv-7-g1a:0.4b
```
- 启动 Ollama 服务（示例）：
```bash
ollama serve
```
- 默认应用连接地址（可通过.env或环境变量覆盖）：`http://127.0.0.1:11434/api/generate`

## 环境变量（可选）
```bash
export OLLAMA_MODEL="mollysama/rwkv-7-g1a:0.4b"
export OLLAMA_API_URL="http://127.0.0.1:11434/api/generate"
export SERVER_HOST="0.0.0.0"
export SERVER_PORT="8501"
```

## 启动服务
```bash
# 开发或调试
python app.py

# 生产（示例使用 gunicorn）
gunicorn -w 4 -b 0.0.0.0:8501 app:app
```
## Systemd 部署（生产环境推荐）

### 1. 准备工作
确保已安装：
- Python 3.8+
- Ollama（用于LLM推理）
- 已拉取模型：`mollysama/rwkv-7-g1a:0.4b`

### 2. 克隆仓库
```bash
git clone https://github.com/AXFOX/Tranquil-Inbox-Ward.git
cd Tranquil-Inbox-Ward
```

### 3. 使用部署脚本
```bash
# 给脚本执行权限
chmod +x deploy-systemd.sh

# 运行部署脚本（需要sudo权限）
sudo ./deploy-systemd.sh
```

### 4. 管理服务
```bash
# 查看服务状态
sudo systemctl status tranquil-inbox-ward

# 启动服务
sudo systemctl start tranquil-inbox-ward

# 停止服务
sudo systemctl stop tranquil-inbox-ward

# 重启服务
sudo systemctl restart tranquil-inbox-ward

# 查看日志
sudo journalctl -u tranquil-inbox-ward -f
```

### 5. 服务文件说明
- **服务文件**: `/etc/systemd/system/tranquil-inbox-ward.service`
- **安装目录**: 当前克隆的目录
- **虚拟环境**: `.Tranquil-Inbox-Ward/`（项目根目录下相同文件名的隐藏文件）
- **日志目录**: `/var/log/tranquil-inbox-ward/`

### 6. 注意事项
1. 部署脚本会在当前目录创建Python虚拟环境
2. 服务使用当前用户运行，无需创建专用系统用户
3. 确保Ollama服务已启动：`systemctl status ollama`
4. 如需修改服务配置，编辑服务文件后运行：`sudo systemctl daemon-reload && sudo systemctl restart tranquil-inbox-ward`

## API 测试

项目提供了 `api_test.sh` 脚本，用于方便地测试API。

### 脚本功能
- 测试单个文本内容
- 从文件批量测试多行文本
- 交互式测试模式
- 彩色输出和 JSON 格式化（如果安装了 `jq`）

### 使用方法

#### 1. 测试单个文本
```bash
./api_test.sh "这是一条测试消息"
```

#### 2. 从文件批量测试
```bash
./api_test.sh -f test_cases.txt
```

#### 3. 交互模式
```bash
./api_test.sh -i
```

#### 4. 显示帮助
```bash
./api_test.sh -h
```

### 依赖要求
- `curl`: 用于发送 HTTP 请求
- `jq` (可选): 用于格式化 JSON 输出，如果未安装则输出原始 JSON

### 示例输出
```bash
$ ./api_test.sh "今天天气真好"
测试内容: 今天天气真好
API URL: http://localhost:8501/v1/models/emotion_model:predict
----------------------------------------
{
  "predictions": [
    {
      "label": "positive",
      "score": 0.95
    }
  ]
}
```

## 其它
- 源代码主文件：`app.py`  
- 如需额外的容器化部署示例，可在仓库中补充 `Dockerfile`
- 已提供systemd部署脚本和模板文件
- =-= So，欢迎PR
