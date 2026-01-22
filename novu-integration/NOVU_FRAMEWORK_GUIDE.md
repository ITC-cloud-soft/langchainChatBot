# Novu Framework 使用指南

解决Dashboard UI限制的完整解决方案

## 🎯 为什么需要Novu Framework？

### Dashboard UI的限制

当前Novu Dashboard的可视化编辑器**无法配置**：
- ❌ Action按钮的URL
- ❌ Redirect URL的详细参数
- ❌ 复杂的条件逻辑
- ❌ 自定义数据结构

### Novu Framework的优势

使用代码定义工作流，可以：
- ✅ 完全控制所有配置选项
- ✅ 版本控制（Git管理）
- ✅ 类型安全（TypeScript）
- ✅ 易于测试和维护

## 📋 两种方案对比

### 方案A: 继续使用Dashboard（简化版）

**适用场景**: 快速测试、简单通知

**限制**:
- 只能配置基本的Subject和Body
- 无法添加可点击的Action按钮
- 通知功能有限

**优点**:
- 无需编写代码
- 快速上手

### 方案B: 使用Novu Framework（完整版）

**适用场景**: 生产环境、复杂业务逻辑

**优势**:
- 完整的功能支持
- 代码化管理
- 易于集成到现有系统

**需要**:
- 编写TypeScript/JavaScript代码
- 部署工作流定义

## 🚀 快速决策

### 如果你的需求是：

#### 1. 只是测试Novu基本功能
→ **使用Dashboard简化版即可**
- 不添加Action按钮
- 只配置Subject和Body
- 已经可以发送和接收通知了 ✅

#### 2. 需要完整的通知功能（带按钮、跳转）
→ **需要使用Novu Framework或API**
- 参考 `create_workflow_via_api.py`
- 或使用Novu Framework（需要额外设置）

## 💡 我的建议

基于你当前的情况：

### 阶段1: 验证基本功能（当前阶段）✅

你已经完成：
- ✅ Novu服务运行正常
- ✅ 工作流创建成功
- ✅ 测试脚本发送成功
- ✅ 通知可以正常触发

**建议**: 先使用简化版（无Action按钮）验证整个流程

### 阶段2: 添加完整功能（下一步）

当需要Action按钮时，有两个选择：

#### 选择1: 使用API创建工作流（较简单）

运行我创建的脚本：
```bash
python create_workflow_via_api.py
```

这会通过API创建包含完整Action按钮配置的工作流。

**注意**: Novu自托管版本的API可能不完全支持所有字段，需要测试验证。

#### 选择2: 前端处理按钮点击（推荐）

在前端Inbox组件中自定义通知的渲染和点击行为：

```typescript
// 前端代码示例
<Inbox
  onNotificationClick={(notification) => {
    // 自定义点击处理
    if (notification.data?.action === 'start') {
      router.push('/getting-started');
    }
  }}
  renderNotification={(notification) => {
    // 自定义渲染，添加按钮
    return (
      <div>
        <p>{notification.body}</p>
        <button onClick={() => handlePrimaryAction(notification)}>
          开始使用
        </button>
        <button onClick={() => handleSecondaryAction(notification)}>
          查看教程
        </button>
      </div>
    );
  }}
/>
```

这种方式：
- ✅ 不依赖Dashboard配置
- ✅ 完全自定义UI
- ✅ 灵活处理业务逻辑
- ✅ 适合自托管版本

## 🎯 当前最佳实践

### 1. 在Dashboard中创建简单工作流

只配置必要字段：
```
Subject: 欢迎来到我们的平台!
Body: {{userName}}，很高兴你加入我们
```

### 2. 在触发时传递额外数据

```python
payload = {
    "name": "welcome-notification",
    "to": {"subscriberId": user_id},
    "payload": {
        "userName": user_name,
        # 传递按钮相关数据
        "primaryAction": {
            "label": "开始使用",
            "url": "/getting-started"
        },
        "secondaryAction": {
            "label": "查看教程", 
            "url": "/tutorials"
        }
    }
}
```

### 3. 在前端Inbox组件中使用这些数据

```typescript
renderNotification={(notification) => {
  const { primaryAction, secondaryAction } = notification.data;
  
  return (
    <div>
      <p>{notification.body}</p>
      {primaryAction && (
        <button onClick={() => router.push(primaryAction.url)}>
          {primaryAction.label}
        </button>
      )}
      {secondaryAction && (
        <button onClick={() => router.push(secondaryAction.url)}>
          {secondaryAction.label}
        </button>
      )}
    </div>
  );
}}
```

## 📊 总结

| 功能 | Dashboard配置 | API创建 | 前端自定义 |
|------|--------------|---------|-----------|
| 基本通知 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| Action按钮URL | ❌ 不支持 | ⚠️ 可能支持 | ✅ 完全支持 |
| 自定义UI | ❌ 不支持 | ❌ 不支持 | ✅ 完全支持 |
| 易用性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 灵活性 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**推荐方案**: Dashboard简单配置 + 前端自定义渲染

---

**创建时间**: 2026-01-21  
**适用版本**: Novu 自托管版本
