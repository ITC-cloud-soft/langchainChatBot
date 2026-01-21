# 自托管Novu集成设计文档

## 目录

1. [概要](#概要)
2. [系统架构设计](#系统架构设计)
3. [技术栈](#技术栈)
4. [数据流设计](#数据流设计)
5. [核心组件设计](#核心组件设计)
6. [API设计](#api设计)
7. [数据库设计](#数据库设计)
8. [安全设计](#安全设计)
9. [性能优化](#性能优化)
10. [部署架构](#部署架构)

---

## 概要

### 项目目标

使用自托管Novu完全替代Dify现有的消息通知系统,实现以下核心功能:

✅ **功能覆盖:**
- 从数据库读取并显示通知消息
- 点击通知生成动态表单和按钮
- 工作流审批交互
- 实时通知推送(WebSocket)
- 跨设备同步
- 通知分类和过滤
- 未读计数和标记已读

✅ **技术优势:**
- 完全开源免费
- 数据完全掌控
- 高性能实时推送
- 易于扩展和维护

### 项目范围

**包含:**
- Novu自托管服务部署
- 后端API适配层开发
- 前端通知组件重构
- 数据迁移方案
- 测试和文档

**不包含:**
- Email/SMS等外部渠道(仅应用内通知)
- 现有业务逻辑修改
- 其他系统功能变更

---

## 系统架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (React)                         │
├─────────────────────────────────────────────────────────────┤
│  NotificationBell Component (自定义UI)                       │
│  ├─ useNovuNotifications Hook                               │
│  ├─ WebSocket实时监听                                        │
│  └─ 动态表单渲染器                                           │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    后端API层 (Python/FastAPI)                │
├─────────────────────────────────────────────────────────────┤
│  NotificationService (适配层)                                │
│  ├─ NovuAdapter - 与Novu API交互                            │
│  ├─ NotificationRepository - 本地数据库操作                  │
│  └─ WorkflowHandler - 工作流逻辑处理                         │
└─────────────────────────────────────────────────────────────┘
                            ↕ REST API
┌─────────────────────────────────────────────────────────────┐
│                   Novu自托管服务 (Docker)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Novu API    │  │  Novu WS     │  │  Novu Web    │      │
│  │  (3000)      │  │  (3002)      │  │  (4200)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↕                 ↕                                  │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  MongoDB     │  │  Redis       │                        │
│  │  (27017)     │  │  (6379)      │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   本地数据库 (PostgreSQL)                     │
├─────────────────────────────────────────────────────────────┤
│  notifications表 (审计日志/备份)                             │
│  ├─ id, tenant_id, chatbot_id                               │
│  ├─ novu_notification_id (关联Novu)                         │
│  ├─ title, content, category, payload                       │
│  └─ status, created_at, read_at                             │
└─────────────────────────────────────────────────────────────┘
```

### 架构特点

1. **双数据源策略**
   - Novu作为主要通知系统
   - PostgreSQL保留审计日志和备份
   - 通过novu_notification_id关联

2. **适配层模式**
   - 保持现有API接口不变
   - 内部调用转发到Novu
   - 平滑迁移,最小化代码改动

3. **Headless前端**
   - 使用Novu Headless SDK
   - 保留现有UI设计
   - 完全自定义渲染逻辑

---

## 技术栈

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18+ | UI框架 |
| TypeScript | 5+ | 类型安全 |
| @novu/headless | latest | Novu Headless SDK |
| socket.io-client | 4+ | WebSocket客户端 |
| Ant Design | 5+ | UI组件库 |
| React Hook Form | 7+ | 动态表单处理 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 后端语言 |
| FastAPI | 0.104+ | Web框架 |
| novu | 1.6+ | Novu Python SDK |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 15+ | 数据库 |
| Redis | 7+ | 缓存 |

### Novu服务栈

| 服务 | 镜像 | 端口 | 用途 |
|------|------|------|------|
| novu-api | ghcr.io/novuhq/novu/api | 3000 | API服务 |
| novu-ws | ghcr.io/novuhq/novu/ws | 3002 | WebSocket服务 |
| novu-web | ghcr.io/novuhq/novu/web | 4200 | 管理控制台 |
| novu-worker | ghcr.io/novuhq/novu/worker | - | 后台任务处理 |
| mongodb | mongo:6 | 27017 | Novu数据存储 |
| redis | redis:alpine | 6379 | 缓存和队列 |

---

## 数据流设计

### 1. 发送通知流程

```
┌──────────────┐
│ 业务触发     │ (例: 工作流审批请求)
└──────┬───────┘
       ↓
┌──────────────────────────────────────────────────┐
│ NotificationService.send_workflow_approval()     │
│ ├─ 1. 创建本地数据库记录                          │
│ ├─ 2. 调用NovuAdapter.trigger()                 │
│ └─ 3. 保存novu_notification_id到本地             │
└──────┬───────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│ Novu API (POST /events/trigger)                 │
│ ├─ workflow: "workflow-approval"                │
│ ├─ subscriberId: "user-123"                     │
│ └─ payload: {workflowData, actions, formSchema} │
└──────┬───────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│ Novu处理引擎                                      │
│ ├─ 1. 工作流匹配                                  │
│ ├─ 2. 创建通知记录                                │
│ ├─ 3. 存储到MongoDB                              │
│ └─ 4. 推送到WebSocket                            │
└──────┬───────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│ 前端实时接收 (WebSocket)                          │
│ ├─ 1. socket.on('notification_received')        │
│ ├─ 2. 更新未读计数                                │
│ ├─ 3. 显示通知提示                                │
│ └─ 4. 更新通知列表                                │
└──────────────────────────────────────────────────┘
```

### 2. 点击通知生成表单流程

```
┌──────────────┐
│ 用户点击通知  │
└──────┬───────┘
       ↓
┌──────────────────────────────────────────────────┐
│ handleNotificationClick(notification)            │
│ ├─ 1. 解析payload.formSchema                    │
│ ├─ 2. 解析payload.actions                       │
│ └─ 3. 解析payload.workflowData                  │
└──────┬───────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│ DynamicFormRenderer                              │
│ ├─ 根据formSchema.fields生成表单字段             │
│ │  ├─ textarea → TextArea组件                   │
│ │  ├─ number → InputNumber组件                  │
│ │  └─ select → Select组件                       │
│ └─ 根据actions生成操作按钮                        │
│    ├─ approve → 承認按钮                         │
│    └─ reject → 否認按钮                          │
└──────┬───────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│ 创建聊天会话并显示表单                             │
│ ├─ 1. 触发createNewChat事件                     │
│ ├─ 2. 创建新的chat session                      │
│ ├─ 3. 渲染带表单的bot消息                         │
│ └─ 4. 标记通知为已读                              │
└──────────────────────────────────────────────────┘
```

### 3. 提交表单流程

```
┌──────────────┐
│ 用户提交表单  │ (点击承認/否認)
└──────┬───────┘
       ↓
┌──────────────────────────────────────────────────┐
│ handleFormSubmit(action, formData)               │
│ ├─ 1. 验证表单数据                                │
│ ├─ 2. 构造提交payload                            │
│ └─ 3. 调用业务API                                │
└──────┬───────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│ WorkflowService.handle_approval()                │
│ ├─ 1. 处理审批逻辑                                │
│ ├─ 2. 更新工作流状态                              │
│ ├─ 3. 发送结果通知给申请人                        │
│ └─ 4. 标记原通知为已处理                          │
└──────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│ 前端显示结果                                      │
│ ├─ 1. 显示成功/失败消息                           │
│ ├─ 2. 关闭表单对话框                              │
│ └─ 3. 刷新通知列表                                │
└──────────────────────────────────────────────────┘
```

---

## 核心组件设计

### 后端组件

#### 1. NovuAdapter (Novu适配器)

**职责:** 封装Novu API调用,提供统一接口

**主要方法:**

```python
class NovuAdapter:
    """Novu API适配器"""
    
    def __init__(self, api_key: str, api_url: str):
        """初始化Novu客户端"""
        
    def create_subscriber(self, user_id: str, user_data: dict) -> dict:
        """创建/更新订阅者"""
        
    def trigger_workflow(
        self, 
        workflow_id: str, 
        subscriber_id: str, 
        payload: dict
    ) -> str:
        """触发工作流,返回notification_id"""
        
    def get_notifications(
        self, 
        subscriber_id: str, 
        page: int = 0, 
        limit: int = 10
    ) -> List[dict]:
        """获取通知列表"""
        
    def mark_as_read(self, notification_id: str) -> bool:
        """标记通知为已读"""
        
    def mark_as_seen(self, notification_id: str) -> bool:
        """标记通知为已查看"""
        
    def delete_notification(self, notification_id: str) -> bool:
        """删除通知"""
        
    def get_unread_count(self, subscriber_id: str) -> int:
        """获取未读计数"""
```

#### 2. NotificationService (通知服务)

**职责:** 业务逻辑处理,协调Novu和本地数据库

**主要方法:**

```python
class NotificationService:
    """通知服务 - 业务逻辑层"""
    
    def __init__(self, novu_adapter: NovuAdapter, db_session: Session):
        """初始化服务"""
        
    def send_workflow_approval(
        self, 
        receiver_id: str, 
        workflow_data: dict
    ) -> Notification:
        """发送工作流审批通知"""
        # 1. 创建本地记录
        # 2. 触发Novu工作流
        # 3. 保存novu_notification_id
        # 4. 返回通知对象
        
    def send_system_notification(
        self, 
        receiver_id: str, 
        title: str, 
        content: str
    ) -> Notification:
        """发送系统通知"""
        
    def list_notifications(
        self, 
        user_id: str, 
        unread_only: bool = False
    ) -> List[Notification]:
        """获取通知列表 (从Novu)"""
        
    def get_unread_count(self, user_id: str) -> int:
        """获取未读数量"""
        
    def mark_read(self, user_id: str, notification_id: str) -> bool:
        """标记已读"""
        
    def delete(self, user_id: str, notification_id: str) -> bool:
        """删除通知"""
        
    def sync_to_local_db(self, novu_notification: dict) -> Notification:
        """同步Novu通知到本地数据库(审计)"""
```

#### 3. WorkflowHandler (工作流处理器)

**职责:** 处理工作流相关的业务逻辑

**主要方法:**

```python
class WorkflowHandler:
    """工作流处理器"""
    
    def handle_approval_request(
        self, 
        workflow_data: dict, 
        approver_id: str
    ) -> str:
        """处理审批请求,返回notification_id"""
        
    def handle_approval_response(
        self, 
        notification_id: str, 
        action: str, 
        form_data: dict
    ) -> dict:
        """处理审批响应"""
        
    def build_approval_payload(self, workflow_data: dict) -> dict:
        """构建审批通知的payload"""
        # 返回包含formSchema和actions的完整payload
```

### 前端组件

#### 1. useNovuNotifications Hook

**职责:** 封装Novu Headless逻辑,提供React Hook

```typescript
interface UseNovuNotificationsOptions {
  subscriberId: string;
  applicationIdentifier: string;
  backendUrl?: string;
  socketUrl?: string;
}

interface UseNovuNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  error: Error | null;
  markAsRead: (notificationId: string) => Promise<void>;
  markAsSeen: (notificationId: string) => Promise<void>;
  remove: (notificationId: string) => Promise<void>;
  fetchMore: () => Promise<void>;
  refetch: () => Promise<void>;
}

function useNovuNotifications(
  options: UseNovuNotificationsOptions
): UseNovuNotificationsReturn {
  // 实现逻辑
}
```

#### 2. NotificationBell Component

**职责:** 通知铃铛UI组件

```typescript
interface NotificationBellProps {
  userId: string;
  onNotificationClick?: (notification: Notification) => void;
}

function NotificationBell({ userId, onNotificationClick }: NotificationBellProps) {
  const { notifications, unreadCount, markAsRead, remove } = useNovuNotifications({
    subscriberId: userId,
    applicationIdentifier: process.env.NEXT_PUBLIC_NOVU_APP_ID!,
  });
  
  // 渲染逻辑
}
```

#### 3. DynamicFormRenderer Component

**职责:** 根据formSchema动态渲染表单

```typescript
interface FormSchema {
  type: string;
  fields: FormField[];
  actions: FormAction[];
}

interface FormField {
  id: string;
  type: 'text' | 'textarea' | 'number' | 'select' | 'date';
  label: string;
  placeholder?: string;
  required?: boolean;
  options?: Array<{ label: string; value: any }>;
}

interface FormAction {
  id: string;
  label: string;
  type: 'primary' | 'secondary' | 'danger';
}

interface DynamicFormRendererProps {
  formSchema: FormSchema;
  workflowData: any;
  onSubmit: (action: string, formData: any) => Promise<void>;
  onCancel: () => void;
}

function DynamicFormRenderer({
  formSchema,
  workflowData,
  onSubmit,
  onCancel
}: DynamicFormRendererProps) {
  // 动态渲染逻辑
}
```

---

## API设计

### 后端API端点

#### 1. 通知管理API

```python
# GET /api/notifications
# 获取通知列表
@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    page: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的通知列表"""
    pass

# GET /api/notifications/unread-count
# 获取未读数量
@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """获取未读通知数量"""
    pass

# POST /api/notifications/{notification_id}/read
# 标记已读
@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """标记通知为已读"""
    pass

# DELETE /api/notifications/{notification_id}
# 删除通知
@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除通知"""
    pass
```

#### 2. 工作流API

```python
# POST /api/workflow/approval/send
# 发送审批请求
@router.post("/workflow/approval/send")
async def send_approval_request(
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user)
):
    """发送工作流审批请求"""
    pass

# POST /api/workflow/approval/respond
# 响应审批请求
@router.post("/workflow/approval/respond")
async def respond_to_approval(
    response: ApprovalResponse,
    current_user: User = Depends(get_current_user)
):
    """响应工作流审批"""
    pass
```

#### 3. Novu管理API

```python
# POST /api/novu/subscribers/sync
# 同步用户到Novu
@router.post("/novu/subscribers/sync")
async def sync_subscribers(
    current_user: User = Depends(get_current_user)
):
    """同步所有用户到Novu订阅者"""
    pass

# GET /api/novu/health
# 健康检查
@router.get("/novu/health")
async def novu_health_check():
    """检查Novu服务健康状态"""
    pass
```

### Novu工作流定义

#### workflow-approval (工作流审批)

```json
{
  "name": "workflow-approval",
  "description": "工作流审批通知",
  "steps": [
    {
      "type": "in_app",
      "template": {
        "content": "{{content}}",
        "cta": {
          "type": "redirect",
          "data": {
            "url": "/chatbot"
          },
          "action": {
            "buttons": [
              {
                "type": "primary",
                "content": "{{approveLabel}}"
              },
              {
                "type": "secondary",
                "content": "{{rejectLabel}}"
              }
            ]
          }
        }
      }
    }
  ]
}
```

---

## 数据库设计

### 本地PostgreSQL表结构

#### notifications表 (保留用于审计)

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    chatbot_id UUID,
    connection_id UUID,
    
    -- Novu关联
    novu_notification_id VARCHAR(255) UNIQUE,
    novu_subscriber_id VARCHAR(255) NOT NULL,
    
    -- 用户信息
    sender_id UUID,
    receiver_id UUID NOT NULL,
    
    -- 通知内容
    title VARCHAR(255) NOT NULL,
    content TEXT,
    category VARCHAR(50),
    payload JSONB,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'sent',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    deleted_at TIMESTAMP,
    
    -- 索引
    INDEX idx_receiver_status (receiver_id, status),
    INDEX idx_novu_notification (novu_notification_id),
    INDEX idx_created_at (created_at DESC)
);
```

#### notification_sync_log表 (同步日志)

```sql
CREATE TABLE notification_sync_log (
    id SERIAL PRIMARY KEY,
    novu_notification_id VARCHAR(255) NOT NULL,
    local_notification_id UUID,
    sync_direction VARCHAR(20), -- 'to_novu' or 'from_novu'
    sync_status VARCHAR(20), -- 'success' or 'failed'
    error_message TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_novu_id (novu_notification_id),
    INDEX idx_sync_status (sync_status, synced_at)
);
```

### Novu MongoDB数据结构

Novu自动管理,主要集合:

- **notifications** - 通知记录
- **subscribers** - 订阅者(用户)
- **messages** - 消息记录
- **jobs** - 任务队列

---

## 安全设计

### 1. 认证和授权

```python
# JWT Token验证
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """验证JWT token并返回当前用户"""
    pass

# Novu HMAC验证
def verify_novu_webhook(
    signature: str, 
    payload: bytes, 
    secret: str
) -> bool:
    """验证Novu webhook签名"""
    import hmac
    import hashlib
    expected = hmac.new(
        secret.encode(), 
        payload, 
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### 2. 数据加密

- **传输加密:** 所有API使用HTTPS/WSS
- **存储加密:** 敏感payload字段加密存储
- **密钥管理:** 使用环境变量,不硬编码

### 3. 权限控制

```python
def check_notification_permission(
    user: User, 
    notification: Notification
) -> bool:
    """检查用户是否有权限访问通知"""
    return (
        notification.receiver_id == user.id or
        user.has_role('admin')
    )
```

### 4. 速率限制

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@router.post("/notifications/send")
@limiter.limit("10/minute")  # 每分钟最多10次
async def send_notification(...):
    pass
```

---

## 性能优化

### 1. 缓存策略

```python
# Redis缓存未读计数
async def get_unread_count_cached(user_id: str) -> int:
    cache_key = f"unread_count:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return int(cached)
    
    count = await novu_adapter.get_unread_count(user_id)
    await redis.setex(cache_key, 60, count)  # 缓存60秒
    return count
```

### 2. 批量操作

```python
# 批量标记已读
async def mark_multiple_as_read(
    user_id: str, 
    notification_ids: List[str]
) -> int:
    """批量标记通知为已读"""
    tasks = [
        novu_adapter.mark_as_read(nid) 
        for nid in notification_ids
    ]
    results = await asyncio.gather(*tasks)
    return sum(results)
```

### 3. 分页加载

```typescript
// 前端无限滚动
function useInfiniteNotifications() {
  const [page, setPage] = useState(0);
  const { notifications, fetchMore } = useNovuNotifications({...});
  
  const handleScroll = useCallback(() => {
    if (isNearBottom()) {
      fetchMore();
      setPage(p => p + 1);
    }
  }, [fetchMore]);
  
  return { notifications, handleScroll };
}
```

### 4. WebSocket优化

```typescript
// 连接池管理
class WebSocketManager {
  private connections: Map<string, WebSocket> = new Map();
  
  getConnection(userId: string): WebSocket {
    if (!this.connections.has(userId)) {
      const ws = this.createConnection(userId);
      this.connections.set(userId, ws);
    }
    return this.connections.get(userId)!;
  }
  
  // 心跳保活
  private startHeartbeat(ws: WebSocket) {
    setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }
}
```

---

## 部署架构

### Docker Compose配置

```yaml
version: '3.8'

services:
  # Novu API服务
  novu-api:
    image: ghcr.io/novuhq/novu/api:latest
    environment:
      NODE_ENV: production
      MONGO_URL: mongodb://novu-mongo:27017/novu-db
      REDIS_HOST: novu-redis
      REDIS_PORT: 6379
      JWT_SECRET: ${NOVU_JWT_SECRET}
      STORE_ENCRYPTION_KEY: ${NOVU_ENCRYPTION_KEY}
    ports:
      - "3000:3000"
    depends_on:
      - novu-mongo
      - novu-redis
    restart: unless-stopped
    networks:
      - novu-network

  # Novu WebSocket服务
  novu-ws:
    image: ghcr.io/novuhq/novu/ws:latest
    environment:
      REDIS_HOST: novu-redis
      REDIS_PORT: 6379
      JWT_SECRET: ${NOVU_JWT_SECRET}
    ports:
      - "3002:3002"
    depends_on:
      - novu-redis
    restart: unless-stopped
    networks:
      - novu-network

  # Novu Worker服务
  novu-worker:
    image: ghcr.io/novuhq/novu/worker:latest
    environment:
      MONGO_URL: mongodb://novu-mongo:27017/novu-db
      REDIS_HOST: novu-redis
      REDIS_PORT: 6379
    depends_on:
      - novu-mongo
      - novu-redis
    restart: unless-stopped
    networks:
      - novu-network

  # Novu Web控制台
  novu-web:
    image: ghcr.io/novuhq/novu/web:latest
    environment:
      REACT_APP_API_URL: http://localhost:3000
      REACT_APP_WS_URL: http://localhost:3002
    ports:
      - "4200:4200"
    restart: unless-stopped
    networks:
      - novu-network

  # MongoDB
  novu-mongo:
    image: mongo:6
    volumes:
      - novu-mongo-data:/data/db
    ports:
      - "27017:27017"
    restart: unless-stopped
    networks:
      - novu-network

  # Redis
  novu-redis:
    image: redis:alpine
    volumes:
      - novu-redis-data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - novu-network

volumes:
  novu-mongo-data:
  novu-redis-data:

networks:
  novu-network:
    driver: bridge
```

### 环境变量配置

```bash
# .env.novu
NOVU_JWT_SECRET=your-super-secret-jwt-key-change-this
NOVU_ENCRYPTION_KEY=your-32-char-encryption-key-here
NOVU_API_URL=http://localhost:3000
NOVU_WS_URL=http://localhost:3002
```

### 生产环境建议

1. **负载均衡**
   - Nginx反向代理
   - 多实例部署novu-api和novu-ws

2. **数据备份**
   - MongoDB定期备份
   - Redis AOF持久化

3. **监控告警**
   - Prometheus + Grafana
   - 监控指标: API响应时间、通知发送成功率、WebSocket连接数

4. **日志管理**
   - ELK Stack (Elasticsearch + Logstash + Kibana)
   - 集中式日志收集

---

## 总结

本设计文档提供了使用自托管Novu完全替代Dify消息通知系统的完整方案:

✅ **架构清晰** - 分层设计,职责明确  
✅ **功能完整** - 覆盖所有Dify现有功能  
✅ **易于扩展** - 模块化设计,便于添加新功能  
✅ **性能优化** - 缓存、批量操作、WebSocket  
✅ **安全可靠** - 认证授权、数据加密、权限控制  
✅ **部署简单** - Docker Compose一键部署

**下一步:** 根据本设计文档进行具体实现

---

**文档版本:** 1.0  
**创建日期:** 2026-01-21  
**作者:** AI Assistant
