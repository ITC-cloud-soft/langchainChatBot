# Localhost硬编码优化方案

## 📊 现状分析

### 发现的问题

在 `api/services/notification_service.py` 中发现 **2处** 仍然使用localhost硬编码：

**位置1 - Line 210-211 (list_notifications方法)**
```python
novu_api_url = os.getenv("NOVU_API_URL", "http://localhost:3000")
novu_api_key = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
```

**位置2 - Line 261-262 (get_unread_count方法)**
```python
novu_api_url = os.getenv("NOVU_API_URL", "http://localhost:3000")
novu_api_key = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
```

### 已优化的部分

✅ `__init__` 方法已添加配置验证（Line 31-44）
✅ `mark_as_read` 方法已使用 `self.novu_api_url`
✅ `mark_as_seen` 方法已使用 `self.novu_api_url`
✅ `mark_all_as_read` 方法已使用 `self.novu_api_url`
✅ `delete_notification` 方法已使用 `self.novu_api_url`

---

## 🔧 优化方案

### 方案1：手动修改（推荐）

在 `notification_service.py` 中修改以下2处：

#### 修改1：list_notifications 方法（约Line 210-214）

**修改前：**
```python
try:
    # Novu Messages APIから直接取得
    novu_api_url = os.getenv("NOVU_API_URL", "http://localhost:3000")
    novu_api_key = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
    
    response = requests.get(
        f"{novu_api_url}/v1/messages",
```

**修改后：**
```python
try:
    # Novu Messages APIから直接取得
    response = requests.get(
        f"{self.novu_api_url}/v1/messages",
```

#### 修改2：get_unread_count 方法（约Line 261-265）

**修改前：**
```python
try:
    # Novu Messages APIから直接取得
    novu_api_url = os.getenv("NOVU_API_URL", "http://localhost:3000")
    novu_api_key = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
    
    response = requests.get(
        f"{novu_api_url}/v1/messages",
```

**修改后：**
```python
try:
    # Novu Messages APIから直接取得
    response = requests.get(
        f"{self.novu_api_url}/v1/messages",
```

---

### 方案2：使用sed命令批量替换

```bash
# 在backend目录执行
cd c:\Users\dev002\OneDrive\Documents\projects\github\aiportal.chatbot\langchainChatBot\backend

# 删除两处的环境变量获取行
sed -i '/novu_api_url = os.getenv("NOVU_API_URL", "http:\/\/localhost:3000")/d' api/services/notification_service.py
sed -i '/novu_api_key = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")/d' api/services/notification_service.py

# 替换URL引用
sed -i 's/f"{novu_api_url}\/v1\/messages"/f"{self.novu_api_url}\/v1\/messages"/g' api/services/notification_service.py
```

---

## 📝 环境变量配置指南

### 开发环境 (.env)

```bash
# Novu API配置
NOVU_API_URL=http://localhost:3000
NOVU_API_KEY=c47cfb7a083c4e27f9d1b523a20ed59f
```

### Docker环境 (docker-compose.yml)

```yaml
services:
  chatbot-backend:
    environment:
      - NOVU_API_URL=http://novu-api:3000
      - NOVU_API_KEY=${NOVU_API_KEY}
```

### 生产环境

```bash
# Kubernetes ConfigMap/Secret
NOVU_API_URL=https://api.novu.co
NOVU_API_KEY=<your-production-api-key>
```

---

## ✅ 验证步骤

修改完成后，执行以下验证：

### 1. 检查配置加载

```python
# 在Python shell中测试
import os
os.environ['NOVU_API_URL'] = 'http://test-novu:3000'
os.environ['NOVU_API_KEY'] = 'test-key'

from api.services.notification_service import NotificationService
# 应该成功初始化，不会使用localhost
```

### 2. 启动时验证

```bash
# 启动backend，检查日志
docker logs chatbot-backend --tail 20

# 应该看到成功加载环境变量，没有localhost相关错误
```

### 3. 功能测试

```bash
# 运行测试套件
cd novu-integration/template/test
python run_tests.py --quick
```

---

## 🎯 优化效果

### 修改前
- ❌ 硬编码localhost作为默认值
- ❌ 每个方法重复获取环境变量
- ❌ 无法在启动时发现配置错误
- ❌ 生产环境部署需要额外注意

### 修改后
- ✅ 必须配置环境变量，无默认值
- ✅ 初始化时一次性获取配置
- ✅ 启动时立即验证配置
- ✅ 生产环境部署更安全

---

## 📌 其他需要检查的文件

### novu_adapter.py

**当前状态（Line 32）：**
```python
self.backend_url = backend_url or os.getenv("NOVU_API_URL", "http://localhost:3000")
```

**建议修改为：**
```python
self.backend_url = backend_url or os.getenv("NOVU_API_URL")
if not self.backend_url:
    raise ValueError(
        "NOVU_API_URL environment variable is required. "
        "Please set it to your Novu API endpoint."
    )
```

### 测试文件

测试文件中的localhost是可以接受的，因为：
- ✅ `tests/test_novu_integration.py` - 单元测试，使用mock
- ✅ `novu-integration/template/test/*.py` - 集成测试，本地环境

---

## 🚀 部署检查清单

部署到生产环境前，确认：

- [ ] 所有硬编码的localhost已移除
- [ ] 环境变量NOVU_API_URL已配置
- [ ] 环境变量NOVU_API_KEY已配置
- [ ] 启动时配置验证通过
- [ ] 功能测试全部通过
- [ ] 日志中无localhost相关警告

---

**创建日期**: 2026-01-22  
**状态**: 待实施
