# Whale Alert WebSocket 实时监控系统

基于 WebSocket 的实时监控方案，使用 Redis 存储数据，方便多项目共享。

## 功能特性

- ✅ 实时监听 Whale Alert 转账事件（WebSocket）
- ✅ 自动观察事件后的价格变化（24小时窗口）
- ✅ Redis 存储，支持多项目访问
- ✅ 自动完成观察窗口并记录结果
- ✅ 统计信息跟踪

## 快速开始

### 1. 启动 Redis

```bash
docker-compose up -d
```

这会启动一个没有认证的 Redis 服务在 `localhost:6379`。

### 2. 安装依赖

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置 API 密钥

编辑 `.env` 文件：

```env
WHALE_ALERT_API_KEY=your_api_key_here
```

### 4. 运行监控系统

```bash
python main_ws.py
```

## 数据结构

### Redis 键结构

```
event:{event_id}              # 事件数据（Hash）
observation:{event_id}        # 观察窗口（Hash，带TTL）
snapshots:{event_id}          # 价格快照列表（List）
result:{event_id}             # 观察结果（Hash）
observations:active           # 活跃观察列表（Sorted Set）
stats:summary                 # 统计信息（Hash）
```

## 数据访问示例

### Python 示例

```python
from src.storage.redis_client import RedisClient

client = RedisClient()

# 获取所有完成的结果
results = client.get_all_results()
for result in results:
    print(f"事件: {result['event_id']}, 变化: {result['final_change_pct']}%")

# 获取活跃观察窗口
active = client.get_active_observations()
print(f"当前观察中: {len(active)} 个事件")

# 获取统计信息
stats = client.get_stats()
print(stats)
```

### 其他语言

Redis 是标准协议，任何支持 Redis 的语言都可以访问：

```bash
# 使用 redis-cli
redis-cli
> KEYS result:*
> HGETALL result:event_12345
> ZRANGE observations:active 0 -1
```

## 工作流程

1. **WebSocket 接收事件**
   - 监听 Whale Alert WebSocket
   - 收到转账事件时触发

2. **创建观察窗口**
   - 记录事件信息和基准价格
   - 创建 24 小时观察窗口
   - 存储到 Redis

3. **定期检查价格**
   - 每 5 分钟检查所有活跃窗口
   - 获取当前价格并计算变化
   - 记录价格快照

4. **完成观察**
   - 24 小时后自动完成
   - 记录最终结果（方向、变化率等）
   - 更新统计信息

## 配置选项

可以在代码中调整：

- `check_interval`: 价格检查间隔（默认 300 秒 = 5 分钟）
- `window_hours`: 观察窗口时长（默认 24 小时）
- `min_value`: 最小转账金额（在订阅时设置）

## 监控和调试

### 查看活跃观察窗口

```python
from src.observers.window_manager import WindowManager

manager = WindowManager()
active = manager.get_active_windows()
print(f"活跃窗口: {len(active)}")
```

### 查看统计信息

```python
manager = WindowManager()
stats = manager.get_statistics()
print(stats)
```

### 查看事件历史

```python
history = manager.get_event_history('event_id_here')
print(history)
```

## 注意事项

1. **Redis 持久化**: docker-compose 配置了 AOF 持久化，数据会保存到 `redis_data` volume
2. **网络连接**: 确保网络稳定，WebSocket 会自动重连
3. **API 限制**: 注意 Whale Alert API 的速率限制
4. **数据清理**: Redis 数据会自动过期（事件 7 天，结果 30 天）

## 故障排除

### Redis 连接失败

```bash
# 检查 Redis 是否运行
docker-compose ps

# 查看 Redis 日志
docker-compose logs redis

# 重启 Redis
docker-compose restart redis
```

### WebSocket 连接问题

- 检查 API 密钥是否正确
- 检查网络连接
- 查看错误日志

## 下一步

收集足够数据后，可以使用 `src/analyzers/granger_test.py` 进行 Granger 因果检验。

