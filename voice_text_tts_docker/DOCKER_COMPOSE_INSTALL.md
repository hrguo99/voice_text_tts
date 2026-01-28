# Docker Compose 安装指南

## 检测当前状态

运行检测脚本：
```bash
./check-docker.sh
```

## 安装方法

### 方法 1: Docker Compose V2（推荐）

Docker Compose V2 是 Docker 的官方插件，使用 `docker compose` 命令（注意没有连字符）。

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y docker-compose-plugin
```

#### 验证安装
```bash
docker compose version
```

### 方法 2: Docker Compose V1

Docker Compose V1 是独立的 `docker-compose` 命令。

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y docker-compose
```

#### 从二进制文件安装（通用）
```bash
# 下载最新版本
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

### 方法 3: 使用 pip 安装

```bash
pip install docker-compose
```

## 验证安装

安装完成后，运行：
```bash
./check-docker.sh
```

应该显示类似：
```
✅ Docker 已安装
Docker version 28.2.2, build ...

✅ Docker Compose V2 已检测到
Docker Compose version v2.x.x
```

## 常见问题

### Q: 应该使用 V1 还是 V2？
A: 推荐使用 V2，因为它是 Docker 的官方发展方向，功能更强大。

### Q: 两个版本可以同时安装吗？
A: 可以，但建议只安装一个版本以避免冲突。我们的脚本会自动检测并使用可用的版本。

### Q: 如何卸载？
- V2: `sudo apt-get remove docker-compose-plugin`
- V1: `sudo apt-get remove docker-compose`

## 快速安装（推荐）

对于 Ubuntu/Debian 用户，直接运行：
```bash
sudo apt-get update && sudo apt-get install -y docker-compose-plugin
```

安装完成后即可使用脚本：
```bash
./start.sh
```
