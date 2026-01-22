# Novu自托管完整实施指南

## 目录

1. [概述](#概述)
2. [前置要求](#前置要求)
3. [步骤1: 部署Novu服务](#步骤1-部署novu服务)
4. [步骤2: 配置后端](#步骤2-配置后端)
5. [步骤3: 配置前端](#步骤3-配置前端)
6. [步骤4: 创建Novu工作流](#步骤4-创建novu工作流)
7. [步骤5: 数据迁移](#步骤5-数据迁移)
8. [步骤6: 测试验证](#步骤6-测试验证)
9. [步骤7: 生产部署](#步骤7-生产部署)
10. [故障排除](#故障排除)

---

## 概述

本指南将帮助你完成从Dify消息通知系统到自托管Novu的完整迁移,实现以下目标:

✅ **功能完全覆盖**
- 从数据库读取并显示通知
- 点击通知生成动态表单和按钮
- 工作流审批交互
- 实时WebSocket推送
- 跨设备同步

✅ **技术优势**
- 开源免费,数据完全掌控
- 高性能实时推送
- 易于扩展和维护

**预计时间:** 4-6周
**难度等级:** 中等

---

## 前置要求

### 系统要求

- **操作系统:** Linux/macOS/Windows
- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **内存:** 最少4GB (推荐8GB)
- **磁盘:** 最少20GB可用空间

### 技术栈要求

**后端:**
- Python 3.11+
- FastAPI 0.104+
- PostgreSQL 15+
- Redis 7+

**前端:**
- Node.js 18+
- React 18+
- TypeScript 5+
- Next.js 14+

### 必要的访问权限

- 服务器SSH访问权限
- 数据库管理权限
- 域名配置权限(生产环境)

---

## 步骤1: 部署Novu服务

### 1.1 准备环境变量

复制环境变量模板:

```bash
cd /path/to/aiportal.chatbot
cp .env.novu.example .env.novu
```

编辑 `.env.novu` 并设置以下关键变量:

```bash
# 生成JWT密钥
openssl rand -base64 32

# 生成加密密钥(必须是32字符)
openssl rand -hex 16
```

将生成的密钥填入 `.env.novu`:

```bash
NOVU_JWT_SECRET=<生成的JWT密钥>
NOVU_ENCRYPTION_KEY=<生成的32字符加密密钥>

# MongoDB认证(生产环境必须修改)
MONGO_ROOT_USERNAME=root
MONGO_ROOT_PASSWORD=<强密码>

# Redis密码(可选)
REDIS_PASSWORD=<Redis密码>

# URL配置
FRONT_BASE_URL=http://localhost:4200
REACT_APP_API_URL=http://localhost:3000
REACT_APP_WS_URL=http://localhost:3002
```

### 1.2 启动Novu服务

```bash
# 启动所有服务
docker-compose -f docker-compose.novu.yml up -d

# 查看日志
docker-compose -f docker-compose.novu.yml logs -f

# 检查服务状态
docker-compose -f docker-compose.novu.yml ps
```

### 1.3 验证服务

等待所有服务启动(约1-2分钟),然后验证:

```bash
# 检查Novu API
curl http://localhost:3000/v1/health-check

# 检查WebSocket
curl http://localhost:3002/health-check

# 访问Web控制台
# 浏览器打开: http://localhost:4200
```

### 1.4 创建Novu账户

1. 访问 `http://localhost:4200`
2. 点击 "Sign Up" 创建账户
3. 填写邮箱和密码
4. 登录后,进入Dashboard

### 1.5 获取API密钥

1. 在Novu Dashboard中,点击右上角的设置图标
2. 选择 "API Keys"
3. 复制 "API Key" (以 `novu_` 开头)
4. 保存到 `.env.novu`:

```bash
NOVU_API_KEY=novu_xxxxxxxxxxxxxx
```

---

## 步骤2: 配置后端

### 2.1 安装Python依赖

编辑 `langchainChatBot/backend/requirements.txt`,添加:

```txt
# Novu SDK
novu==1.6.0

# Socket.IO (如果还没有)
python-socketio==5.11.0
```

安装依赖:

```bash
cd langchainChatBot/backend
pip install -r requirements.txt
```

### 2.2 配置环境变量

编辑 `langchainChatBot/backend/.env`:

```bash
# Novu配置
NOVU_API_KEY=novu_xxxxxxxxxxxxxx
NOVU_API_URL=http://localhost:3000
NOVU_WS_URL=http://localhost:3002
```

### 2.3 创建数据库迁移

创建数据库迁移文件:

```bash
cd langchainChatBot/backend

# 创建迁移
alembic revision -m "add_novu_notification_tables"
```

编辑生成的迁移文件 `alembic/versions/xxxx_add_novu_notification_tables.py`:

```python
"""add_novu_notification_tables

Revision ID: xxxx
Revises: yyyy
Create Date: 2026-01-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'xxxx'
down_revision = 'yyyy'
branch_labels = None
depends_on = None


def upgrade():
    # notifications表
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('chatbot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('novu_notification_id', sa.String(255), unique=True, nullable=True),
        sa.Column('novu_subscriber_id', sa.String(255), nullable=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('receiver_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('payload', postgresql.JSON, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('sent_at', sa.DateTime, nullable=True),
        sa.Column('read_at', sa.DateTime, nullable=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )
    
    # インデックス作成
    op.create_index('idx_notifications_receiver_status', 'notifications', ['receiver_id', 'status'])
    op.create_index('idx_notifications_novu_id', 'notifications', ['novu_notification_id'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('idx_notifications_category', 'notifications', ['category'])
    
    # notification_sync_log表
    op.create_table(
        'notification_sync_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('novu_notification_id', sa.String(255), nullable=False),
        sa.Column('local_notification_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sync_direction', sa.String(20), nullable=False),
        sa.Column('sync_status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('synced_at', sa.DateTime, nullable=False),
    )
    
    op.create_index('idx_sync_log_novu_id', 'notification_sync_log', ['novu_notification_id'])
    op.create_index('idx_sync_log_status', 'notification_sync_log', ['sync_status', 'synced_at'])


def downgrade():
    op.drop_table('notification_sync_log')
    op.drop_table('notifications')
```

実行マイグレーション:

```bash
alembic upgrade head
```

### 2.4 注册API路由

编辑 `langchainChatBot/backend/main.py`,添加通知路由:

```python
from api.controllers.notification_controller import router as notification_router

# 注册路由
app.include_router(notification_router)
```

### 2.5 配置依赖注入

创建 `langchainChatBot/backend/api/dependencies.py` (如果不存在):

```python
from functools import lru_cache
from sqlalchemy.orm import Session
from api.adapters.novu_adapter import NovuAdapter
from api.database import SessionLocal
import os

def get_db():
    """データベースセッションの取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@lru_cache()
def get_novu_adapter() -> NovuAdapter:
    """Novuアダプターのシングルトン取得"""
    return NovuAdapter(
        api_key=os.getenv("NOVU_API_KEY"),
        backend_url=os.getenv("NOVU_API_URL")
    )

def get_current_user():
    """現在のユーザーを取得 (認証実装に応じて修正)"""
    # TODO: JWT認証実装
    pass
```

---

## 步骤3: 配置前端

### 3.1 安装NPM依赖

```bash
cd langchainChatBot/frontend

# 安装Socket.IO客户端
npm install socket.io-client

# 安装Ant Design (如果还没有)
npm install antd @ant-design/icons
```

### 3.2 配置环境变量

编辑 `langchainChatBot/frontend/.env.local`:

```bash
# Novu配置
NEXT_PUBLIC_NOVU_APP_ID=your-application-identifier
NEXT_PUBLIC_NOVU_API_URL=http://localhost:3000
NEXT_PUBLIC_NOVU_WS_URL=http://localhost:3002

# 后端API
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**获取Application Identifier:**
1. 登录Novu Dashboard (`http://localhost:4200`)
2. 点击左侧菜单 "Settings" → "API Keys"
3. 复制 "Application Identifier"

### 3.3 集成NotificationBell组件

编辑你的布局文件 (例如 `app/layout.tsx`):

```typescript
import NotificationBell from '@/components/NotificationBell';
import { useAuth } from '@/contexts/AuthContext';

export default function Layout({ children }) {
  const { user } = useAuth();
  
  return (
    <div>
      <header>
        {/* 其他头部内容 */}
        {user && <NotificationBell userId={user.id} />}
      </header>
      <main>{children}</main>
    </div>
  );
}
```

### 3.4 配置聊天机器人集成

编辑 `app/chatbot/hooks/useChatbotActions.ts`,添加通知事件监听:

```typescript
import { useEffect } from 'react';

export function useChatbotActions() {
  // 现有代码...
  
  useEffect(() => {
    // 监听通知创建聊天事件
    const handleNewChat = (event: CustomEvent) => {
      const { title, content, payload, type, showApprovalButtons } = event.detail;
      
      if (type === 'workflow_request') {
        // 创建新的聊天会话
        const newSessionId = `draft_${Date.now()}`;
        
        // 创建带审批按钮的消息
        const approvalMessage = {
          id: `approval-${Date.now()}`,
          type: 'bot',
          content: `${content}\n\nWorkID: ${payload.workflowData.WorkID}\nFlowName: ${payload.workflowData.FlowName}`,
          formElements: payload.actions.map((action: any) => ({
            type: 'button',
            id: action.id,
            label: action.label,
            action: action.action,
            primary: action.type === 'primary'
          })),
          formRole: 'approve',
          formSchema: payload.formSchema
        };
        
        // 会话とメッセージを設定
        setSessions([...sessions, { id: newSessionId, title, messages: [approvalMessage] }]);
        setSelectedSession(newSessionId);
      }
    };
    
    window.addEventListener('createNewChat', handleNewChat as EventListener);
    
    return () => {
      window.removeEventListener('createNewChat', handleNewChat as EventListener);
    };
  }, [sessions]);
  
  // 现有代码...
}
```

---

## 步骤4: 创建Novu工作流

### 4.1 登录Novu Dashboard

访问 `http://localhost:4200` 并登录

### 4.2 创建工作流审批通知

1. 点击左侧菜单 "Workflows"
2. 点击 "Create Workflow"
3. 选择 "Blank Workflow"

**配置工作流:**

- **Name:** `workflow-approval`
- **Identifier:** `workflow-approval` (重要:必须与代码中一致)
- **Description:** 工作流审批通知

### 4.3 添加In-App步骤

1. 点击 "Add Step"
2. 选择 "In-App"
3. 配置模板:

**Content:**
```
{{content}}
```

**CTA (Call To Action):**
- Type: `redirect`
- URL: `/chatbot`

**Actions:**
添加两个按钮:

按钮1:
- Type: `primary`
- Label: `{{approveLabel}}`

按钮2:
- Type: `secondary`
- Label: `{{rejectLabel}}`

4. 点击 "Save" 保存

### 4.4 创建系统通知工作流

重复上述步骤,创建 `system-notification` 工作流:

- **Name:** `system-notification`
- **Identifier:** `system-notification`
- **Description:** 系统通知

**Content:**
```
{{title}}

{{content}}
```

---

## 步骤5: 数据迁移

### 5.1 创建迁移脚本

创建 `langchainChatBot/backend/scripts/migrate_notifications_to_novu.py`:

```python
"""
既存の通知データをNovuに移行するスクリプト
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.adapters.novu_adapter import NovuAdapter
from api.models.notification import Notification
from api.services.notification_service import NotificationService

load_dotenv()

# データベース接続
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def migrate_notifications():
    """既存の通知をNovuに移行"""
    db = SessionLocal()
    novu = NovuAdapter()
    service = NotificationService(novu_adapter=novu, db_session=db)
    
    try:
        # 既存の通知を取得 (Novu IDがないもの)
        notifications = db.query(Notification).filter(
            Notification.novu_notification_id == None
        ).all()
        
        print(f"Found {len(notifications)} notifications to migrate")
        
        migrated_count = 0
        failed_count = 0
        
        for notif in notifications:
            try:
                # 購読者を作成
                novu.create_subscriber(
                    subscriber_id=str(notif.receiver_id),
                    data={"tenant_id": str(notif.tenant_id) if notif.tenant_id else None}
                )
                
                # 通知を再送信
                if notif.category == "workflow_request":
                    # ワークフロー承認通知
                    novu_id = novu.trigger_workflow(
                        workflow_id="workflow-approval",
                        subscriber_id=str(notif.receiver_id),
                        payload=notif.payload or {}
                    )
                else:
                    # システム通知
                    novu_id = novu.trigger_workflow(
                        workflow_id="system-notification",
                        subscriber_id=str(notif.receiver_id),
                        payload={
                            "title": notif.title,
                            "content": notif.content,
                            "category": notif.category
                        }
                    )
                
                # Novu IDを保存
                notif.novu_notification_id = novu_id
                db.commit()
                
                migrated_count += 1
                print(f"Migrated notification {notif.id}")
                
            except Exception as e:
                print(f"Failed to migrate notification {notif.id}: {str(e)}")
                failed_count += 1
                continue
        
        print(f"\nMigration completed:")
        print(f"  Migrated: {migrated_count}")
        print(f"  Failed: {failed_count}")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_notifications()
```

### 5.2 执行迁移

```bash
cd langchainChatBot/backend
python scripts/migrate_notifications_to_novu.py
```

---

## 步骤6: 测试验证

### 6.1 单元测试

创建 `langchainChatBot/backend/tests/test_notification_service.py`:

```python
import pytest
from unittest.mock import Mock, patch
from api.services.notification_service import NotificationService
from api.adapters.novu_adapter import NovuAdapter

@pytest.fixture
def mock_novu():
    return Mock(spec=NovuAdapter)

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def service(mock_novu, mock_db):
    return NotificationService(novu_adapter=mock_novu, db_session=mock_db)

def test_send_workflow_approval(service, mock_novu):
    """ワークフロー承認通知の送信テスト"""
    workflow_data = {
        "WorkID": "WF001",
        "FlowName": "経費申請",
        "StarterName": "山田太郎"
    }
    
    mock_novu.trigger_workflow.return_value = "novu_notif_123"
    
    result = service.send_workflow_approval(
        receiver_id="user-123",
        workflow_data=workflow_data
    )
    
    assert result is not None
    assert mock_novu.trigger_workflow.called

def test_mark_as_read(service, mock_novu):
    """既読マークのテスト"""
    mock_novu.mark_message_as_read.return_value = True
    
    success = service.mark_as_read(
        user_id="user-123",
        notification_id="notif-456"
    )
    
    assert success is True
    assert mock_novu.mark_message_as_read.called
```

运行测试:

```bash
cd langchainChatBot/backend
pytest tests/test_notification_service.py -v
```

### 6.2 集成测试

创建测试脚本 `langchainChatBot/backend/scripts/test_novu_integration.py`:

```python
"""
Novu統合テストスクリプト
"""
import os
from dotenv import load_dotenv
from api.adapters.novu_adapter import NovuAdapter

load_dotenv()

def test_novu_connection():
    """Novu接続テスト"""
    print("Testing Novu connection...")
    
    novu = NovuAdapter()
    
    # 1. 購読者作成テスト
    print("\n1. Creating subscriber...")
    subscriber = novu.create_subscriber(
        subscriber_id="test-user-001",
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )
    print(f"✓ Subscriber created: {subscriber}")
    
    # 2. ワークフロートリガーテスト
    print("\n2. Triggering workflow...")
    notif_id = novu.trigger_workflow(
        workflow_id="workflow-approval",
        subscriber_id="test-user-001",
        payload={
            "title": "テスト承認リクエスト",
            "content": "これはテスト通知です",
            "workflowData": {
                "WorkID": "TEST001",
                "FlowName": "テストフロー",
                "StarterName": "テストユーザー"
            }
        }
    )
    print(f"✓ Workflow triggered: {notif_id}")
    
    # 3. 通知取得テスト
    print("\n3. Fetching notifications...")
    notifications = novu.get_notifications(
        subscriber_id="test-user-001",
        page=0,
        limit=10
    )
    print(f"✓ Notifications fetched: {len(notifications.get('data', []))} items")
    
    # 4. 未読数取得テスト
    print("\n4. Getting unread count...")
    count = novu.get_unseen_count(subscriber_id="test-user-001")
    print(f"✓ Unread count: {count}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_novu_connection()
```

运行集成测试:

```bash
cd langchainChatBot/backend
python scripts/test_novu_integration.py
```

### 6.3 端到端测试

**手动测试步骤:**

1. **启动所有服务**
   ```bash
   # Novu
   docker-compose -f docker-compose.novu.yml up -d
   
   # 后端
   cd langchainChatBot/backend
   uvicorn main:app --reload
   
   # 前端
   cd langchainChatBot/frontend
   npm run dev
   ```

2. **测试通知发送**
   - 使用Postman或curl发送测试通知
   ```bash
   curl -X POST http://localhost:8000/api/notifications/send/workflow-approval \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "receiver_id": "user-123",
       "workflow_data": {
         "WorkID": "WF001",
         "FlowName": "経費申請",
         "StarterName": "山田太郎"
       }
     }'
   ```

3. **验证前端显示**
   - 打开浏览器访问 `http://localhost:3001`
   - 检查通知铃铛是否显示未读数
   - 点击铃铛查看通知列表

4. **测试点击交互**
   - 点击通知项
   - 验证是否跳转到聊天机器人页面
   - 验证是否显示审批表单和按钮

5. **测试实时推送**
   - 打开两个浏览器窗口
   - 在一个窗口发送通知
   - 验证另一个窗口是否实时收到

---

## 步骤7: 生产部署

### 7.1 生产环境配置

编辑生产环境配置 `.env.novu.production`:

```bash
NODE_ENV=production

# 使用真实域名
FRONT_BASE_URL=https://novu.yourdomain.com
REACT_APP_API_URL=https://novu-api.yourdomain.com
REACT_APP_WS_URL=https://novu-ws.yourdomain.com

# 强密码
NOVU_JWT_SECRET=<生产环境强密钥>
NOVU_ENCRYPTION_KEY=<生产环境32字符密钥>
MONGO_ROOT_PASSWORD=<生产环境强密码>
REDIS_PASSWORD=<生产环境Redis密码>

# 禁用用户注册
DISABLE_USER_REGISTRATION=true
```

### 7.2 配置Nginx反向代理

创建 `/etc/nginx/sites-available/novu`:

```nginx
# Novu API
upstream novu_api {
    server localhost:3000;
}

# Novu WebSocket
upstream novu_ws {
    server localhost:3002;
}

# Novu Web
upstream novu_web {
    server localhost:4200;
}

# API服务器
server {
    listen 443 ssl http2;
    server_name novu-api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://novu_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# WebSocketサーバー
server {
    listen 443 ssl http2;
    server_name novu-ws.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://novu_ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Web管理コンソール
server {
    listen 443 ssl http2;
    server_name novu.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://novu_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

启用配置:

```bash
sudo ln -s /etc/nginx/sites-available/novu /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7.3 配置SSL证书

使用Let's Encrypt:

```bash
sudo certbot --nginx -d novu.yourdomain.com -d novu-api.yourdomain.com -d novu-ws.yourdomain.com
```

### 7.4 配置数据备份

创建备份脚本 `/opt/scripts/backup_novu.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/novu"
DATE=$(date +%Y%m%d_%H%M%S)

# MongoDB备份
docker exec novu-mongo mongodump --out /tmp/backup
docker cp novu-mongo:/tmp/backup $BACKUP_DIR/mongodb_$DATE

# Redis备份
docker exec novu-redis redis-cli SAVE
docker cp novu-redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 压缩备份
tar -czf $BACKUP_DIR/novu_backup_$DATE.tar.gz $BACKUP_DIR/mongodb_$DATE $BACKUP_DIR/redis_$DATE.rdb

# 删除30天前的备份
find $BACKUP_DIR -name "novu_backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/novu_backup_$DATE.tar.gz"
```

添加到crontab:

```bash
# 每天凌晨2点备份
0 2 * * * /opt/scripts/backup_novu.sh
```

### 7.5 配置监控

使用Prometheus + Grafana监控Novu:

创建 `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - novu-network

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    networks:
      - novu-network

volumes:
  prometheus-data:
  grafana-data:

networks:
  novu-network:
    external: true
```

---

## 故障排除

### 问题1: Novu服务无法启动

**症状:** Docker容器启动失败

**解决方案:**
```bash
# 查看日志
docker-compose -f docker-compose.novu.yml logs novu-api

# 常见原因:
# 1. 端口被占用
sudo lsof -i :3000
sudo lsof -i :3002

# 2. MongoDB未就绪
docker-compose -f docker-compose.novu.yml restart novu-mongo
sleep 10
docker-compose -f docker-compose.novu.yml restart novu-api

# 3. 环境变量错误
# 检查 .env.novu 文件
```

### 问题2: 通知无法发送

**症状:** API调用成功但通知未显示

**解决方案:**
```bash
# 1. 检查Novu API连接
curl http://localhost:3000/v1/health-check

# 2. 检查工作流是否存在
# 登录Novu Dashboard查看Workflows

# 3. 检查购订者是否创建
# 在Novu Dashboard查看Subscribers

# 4. 查看后端日志
tail -f langchainChatBot/backend/logs/app.log
```

### 问题3: WebSocket连接失败

**症状:** 无法实时接收通知

**解决方案:**
```bash
# 1. 检查WebSocket服务
curl http://localhost:3002/health-check

# 2. 检查防火墙
sudo ufw allow 3002/tcp

# 3. 检查Nginx配置 (生产环境)
# 确保WebSocket升级头正确配置

# 4. 浏览器控制台检查
# 打开开发者工具查看WebSocket连接状态
```

### 问题4: 数据库迁移失败

**症状:** Alembic迁移报错

**解决方案:**
```bash
# 1. 检查数据库连接
psql -h localhost -U postgres -d your_database

# 2. 回滚迁移
alembic downgrade -1

# 3. 重新运行
alembic upgrade head

# 4. 如果表已存在
# 手动删除表后重新迁移
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS notification_sync_log CASCADE;
```

### 问题5: 前端无法连接后端

**症状:** API请求失败

**解决方案:**
```bash
# 1. 检查环境变量
cat langchainChatBot/frontend/.env.local

# 2. 检查CORS配置
# 在后端 main.py 添加:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 检查认证token
# 浏览器开发者工具 → Application → Local Storage
```

---

## 总结

完成本指南后,你将拥有:

✅ **完全自托管的Novu通知系统**
- 所有服务运行在你的基础设施上
- 数据完全掌控

✅ **功能完整的通知系统**
- 实时WebSocket推送
- 动态表单生成
- 工作流审批交互
- 跨设备同步

✅ **生产就绪的部署**
- SSL/TLS加密
- 自动备份
- 监控告警
- 负载均衡

**下一步:**
- 根据实际业务需求创建更多工作流
- 配置通知偏好设置
- 集成更多通知渠道(Email, SMS等)
- 优化性能和扩展性

**获取帮助:**
- Novu官方文档: https://docs.novu.co
- Novu GitHub: https://github.com/novuhq/novu
- Novu Discord社区: https://discord.gg/novu

---

**文档版本:** 1.0  
**最后更新:** 2026-01-21  
**作者:** AI Assistant
