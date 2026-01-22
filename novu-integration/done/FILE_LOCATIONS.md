# Novu集成文件位置说明

本文档说明Novu集成相关的所有文件位置。

## 📂 文件组织结构

### 1. 文档和Docker配置 (本目录)

```
langchainChatBot/novu-integration/
├── README.md                        # 主README(快速开始指南)
├── FILE_LOCATIONS.md               # 本文件(文件位置说明)
│
├── docker.novu/                    # Docker配置
│   ├── docker-compose.novu.yml    # Novu服务编排文件
│   ├── .env.novu.example          # 环境变量模板
│   └── mongo/
│       └── init-mongo.js          # MongoDB初始化脚本
│
└── docs/                           # 文档索引
    └── README.md                   # 文档导航

**完整文档位置:** `langchainChatBot/docs/done/notification/`
- NOVU_SELF_HOSTED_DESIGN.md      # 设计文档
- NOVU_IMPLEMENTATION_GUIDE.md    # 实施指南
- README_NOVU_INTEGRATION.md      # 项目总结
```

### 2. 后端实现代码 (在backend目录)

```
langchainChatBot/backend/api/
├── adapters/
│   ├── __init__.py
│   └── novu_adapter.py            # Novu API适配器 ⭐
│
├── services/
│   ├── __init__.py
│   └── notification_service.py    # 通知业务逻辑服务 ⭐
│
├── models/
│   ├── __init__.py
│   └── notification.py            # 通知数据模型 ⭐
│
├── controllers/
│   ├── __init__.py
│   └── notification_controller.py # 通知API控制器 ⭐
│
└── schemas/
    ├── __init__.py
    └── notification.py            # 请求/响应模型 ⭐
```

### 3. 前端实现代码 (在frontend目录)

```
langchainChatBot/frontend/src/
├── hooks/
│   └── useNovuNotifications.ts    # Novu通知React Hook ⭐
│
└── components/
    └── NotificationBell.tsx       # 通知铃铛组件 ⭐
```

## 🎯 快速定位指南

### 需要部署Novu服务?
👉 `langchainChatBot/novu-integration/docker.novu/docker-compose.novu.yml`

### 需要配置环境变量?
👉 `langchainChatBot/novu-integration/docker.novu/.env.novu.example`

### 需要了解系统设计?
👉 `langchainChatBot/docs/done/notification/NOVU_SELF_HOSTED_DESIGN.md`

### 需要实施部署步骤?
👉 `langchainChatBot/docs/done/notification/NOVU_IMPLEMENTATION_GUIDE.md`

### 需要修改后端API逻辑?
👉 `langchainChatBot/backend/api/services/notification_service.py`

### 需要修改Novu API调用?
👉 `langchainChatBot/backend/api/adapters/novu_adapter.py`

### 需要修改前端通知UI?
👉 `langchainChatBot/frontend/src/components/NotificationBell.tsx`

### 需要修改通知数据模型?
👉 `langchainChatBot/backend/api/models/notification.py`

## 📋 文件清单

### Docker配置文件 (3个)
- ✅ `docker.novu/docker-compose.novu.yml` - Novu服务编排
- ✅ `docker.novu/.env.novu.example` - 环境变量模板
- ✅ `docker.novu/mongo/init-mongo.js` - MongoDB初始化

### 文档文件 (5个)
- ✅ `README.md` - 主README
- ✅ `FILE_LOCATIONS.md` - 本文件
- ✅ `docs/README.md` - 文档索引
- ✅ `../docs/done/notification/NOVU_SELF_HOSTED_DESIGN.md` - 设计文档(约1000行)
- ✅ `../docs/done/notification/NOVU_IMPLEMENTATION_GUIDE.md` - 实施指南(约1100行)
- ✅ `../docs/done/notification/README_NOVU_INTEGRATION.md` - 项目总结(约450行)

### 后端代码文件 (5个)
- ✅ `backend/api/adapters/novu_adapter.py` - Novu适配器(约600行)
- ✅ `backend/api/services/notification_service.py` - 通知服务(约480行)
- ✅ `backend/api/models/notification.py` - 数据模型(约120行)
- ✅ `backend/api/controllers/notification_controller.py` - API控制器(约200行)
- ✅ `backend/api/schemas/notification.py` - Schemas(约60行)

### 前端代码文件 (2个)
- ✅ `frontend/src/hooks/useNovuNotifications.ts` - React Hook(约400行)
- ✅ `frontend/src/components/NotificationBell.tsx` - 通知组件(约300行)

**总计:** 15个文件,约4700行代码和文档

## 🔄 文件关系图

```
novu-integration/docker.novu/
  └─ docker-compose.novu.yml ──┐
                               │
                               ├─> 启动Novu服务
                               │
                               ↓
backend/api/adapters/
  └─ novu_adapter.py ─────────┐
                              │
                              ├─> 调用Novu API
                              │
                              ↓
backend/api/services/
  └─ notification_service.py ─┐
                              │
                              ├─> 业务逻辑处理
                              │
                              ↓
backend/api/controllers/
  └─ notification_controller.py ─┐
                                 │
                                 ├─> 提供REST API
                                 │
                                 ↓
frontend/src/hooks/
  └─ useNovuNotifications.ts ───┐
                                │
                                ├─> 调用后端API
                                │
                                ↓
frontend/src/components/
  └─ NotificationBell.tsx ──────> 显示通知UI
```

## 💡 使用建议

### 开发阶段
1. 先阅读 `docs/NOVU_SELF_HOSTED_DESIGN.md` 了解架构
2. 按照 `docs/NOVU_IMPLEMENTATION_GUIDE.md` 部署测试环境
3. 修改后端代码时,从 `services/` 开始,不要直接修改 `adapters/`
4. 修改前端UI时,只需修改 `components/NotificationBell.tsx`

### 生产部署
1. 复制 `docker.novu/.env.novu.example` 为 `.env.novu`
2. 修改所有密钥和密码
3. 运行 `docker-compose -f docker.novu/docker-compose.novu.yml up -d`
4. 按照实施指南完成后端和前端配置

### 维护阶段
1. 查看 `docs/NOVU_IMPLEMENTATION_GUIDE.md` 第10章故障排除
2. 检查 `docker/` 目录下的日志
3. 参考 `docs/NOVU_SELF_HOSTED_DESIGN.md` 理解系统行为

## 🔗 相关链接

- **Novu官方文档:** https://docs.novu.co
- **Novu GitHub:** https://github.com/novuhq/novu
- **项目主README:** `../README.md`

---

**创建日期:** 2026-01-21  
**维护者:** AI Assistant  
**版本:** 1.0
