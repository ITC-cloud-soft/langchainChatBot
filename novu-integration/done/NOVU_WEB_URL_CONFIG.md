# Novu Web URL 配置说明

**问题**: Novu Web 是预构建的 Docker 镜像,`REACT_APP_*` 环境变量在构建时固化,运行时无法修改。

## 当前状态

### 配置文件
- `docker-compose.novu.yml` 中设置了 `env_file: .env.novu`
- `environment` 部分的变量会**覆盖** `env_file` 的设置

### 问题原因
```yaml
environment:
  REACT_APP_API_URL: ${REACT_APP_API_URL:-http://localhost:3000}
  REACT_APP_WS_URL: ${REACT_APP_WS_URL:-http://localhost:3002}
```

这里的 `${REACT_APP_API_URL:-http://localhost:3000}` 语法:
- 如果环境变量 `REACT_APP_API_URL` 存在,使用其值
- 如果不存在,使用默认值 `http://localhost:3000`

**但是**: 即使 `.env.novu` 文件中设置了这些变量,Docker Compose 在解析 `environment` 时,会从**宿主机的环境变量**中查找,而不是从 `env_file` 中查找。

## 解决方案

### 方案 1: 移除 environment 中的重复定义 (推荐)

修改 `docker-compose.novu.yml`:

```yaml
novu-web:
  image: ghcr.io/novuhq/novu/web:0.24.0
  container_name: novu-web
  env_file:
    - .env.novu
  environment:
    TZ: Asia/Tokyo
  ports:
    - "4200:4200"
```

**优点**: 所有配置集中在 `.env.novu` 文件中
**缺点**: Novu Web 预构建镜像可能不支持运行时修改这些 URL

### 方案 2: 在宿主机设置环境变量

在启动 Docker Compose 前设置环境变量:

**Windows PowerShell:**
```powershell
$env:REACT_APP_API_URL="http://192.168.1.78:3000"
$env:REACT_APP_WS_URL="http://192.168.1.78:3002"
docker-compose -f docker-compose.novu.yml up -d
```

**Linux/Mac:**
```bash
export REACT_APP_API_URL=http://192.168.1.78:3000
export REACT_APP_WS_URL=http://192.168.1.78:3002
docker-compose -f docker-compose.novu.yml up -d
```

### 方案 3: 直接在 docker-compose.yml 中硬编码

```yaml
environment:
  TZ: Asia/Tokyo
  REACT_APP_API_URL: http://192.168.1.78:3000
  REACT_APP_WS_URL: http://192.168.1.78:3002
  REACT_APP_ENVIRONMENT: production
```

**优点**: 明确且简单
**缺点**: 
- 需要修改 docker-compose.yml 文件
- 切换环境时需要手动修改

### 方案 4: 使用 Nginx 反向代理 (最佳方案)

创建一个 Nginx 反向代理,让 Novu Web 使用相对路径:

```yaml
novu-web:
  environment:
    REACT_APP_API_URL: /novu-api
    REACT_APP_WS_URL: /novu-ws
```

然后在 Nginx 中配置:
```nginx
location /novu-api {
    proxy_pass http://novu-api:3000;
}

location /novu-ws {
    proxy_pass http://novu-ws:3002;
}
```

**优点**: 
- 支持任意访问方式 (localhost/IP)
- 不需要修改 URL 配置
- 更安全

**缺点**: 需要额外的 Nginx 配置

## 当前推荐配置

### 1. 修改 docker-compose.novu.yml

```yaml
novu-web:
  image: ghcr.io/novuhq/novu/web:0.24.0
  container_name: novu-web
  environment:
    TZ: Asia/Tokyo
    # 直接硬编码 URL,根据主要使用场景选择
    # 本机访问使用 localhost
    REACT_APP_API_URL: http://localhost:3000
    REACT_APP_WS_URL: http://localhost:3002
    # 局域网访问使用 IP
    # REACT_APP_API_URL: http://192.168.1.78:3000
    # REACT_APP_WS_URL: http://192.168.1.78:3002
    REACT_APP_ENVIRONMENT: production
  ports:
    - "4200:4200"
```

### 2. 访问方式

**使用 localhost 配置时:**
- ✅ 访问 `http://localhost:4200` - 正常
- ❌ 访问 `http://192.168.1.78:4200` - CORS 错误

**使用 192.168.1.78 配置时:**
- ❌ 访问 `http://localhost:4200` - CORS 错误
- ✅ 访问 `http://192.168.1.78:4200` - 正常

## 验证配置是否生效

```bash
# 检查容器内的环境变量
docker exec novu-web printenv | findstr REACT_APP

# 应该看到:
# REACT_APP_API_URL=http://192.168.1.78:3000
# REACT_APP_WS_URL=http://192.168.1.78:3002
```

## 重要提示

⚠️ **Novu Web 是预构建镜像,运行时设置 `REACT_APP_*` 可能不生效**

如果运行时设置无效,需要:
1. 自定义构建 Novu Web 镜像
2. 或使用 Nginx 反向代理方案
3. 或接受只能使用一种访问方式的限制

---

**最后更新**: 2026-01-22  
**状态**: ⚠️ 需要验证预构建镜像是否支持运行时环境变量
