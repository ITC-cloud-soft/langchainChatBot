# ARS API Key设置指南

## 🔑 问题说明

当前错误: `❌ Flow 9 実行失敗: ARS API error: 401 - APIキーが必要です`

**原因**: ARS API需要特定格式的API key,必须以`ars_`开头。

---

## ✅ 如何获取正确的ARS API Key

### 方法1: 通过ARS前端生成

1. 访问ARS前端: `http://localhost:3030`
2. 登录ARS系统
3. 进入**API Key管理**页面
4. 点击**生成新的API Key**
5. 复制生成的API key (格式: `ars_xxxxxxxxxxxxxx...`)

### 方法2: 直接从ARS数据库查询

如果你已经在ARS系统中创建了API key,可以从数据库中查询:

```bash
docker exec ars-mysql-db mysql -uroot -prootpassword -D ars_db -e "SELECT id, name, api_key, created_at FROM api_keys WHERE is_active=1;"
```

---

## 📝 在Chatbot中保存ARS API Key

1. 访问Chatbot前端: `http://localhost:3000`
2. 登录后,进入**ARS设置**页面
3. 在**ARS API Token**输入框中粘贴从ARS获取的API key
   - ✅ 正确格式: `ars_abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGH`
   - ❌ 错误格式: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (这是JWT token,不是API key)
4. 点击**保存**

---

## 🧪 验证API Key是否正确

保存后,在聊天页面发送:

```
CCFLOWシステム申請--仕入計画を実行します
```

### 期望结果

- ✅ **成功**: `✅ Flow 9 実行成功!` + 执行结果
- ❌ **失败**: 
  - `401 - APIキーが必要です` → API key未保存或格式错误
  - `401 - 無効なAPIキー形式です` → API key格式错误(不是以`ars_`开头)
  - `403 - APIキーが無効です` → API key已失效或被删除

---

## 🔍 API Key格式说明

ARS API key的格式:
- **前缀**: `ars_`
- **长度**: 52个字符 (前缀4个 + 随机48个)
- **字符集**: 大小写字母 + 数字
- **示例**: `ars_Abc123XyZ789...` (共52个字符)

**注意**: 不要与JWT token混淆!
- JWT token: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- ARS API key: `ars_...`

---

## 🚀 快速测试

如果你想快速测试,可以临时创建一个测试API key:

```bash
# 进入ARS后端容器
docker exec -it ars-backend bash

# 运行Python脚本创建API key
python -c "
from services.db_services.api_key_service import create_api_key
result = create_api_key('test_key', 'Test API Key for chatbot', user_id=1)
print('API Key:', result['api_key'])
"
```

复制输出的API key,然后在Chatbot的ARS设置页面保存。

---

## ❓ 常见问题

### Q: 我应该使用哪个token?
A: 使用**ARS API key** (以`ars_`开头),不是JWT token。

### Q: API key在哪里生成?
A: 在ARS系统中生成,不是在Chatbot中生成。

### Q: 为什么我的token不工作?
A: 检查是否以`ars_`开头,如果不是,说明你保存的是错误的token。

### Q: 如何检查我保存的token?
A: 查看Chatbot数据库:
```bash
docker exec mysql-db mysql -uroot -pmysql_root_password -D chatbot_db -e "SELECT user_id, LEFT(token, 10) as token_prefix FROM ars_tokens;"
```
应该看到`ars_...`开头的token。
