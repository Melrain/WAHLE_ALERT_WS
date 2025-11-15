# WebSocket 实时监控快速开始

## 1. 启动 Redis

```bash
docker-compose up -d
```

检查 Redis 是否运行：
```bash
docker-compose ps
```

## 2. 安装依赖

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 3. 配置 API 密钥

编辑 `.env` 文件，填入你的 Whale Alert API 密钥：
```env
WHALE_ALERT_API_KEY=your_api_key_here
```

## 4. 运行监控系统

```bash
python main_ws.py
```

## 工作流程

1. **WebSocket 连接**：连接到 Whale Alert WebSocket API
2. **接收事件**：当有大额转账时，自动接收事件
3. **记录基准价格**：获取当前价格作为基准
4. **创建观察窗口**：启动 24 小时观察窗口
5. **定期检查**：每 5 分钟检查价格变化
6. **完成观察**：24 小时后记录最终结果

## 查看数据

### 使用 Python

```python
from src.observers.window_manager import WindowManager

manager = WindowManager()

# 查看活跃观察窗口
active = manager.get_active_windows()
print(f"活跃窗口: {len(active)}")

# 查看已完成结果
results = manager.get_completed_results(limit=10)
for result in results:
    print(f"事件: {result.get('event_id')}, 变化: {result.get('final_change_pct')}%")

# 查看统计信息
stats = manager.get_statistics()
print(stats)
```

### 使用 Redis CLI

```bash
# 连接到Redis
docker-compose exec redis redis-cli

# 查看所有结果
KEYS result:*

# 查看特定事件的结果
HGETALL result:event_12345

# 查看活跃观察窗口
ZRANGE observations:active 0 -1

# 查看统计信息
HGETALL stats:summary
```

## 停止服务

```bash
# 停止监控程序
Ctrl+C

# 停止Redis
docker-compose down
```

## 注意事项

- 确保 Redis 服务正在运行
- WebSocket 连接会自动重连
- 数据会自动过期（事件7天，结果30天）
- 观察窗口默认24小时，可在代码中调整

