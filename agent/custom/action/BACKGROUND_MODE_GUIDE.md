# 🚀 自动远征后台模式 - 快速使用指南

## 问题

原来的远征系统会阻塞执行流程：

```
启动远征 → ⏸️ 等待... → ⏸️ 检测... → ⏸️ 收取... → 其他任务
```

**其他任务必须等待远征完成才能执行！**

## 解决方案

使用**后台模式**，让远征在后台线程运行：

```
启动远征 → ✅ 立即返回 → 同时执行其他任务
            ↓
      后台自动运行
```

## 🎯 使用方法

### 方式1：在 Pipeline 中配置 ⭐

**启动后台远征：**

```json
{
  "StartExpedition": {
    "action": "Custom",
    "custom_action": "AutoExpedition",
    "custom_action_param": "{\"mode\": \"start\", \"background\": true}",
    "next": ["其他任务"]
  }
}
```

**停止后台远征：**

```json
{
  "StopExpedition": {
    "action": "Custom",
    "custom_action": "AutoExpedition",
    "custom_action_param": "{\"mode\": \"stop\"}"
  }
}
```

### 方式2：完整流程示例

```json
{
  "MainFlow": {
    "next": ["StartExpedition"]
  },
  
  "StartExpedition": {
    "action": "Custom",
    "custom_action": "AutoExpedition",
    "custom_action_param": "{\"mode\": \"start\", \"background\": true}",
    "next": ["DailyTask"]
  },
  
  "DailyTask": {
    "action": "Click",
    "target": "日常任务",
    "next": ["Combat"]
  },
  
  "Combat": {
    "recognition": "TemplateMatch",
    "template": "战斗.png",
    "next": ["Exercise"]
  },
  
  "Exercise": {
    "action": "Click",
    "target": "演习",
    "next": ["StopExpedition"]
  },
  
  "StopExpedition": {
    "action": "Custom",
    "custom_action": "AutoExpedition",
    "custom_action_param": "{\"mode\": \"stop\"}",
    "next": ["End"]
  },
  
  "End": {
    "action": "Click",
    "target": "返回"
  }
}
```

**执行流程：**

1. ✅ 启动后台远征
2. ✅ 立即执行日常任务
3. ✅ 执行战斗
4. ✅ 执行演习
5. ✅ 停止远征
6. ✅ 返回

**远征在后台持续运行，自动收取和派出！**

## 📊 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| `mode` | string | `"start"` | `"start"` 启动远征<br>`"stop"` 停止远征 |
| `background` | boolean | `true` | `true` 后台运行（不阻塞）<br>`false` 前台运行（阻塞） |

## 🆚 模式对比

### 前台模式 (background: false)

```
┌─────────────────────────────────────┐
│ 启动远征                             │
├─────────────────────────────────────┤
│ ⏸️  等待检测...                      │
│ ⏸️  收取奖励...                      │
│ ⏸️  重新派出...                      │
│ ⏸️  等待检测...                      │
│ ⏸️  收取奖励...                      │
├─────────────────────────────────────┤
│ ✅ 远征结束                          │
├─────────────────────────────────────┤
│ 执行其他任务 ←────────── 必须等待    │
└─────────────────────────────────────┘
```

**特点：**

- ✅ 简单，易控制
- ❌ 阻塞执行
- ❌ 效率低

### 后台模式 (background: true) ⭐

```
┌──────────────────┐    ┌──────────────────┐
│ 启动远征         │    │ 后台线程         │
├──────────────────┤    ├──────────────────┤
│ ✅ 立即返回      │    │ 🔄 检测...       │
├──────────────────┤    │ 💰 收取...       │
│ 执行日常任务     │    │ 🚢 派出...       │
├──────────────────┤    │ 🔄 检测...       │
│ 执行战斗         │    │ 💰 收取...       │
├──────────────────┤    │ 🚢 派出...       │
│ 执行演习         │    │ 🔄 检测...       │
├──────────────────┤    ├──────────────────┤
│ 停止远征         │───►│ 🛑 停止          │
└──────────────────┘    └──────────────────┘
   同时执行！               自动运行
```

**特点：**

- ✅ 不阻塞，效率高
- ✅ 可同时执行多任务
- ✅ 自动管理远征
- ⚠️ 需手动停止

## ⚙️ 已修改的文件

1. **`expedition.py`** - 添加后台模式支持
   - 新增 `run_task_background()` 函数
   - 新增线程控制逻辑
   - 支持 `mode` 和 `background` 参数

2. **`远征确认.json`** - 添加示例配置
   - `AutoExpeditionTest` - 前台模式示例
   - `AutoExpeditionBackground` - 后台模式示例
   - `StopExpedition` - 停止示例

## 💡 使用建议

### 推荐：后台模式

```json
{
  "custom_action_param": "{\"mode\": \"start\", \"background\": true}"
}
```

**适用场景：**

- ✅ 需要同时运行远征和其他任务
- ✅ 提高执行效率
- ✅ 远征作为辅助任务

### 前台模式

```json
{
  "custom_action_param": "{\"mode\": \"start\", \"background\": false}"
}
```

**适用场景：**

- ✅ 只运行远征
- ✅ 需要等待远征完成
- ✅ 兼容原有逻辑

## ⚠️ 注意事项

1. **后台模式启动后会持续运行**
   - 建议在流程结束前调用 `stop` 停止
   - 或者依赖程序退出自动停止（守护线程）

2. **查看日志**
   - 后台远征日志带 `[ExpeditionThread]` 标记
   - 可以区分主线程和远征线程的日志

3. **线程安全**
   - 远征系统使用独立线程
   - Context 对象线程安全
   - 不会与主线程冲突

4. **停止建议**

   ```json
   {
     "LastTask": {
       "action": "Custom",
       "custom_action": "AutoExpedition",
       "custom_action_param": "{\"mode\": \"stop\"}"
     }
   }
   ```

## 🎉 完成

现在你可以：

1. ✅ 启动后台远征
2. ✅ 同时执行其他任务
3. ✅ 远征自动收取和派出
4. ✅ 任务完成后停止远征

**效率提升，不再等待！** 🚀
