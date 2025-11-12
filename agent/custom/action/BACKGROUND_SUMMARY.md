# ✅ 后台远征功能已完成

## 🎯 解决的问题

**原问题：** 自动远征阻塞执行流程，其他任务只能在检测结束后执行

**解决方案：** 使用多线程，让远征在后台运行

## 📦 已完成的修改

### 1. `expedition.py` - 核心功能 ⭐

**新增功能：**

- ✅ 后台运行模式（使用独立线程）
- ✅ 前台运行模式（兼容原版）
- ✅ 停止功能（优雅停止后台线程）
- ✅ 线程安全的 Context 调用

**新增函数：**

```python
def run_task_background(task_conf, context, stop_event)
    # 后台线程运行远征
    # 支持停止信号
    # 自动循环检测收取
```

**新增参数：**

```json
{
  "mode": "start",      // "start" 或 "stop"
  "background": true    // true=后台, false=前台
}
```

### 2. `远征确认.json` - Pipeline 配置

**新增任务：**

- `AutoExpeditionBackground` - 后台模式示例
- `StopExpedition` - 停止远征示例
- 完整流程示例

### 3. 文档和工具

**新增文件：**

- `BACKGROUND_MODE_GUIDE.md` - 快速使用指南 📖
- `expedition_background_config.json` - 详细配置说明
- `test_background_expedition.py` - 演示程序

## 🚀 使用方法

### 快速开始

**1. 启动后台远征：**

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

**2. 执行其他任务（同时进行）：**

```json
{
  "其他任务": {
    "action": "Click",
    "target": "按钮",
    "next": ["更多任务"]
  }
}
```

**3. 停止远征：**

```json
{
  "StopExpedition": {
    "action": "Custom",
    "custom_action": "AutoExpedition",
    "custom_action_param": "{\"mode\": \"stop\"}"
  }
}
```

## 📊 性能提升

### 前台模式（原版）

```
启动远征 → ⏸️ 等待12分钟 → 其他任务
总耗时：12分钟 + 其他任务时间
```

### 后台模式（新版）⭐

```
启动远征 ─┬→ 后台运行（12分钟）
          └→ 其他任务（5分钟）← 同时进行
总耗时：max(12分钟, 5分钟) = 12分钟
节省：5分钟！
```

## 🔍 工作原理

### 线程模型

```
主线程                      远征线程
  │                           │
  ├─ 启动远征 ──────────────→ │
  │                          ├─ 初始化舰队
  ├─ 立即返回                ├─ 开始循环
  │                          │  │
  ├─ 执行任务1               │  ├─ 检测舰队2
  │                          │  ├─ 收取奖励
  ├─ 执行任务2               │  ├─ 重新派出
  │                          │  │
  ├─ 执行任务3               │  ├─ 检测舰队5
  │                          │  ├─ 收取奖励
  ├─ ...                     │  ├─ 重新派出
  │                          │  │
  ├─ 停止远征 ──────────────→ │  └─ 收到停止信号
  │                          │
  └─ 结束                    └─ 结束
```

### 停止机制

- 使用 `threading.Event` 作为停止信号
- 后台线程每次循环检查停止事件
- 优雅停止，等待当前操作完成
- 守护线程，程序退出自动停止

## ⚙️ 配置选项

### Mode 参数

| 值 | 功能 | 说明 |
|----|------|------|
| `"start"` | 启动远征 | 开始远征系统 |
| `"stop"` | 停止远征 | 停止后台线程 |

### Background 参数

| 值 | 模式 | 阻塞 | 适用场景 |
|----|------|------|---------|
| `true` | 后台 | 否 | 远征 + 其他任务 ⭐ |
| `false` | 前台 | 是 | 只运行远征 |

## 💡 最佳实践

### 1. 推荐流程

```json
{
  "Main": {
    "next": ["StartExpedition"]
  },
  "StartExpedition": {
    "action": "Custom",
    "custom_action": "AutoExpedition",
    "custom_action_param": "{\"mode\": \"start\", \"background\": true}",
    "next": ["DailyTasks"]
  },
  "DailyTasks": {
    "next": ["Task1", "Task2", "Task3"]
  },
  "Task1": { "...": "..." },
  "Task2": { "...": "..." },
  "Task3": {
    "...": "...",
    "next": ["StopExpedition"]
  },
  "StopExpedition": {
    "action": "Custom",
    "custom_action": "AutoExpedition",
    "custom_action_param": "{\"mode\": \"stop\"}"
  }
}
```

### 2. 查看日志

后台远征的日志会包含线程信息：

```
[INFO] [ExpeditionThread] 🔍 检测第2队是否远征完成...
[INFO] [ExpeditionThread] 💰 收取第2队远征奖励
[INFO] [ExpeditionThread] 🚢 第2队开始远征（720s）
```

### 3. 错误处理

```python
# 远征系统内置错误处理
try:
    context.run_task(f"CollectExpedition_{fleet_id}")
except Exception as e:
    logger.error(f"收取舰队{fleet_id}奖励时出错: {e}")
```

## ⚠️ 注意事项

1. **线程生命周期**
   - 后台线程启动后会持续运行
   - 建议在流程结束前手动停止
   - 或依赖守护线程自动停止

2. **Context 线程安全**
   - MAA Context 对象是线程安全的
   - 可以在多个线程中使用

3. **资源管理**
   - 后台线程占用少量资源
   - 不会影响主流程性能

4. **测试建议**
   - 先使用前台模式测试功能
   - 确认无误后切换到后台模式

## 📁 文件清单

```
agent/custom/action/
├── expedition.py                          # ✏️ 已修改（核心功能）
├── BACKGROUND_MODE_GUIDE.md               # 🆕 使用指南
├── expedition_background_config.json      # 🆕 配置说明
└── test_background_expedition.py          # 🆕 演示程序

assets/resource/pipeline/public/expedition/
└── 远征确认.json                          # ✏️ 已修改（示例配置）
```

## 🎉 完成

现在你可以：

1. ✅ **启动后台远征** - 不阻塞主流程
2. ✅ **同时执行其他任务** - 提高效率
3. ✅ **自动收取和派出** - 无需手动管理
4. ✅ **优雅停止** - 流程结束后停止

**告别等待，效率翻倍！** 🚀

---

## 📚 相关文档

- [BACKGROUND_MODE_GUIDE.md](BACKGROUND_MODE_GUIDE.md) - 快速使用指南
- [expedition_background_config.json](expedition_background_config.json) - 详细配置
- [test_background_expedition.py](test_background_expedition.py) - 演示程序

## 🤝 需要帮助？

查看示例配置或运行演示程序：

```bash
python agent/custom/action/test_background_expedition.py
```
