# Novu集成快速开始指南

5分钟快速启动Novu通知系统!

## 🚀 快速启动 (3步)

### 步骤1: 启动Novu服务 (2分钟)

```bash
cd langchainChatBot/novu-integration/docker.novu

# 复制环境变量
cp .env.novu.example .env.novu

# 生成密钥并填入.env.novu
openssl rand -base64 32  # JWT密钥
openssl rand -hex 16     # 加密密钥(32字符)

# 启动服务
docker-compose -f docker-compose.novu.yml up -d

# 等待服务就绪(约30秒)
docker-compose -f docker-compose.novu.yml logs -f novu-api
```

### 步骤2: 配置Novu (2分钟)

1. 打开浏览器访问: `http://localhost:4200`
2. 创建账户(任意邮箱和密码)
3. 登录后,点击右上角设置图标
4. 进入 "API Keys" 页面
5. 复制 "API Key" (以 `novu_` 开头)
6. 复制 "Application Identifier"

### 步骤3: 配置应用 (1分钟)

**后端配置:**

```bash
cd ../../backend

# 添加到.env文件
echo "NOVU_API_KEY=novu_xxxxxx" >> .env
echo "NOVU_API_URL=http://localhost:3000" >> .env
```

**前端配置:**

```bash
cd ../frontend

# 添加到.env.local文件
echo "NEXT_PUBLIC_NOVU_APP_ID=your_app_id" >> .env.local
echo "NEXT_PUBLIC_NOVU_API_URL=http://localhost:3000" >> .env.local
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" >> .env.local
```

## ✅ 验证安装

### 检查Novu服务

```bash
# 检查所有服务是否运行
docker-compose -f langchainChatBot/novu-integration/docker.novu/docker-compose.novu.yml ps

# 应该看到5个服务都是"Up"状态:
# - novu-api
# - novu-ws
# - novu-worker
# - novu-web
# - novu-mongo
# - novu-redis
```

### 测试API连接

```bash
# 测试Novu API
curl http://localhost:3000/v1/health-check

# 应该返回: {"status":"ok"}
```

### 测试WebSocket

```bash
# 测试WebSocket服务
curl http://localhost:3002/health-check

# 应该返回: {"status":"ok"}
```

## 📝 下一步

### 创建第一个工作流

1. 登录Novu Dashboard: `http://localhost:4200`
2. 点击左侧 "Workflows"
3. 点击 "Create Workflow"
4. 选择 "Blank Workflow"
5. 设置:
   - Name: `workflow-approval`
   - Identifier: `workflow-approval`
6. 点击 "Add Step" → 选择 "In-App"
7. 配置内容: `{{content}}`
8. 保存

### 发送测试通知

```bash
cd langchainChatBot/backend

# 运行测试脚本
python scripts/test_novu_integration.py
```

### 启动应用

```bash
# 启动后端
cd langchainChatBot/backend
uvicorn main:app --reload

# 启动前端(新终端)
cd langchainChatBot/frontend
npm run dev
```

访问 `http://localhost:3001` 查看通知铃铛!

## 🐛 常见问题

### 问题1: Docker服务无法启动

**解决方案:**

```bash
# 检查端口占用
netstat -ano | findstr "3000"
netstat -ano | findstr "27017"

# 停止并重启
docker-compose -f docker-compose.novu.yml down
docker-compose -f docker-compose.novu.yml up -d
```

### 问题2: 无法访问Dashboard

**解决方案:**

```bash
# 检查novu-web服务
docker logs novu-web

# 重启服务
docker-compose -f docker-compose.novu.yml restart novu-web
```

### 问题3: API Key无效

**解决方案:**

1. 确认复制了完整的API Key(包括 `novu_` 前缀)
2. 检查 `.env` 文件中没有多余的空格或引号
3. 重启后端服务

## 📚 详细文档

- **完整实施指南:** `../docs/done/notification/NOVU_IMPLEMENTATION_GUIDE.md`
- **系统设计文档:** `../docs/done/notification/NOVU_SELF_HOSTED_DESIGN.md`
- **文件位置说明:** `FILE_LOCATIONS.md`
- **项目总结:** `../docs/done/notification/README_NOVU_INTEGRATION.md`

## 💬 获取帮助

- 查看故障排除: `../docs/done/notification/NOVU_IMPLEMENTATION_GUIDE.md` 第10章
- Novu官方文档: https://docs.novu.co
- Novu Discord: https://discord.gg/novu

---

**预计完成时间:** 5分钟  
**难度:** ⭐⭐☆☆☆ (简单)  
**最后更新:** 2026-01-21
