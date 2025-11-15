# Whale Alert 与 Binance 价格关联性分析

这个项目用于分析 Whale Alert API 提供的鲸鱼转账数据与 Binance API 提供的加密货币价格数据之间的关联性。

## 项目概述

本项目包含两个主要功能：

1. **实时数据收集系统** (`main_ws.py`): 通过 WebSocket 实时监听 Whale Alert 转账事件，自动跟踪价格变化，并将数据存储到 Redis
2. **历史数据分析** (`main.py`): 使用历史数据进行 Granger 因果检验和相关性分析

## 安装

1. **创建虚拟环境**（如果还没有）：
```bash
python3 -m venv venv
```

2. **激活虚拟环境**：
```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. **安装依赖**：
```bash
pip install -r requirements.txt
```

4. **配置环境变量**：
```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的配置
# 主要配置项：
# - WHALE_ALERT_API_KEY: Whale Alert API 密钥（必需）
# - SYMBOLS: 订阅的币种列表，逗号分隔（如 "btc,eth,xrp"）
# - BLOCKCHAINS: 订阅的区块链列表，逗号分隔（如 "bitcoin,ethereum"）
# - WHALE_ALERT_MIN_VALUE_USD: 最小转账金额（美元，默认 500000）
```

5. **启动 Redis**：
```bash
docker-compose up -d
```

这会启动：
- Redis 服务（端口 6379）
- Redis Insight 可视化工具（端口 8001，访问 http://localhost:8001）

## 使用方法

### 实时数据收集（推荐）

运行实时监控系统：

```bash
python main_ws.py
```

系统会：
1. 连接 Whale Alert WebSocket API
2. 实时接收转账事件（默认最小金额 $500,000）
3. 自动获取转账发生时的基准价格
4. 每 5 分钟检查一次价格变化
5. 24 小时后自动完成观察并保存结果
6. 所有数据存储到 Redis

### 历史数据分析

运行历史数据分析：

```bash
python main.py
```

程序会：
1. 从 Whale Alert API 收集最近30天的转账数据
2. 从 Binance API 收集对应的K线数据
3. 对数据进行处理和对齐
4. 执行相关性分析和 Granger 因果检验
5. 生成可视化图表和分析报告

## Redis 数据结构详解

系统使用 Redis 存储所有数据，数据结构如下：

### 1. 事件数据 (`event:{event_id}`)

**类型**: Hash  
**过期时间**: 7 天  
**说明**: 存储转账事件的详细信息

**字段说明**:

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `timestamp` | string | 转账发生时间（ISO 格式） | `2025-11-15T08:00:00.123456` |
| `amount` | string | 转账数量（币种单位） | `179.0` |
| `amount_usd` | string | 转账金额（美元） | `563558.0` |
| `currency` | string | 币种代码（小写） | `eth` |
| `from_address` | string | 发送方地址或名称 | `Bitfinex` 或 `0x1234...5678` |
| `to_address` | string | 接收方地址或名称 | `Unknown wallet` 或 `0xabcd...efgh` |
| `blockchain` | string | 区块链名称 | `ethereum`, `bitcoin` |
| `transaction_type` | string | 交易类型 | `transfer`, `mint`, `burn` |
| `channel_id` | string | 频道ID | `Gi7HlomR` |
| `text` | string | 事件描述文本 | `179 ETH (563,558 USD) transferred from Bitfinex to ...` |
| `baseline_price` | string | 基准价格（转账时的价格，美元） | `3146.54` |
| `baseline_time` | string | 基准价格记录时间（ISO 格式） | `2025-11-15T08:00:00.123456` |
| `status` | string | 状态 | `observing` |

**示例数据**:
```json
{
  "timestamp": "2025-11-15T08:00:00.123456",
  "amount": "179.0",
  "amount_usd": "563558.0",
  "currency": "eth",
  "from_address": "Bitfinex",
  "to_address": "0x1234567890abcdef1234567890abcdef12345678",
  "blockchain": "ethereum",
  "transaction_type": "transfer",
  "channel_id": "Gi7HlomR",
  "text": "179 ETH (563,558 USD) transferred from Bitfinex to ...",
  "baseline_price": "3146.54",
  "baseline_time": "2025-11-15T08:00:00.123456",
  "status": "observing"
}
```

### 2. 观察窗口 (`observation:{event_id}`)

**类型**: Hash  
**过期时间**: 观察窗口时长 + 1 小时  
**说明**: 存储观察窗口的配置和状态

**字段说明**:

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `baseline_price` | string | 基准价格（美元） | `3146.54` |
| `baseline_time` | string | 基准时间（ISO 格式） | `2025-11-15T08:00:00.123456` |
| `window_hours` | string | 观察窗口小时数 | `24` |
| `status` | string | 状态 | `observing` 或 `completed` |
| `expires_at` | string | 过期时间（ISO 格式） | `2025-11-16T08:00:00.123456` |

**示例数据**:
```json
{
  "baseline_price": "3146.54",
  "baseline_time": "2025-11-15T08:00:00.123456",
  "window_hours": "24",
  "status": "observing",
  "expires_at": "2025-11-16T08:00:00.123456"
}
```

### 3. 价格快照 (`snapshots:{event_id}`)

**类型**: List（JSON 字符串列表）  
**过期时间**: 7 天  
**说明**: 存储观察窗口内的所有价格快照

**快照格式**（每个元素是 JSON 字符串）:

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `time` | string | 快照时间（ISO 格式） | `2025-11-15T08:05:00.123456` |
| `price` | string | 当前价格（美元） | `3150.20` |
| `change_pct` | string | 价格变化百分比 | `0.12` |

**计算公式**:
```
change_pct = ((current_price - baseline_price) / baseline_price) * 100
```

**示例数据**:
```json
[
  {
    "time": "2025-11-15T08:05:00.123456",
    "price": "3148.50",
    "change_pct": "0.06"
  },
  {
    "time": "2025-11-15T08:10:00.123456",
    "price": "3149.20",
    "change_pct": "0.08"
  },
  {
    "time": "2025-11-15T08:15:00.123456",
    "price": "3150.10",
    "change_pct": "0.11"
  }
]
```

**注意**: 
- 每 5 分钟记录一次快照
- 24 小时观察窗口约产生 288 个快照（24 × 60 / 5）
- 所有快照按时间顺序存储在列表中

### 4. 观察结果 (`result:{event_id}`)

**类型**: Hash  
**过期时间**: 30 天  
**说明**: 存储观察窗口完成后的最终结果

**字段说明**:

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `final_price` | string | 最终价格（美元） | `3150.20` |
| `final_change_pct` | string | 最终变化百分比 | `0.12` |
| `direction` | string | 价格方向 | `up` 或 `down` |
| `max_change_pct` | string | 观察窗口内最大变化百分比 | `0.25` |
| `min_change_pct` | string | 观察窗口内最小变化百分比 | `-0.15` |
| `completed_at` | string | 完成时间（ISO 格式） | `2025-11-16T08:00:00.123456` |

**示例数据**:
```json
{
  "final_price": "3150.20",
  "final_change_pct": "0.12",
  "direction": "up",
  "max_change_pct": "0.25",
  "min_change_pct": "-0.15",
  "completed_at": "2025-11-16T08:00:00.123456"
}
```

### 5. 活跃观察列表 (`observations:active`)

**类型**: Sorted Set  
**说明**: 存储所有正在观察的事件ID，使用时间戳作为分数

**数据结构**:
- **Key**: `observations:active`
- **Value**: 事件ID（如 `0x4a70ff85580706d...`）
- **Score**: 观察窗口创建时间的时间戳

**用途**: 快速查找所有正在观察的事件

### 6. 统计信息 (`stats:summary`)

**类型**: Hash  
**说明**: 存储系统整体统计信息

**字段说明**:

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `total_events` | string | 总事件数 | `150` |
| `observing_count` | string | 正在观察的事件数 | `45` |
| `completed_count` | string | 已完成的事件数 | `105` |
| `up_count` | string | 价格上涨的事件数 | `60` |
| `down_count` | string | 价格下跌的事件数 | `45` |
| `updated_at` | string | 最后更新时间（ISO 格式） | `2025-11-15T08:00:00.123456` |

**示例数据**:
```json
{
  "total_events": "150",
  "observing_count": "45",
  "completed_count": "105",
  "up_count": "60",
  "down_count": "45",
  "updated_at": "2025-11-15T08:00:00.123456"
}
```

## 数据访问示例

### Python 示例

#### 1. 获取所有完成的结果（用于 Granger 分析）

```python
from src.storage.redis_client import RedisClient
import pandas as pd
from datetime import datetime

client = RedisClient()

# 获取所有完成的结果
results = client.get_all_results()

# 构建时间序列数据
events = []
price_changes = []
timestamps = []

for result in results:
    event_id = result.get('event_id', '')
    if not event_id:
        continue
    
    # 获取事件信息
    event = client.get_event(event_id)
    if not event:
        continue
    
    # 获取时间戳
    timestamp_str = event.get('timestamp', '')
    if not timestamp_str:
        continue
    
    try:
        timestamp = pd.to_datetime(timestamp_str)
        timestamps.append(timestamp)
        
        # 转账金额（USD）- 用于 X 序列
        amount_usd = float(event.get('amount_usd', 0))
        events.append(amount_usd)
        
        # 价格变化百分比 - 用于 Y 序列
        change_pct = float(result.get('final_change_pct', 0))
        price_changes.append(change_pct)
        
    except Exception as e:
        print(f"处理事件 {event_id} 时出错: {e}")
        continue

# 创建时间序列
df = pd.DataFrame({
    'timestamp': timestamps,
    'event_amount': events,
    'price_change': price_changes
}).sort_values('timestamp')

# 创建 pandas Series（用于 Granger 检验）
X = pd.Series(df['event_amount'].values, index=df['timestamp'], name='转账金额')
Y = pd.Series(df['price_change'].values, index=df['timestamp'], name='价格变化')

print(f"数据点数量: {len(X)}")
print(f"时间范围: {X.index.min()} 到 {X.index.max()}")
```

#### 2. 获取特定事件的所有快照

```python
from src.storage.redis_client import RedisClient
import pandas as pd

client = RedisClient()

# 获取事件ID（从结果中）
results = client.get_all_results()
event_id = results[0]['event_id']  # 使用第一个事件

# 获取所有快照
snapshots = client.get_price_snapshots(event_id)

# 转换为 DataFrame
df = pd.DataFrame(snapshots)
df['time'] = pd.to_datetime(df['time'])
df['price'] = df['price'].astype(float)
df['change_pct'] = df['change_pct'].astype(float)

print(df.head())
```

#### 3. 获取统计信息

```python
from src.storage.redis_client import RedisClient

client = RedisClient()

# 获取统计信息
stats = client.get_stats()

print(f"总事件数: {stats.get('total_events', 0)}")
print(f"观察中: {stats.get('observing_count', 0)}")
print(f"已完成: {stats.get('completed_count', 0)}")
print(f"上涨: {stats.get('up_count', 0)}")
print(f"下跌: {stats.get('down_count', 0)}")
```

#### 4. 获取活跃观察窗口

```python
from src.storage.redis_client import RedisClient

client = RedisClient()

# 获取所有活跃的观察窗口
active_events = client.get_active_observations()

print(f"当前有 {len(active_events)} 个活跃观察窗口")

for event_id in active_events[:5]:  # 显示前5个
    observation = client.get_observation(event_id)
    event = client.get_event(event_id)
    
    print(f"\n事件ID: {event_id[:16]}...")
    print(f"币种: {event.get('currency', 'N/A')}")
    print(f"金额: ${float(event.get('amount_usd', 0)):,.0f}")
    print(f"基准价格: ${float(observation.get('baseline_price', 0)):,.2f}")
    print(f"状态: {observation.get('status', 'N/A')}")
```

### Redis CLI 示例

```bash
# 连接到 Redis
redis-cli

# 查看所有事件
KEYS event:*

# 查看特定事件
HGETALL event:0x4a70ff85580706d

# 查看所有结果
KEYS result:*

# 查看特定结果
HGETALL result:0x4a70ff85580706d

# 查看活跃观察列表
ZRANGE observations:active 0 -1

# 查看统计信息
HGETALL stats:summary

# 查看快照（需要先知道 event_id）
LRANGE snapshots:0x4a70ff85580706d 0 -1
```

## Granger 因果检验数据准备

### 数据要求

- **最小数据量**: 至少 34 个完成的事件（如果 `max_lag=24`）
- **推荐数据量**: 50-100 个完成的事件（结果更可靠）
- **理想数据量**: 100+ 个完成的事件（统计显著性更好）

### 数据准备步骤

1. **确保有足够的数据**:
```python
from src.storage.redis_client import RedisClient

client = RedisClient()
results = client.get_all_results()

if len(results) < 34:
    print(f"数据不足: 只有 {len(results)} 个完成的事件，需要至少 34 个")
    print(f"还需要: {34 - len(results)} 个事件")
else:
    print(f"数据充足: 有 {len(results)} 个完成的事件，可以开始分析")
```

2. **构建时间序列**:
```python
# 使用上面的示例代码构建 X 和 Y 序列
# X: 转账金额序列（自变量）
# Y: 价格变化序列（因变量）
```

3. **执行 Granger 检验**:
```python
from src.analyzers.granger_test import granger_causality_test

result = granger_causality_test(
    X=X,  # 转账金额序列
    Y=Y,  # 价格变化序列
    max_lag=24,
    significance_level=0.05,
    verbose=True,
    auto_stationary=True
)

if result.get('has_causality'):
    print("✓ 发现因果关系！")
    print(f"最优滞后阶数: {result.get('optimal_lag')}")
    print(f"最小p值: {result.get('min_p_value'):.4f}")
else:
    print("✗ 未发现因果关系")
```

### 数据字段映射

| Granger 检验 | Redis 数据源 | 字段路径 |
|-------------|-------------|----------|
| X (自变量) | `event:{event_id}` | `amount_usd` |
| Y (因变量) | `result:{event_id}` | `final_change_pct` |
| 时间索引 | `event:{event_id}` | `timestamp` |

## 项目结构

```
whale_alert_trends/
├── config/                 # 配置文件
│   └── settings.py        # 配置设置
├── src/                   # 源代码
│   ├── data_collectors/  # 数据收集器
│   │   ├── whale_alert.py
│   │   └── binance.py
│   ├── data_processors/  # 数据处理
│   │   ├── aggregator.py
│   │   └── aligner.py
│   ├── analyzers/        # 分析模块
│   │   ├── granger_test.py
│   │   └── correlation.py
│   ├── observers/        # 观察器
│   │   ├── price_observer.py
│   │   └── window_manager.py
│   ├── storage/          # 存储模块
│   │   └── redis_client.py
│   ├── websocket/       # WebSocket 客户端
│   │   └── whale_alert_ws.py
│   └── utils/           # 工具函数
│       └── visualizer.py
├── data/                 # 数据目录
│   ├── raw/             # 原始数据
│   ├── processed/       # 处理后的数据
│   └── results/         # 分析结果
├── main_ws.py          # 实时监控主程序
├── main.py             # 历史数据分析主程序
├── docker-compose.yml  # Docker 配置
├── requirements.txt    # 依赖包
└── README.md          # 说明文档
```

## 核心功能

### 1. 实时数据收集

- **WebSocket 监听**: 实时接收 Whale Alert 转账事件
- **价格跟踪**: 自动获取转账发生时的基准价格
- **定期检查**: 每 5 分钟检查一次价格变化
- **自动完成**: 24 小时后自动完成观察并保存结果

### 2. 数据处理

- **数据聚合**: 将离散的转账事件聚合为时间序列
- **数据对齐**: 对齐不同频率的时间序列数据
- **数据存储**: Redis 持久化存储，支持多项目访问

### 3. 统计分析

- **相关性分析**: Pearson 和 Spearman 相关系数
- **滞后相关性**: 分析不同时间滞后的相关性
- **Granger 因果检验**: 检验转账事件是否对价格变化有预测能力

### 4. 可视化

- **Redis Insight**: 通过 Web UI 查看数据
- **时间序列图**: 可视化价格变化趋势
- **Granger 检验结果图**: 可视化检验结果

## 配置选项

### 环境变量

在 `.env` 文件中配置：

```env
# Whale Alert API
WHALE_ALERT_API_KEY=your_api_key_here
WHALE_ALERT_WS_URL=  # 可选，自定义 WebSocket 端点

# Binance API（可选）
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret

# Redis 配置（优先使用 REDIS_URL）
# 方式1: 使用 URL（推荐）
REDIS_URL=redis://localhost:6379/0
# 如果有密码: redis://:password@localhost:6379/0

# 方式2: 分别配置（向后兼容，如果未设置 REDIS_URL 时使用）
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0
# REDIS_PASSWORD=
```

### 代码配置

在 `main_ws.py` 中可以调整：

- `check_interval`: 价格检查间隔（默认 300 秒 = 5 分钟）
- `window_hours`: 观察窗口时长（默认 24 小时）

### 环境变量配置

在 `.env` 文件中可以配置订阅参数：

根据官方文档，`blockchains` 和 `symbols` 都是**可选参数**：
- 如果省略 `blockchains`，API 会自动包含所有区块链（推荐）
- 如果省略 `symbols`，API 会自动包含所有币种
- 只有 `min_value_usd` 是必需参数

- `SYMBOLS`: 币种列表，逗号分隔（如 `"btc,eth,xrp,usdt"`）
  - 支持的币种：btc, eth, xrp, usdt, bnb, ada, sol, dot, matic, avax 等
  - **可选参数**：如果留空或设置为空字符串，API 会自动包含所有币种
  - 默认值：空（不指定币种，自动包含所有币种）
  - **注意**：Whale Alert API 每小时最多接收 100 条警报，建议根据需求选择币种数量
  
- `BLOCKCHAINS`: 区块链列表，逗号分隔（如 `"bitcoin,ethereum,ripple"`）
  - 支持的区块链：bitcoin, ethereum, solana, avalanche, polygon, bsc, ripple, tron 等
  - **可选参数**：如果留空或设置为空字符串，API 会自动包含所有区块链（推荐）
  - 默认值：空（不指定区块链，自动监测所有链）
  - **注意**：某些区块链名称可能不同，如 "binance" 应该是 "bsc"

- `WHALE_ALERT_MIN_VALUE_USD`: 最小转账金额（美元）
  - **必需参数**：最小值为 100,000 美元
  - 默认值：`500000`（50万美元）

**推荐配置**（只指定币种，让 API 自动监测所有链）：
```env
# 只指定币种，不指定区块链（推荐）
SYMBOLS=btc,eth,sol,avax,matic,usdt,bnb,xrp
# BLOCKCHAINS 留空，API 会自动监测所有链上的这些币种

# 最小转账金额
WHALE_ALERT_MIN_VALUE_USD=500000
```

**其他配置示例**：
```env
# 示例1: 指定币种和特定区块链
SYMBOLS=eth,usdt
BLOCKCHAINS=ethereum,polygon

# 示例2: 只指定币种，监测所有链（推荐）
SYMBOLS=btc,eth,sol
# BLOCKCHAINS 留空

# 示例3: 只指定区块链，监测所有币种
BLOCKCHAINS=bitcoin,ethereum
# SYMBOLS 留空

# 示例4: 监测所有币种和所有链（不推荐，可能超过每小时100条限制）
# SYMBOLS 和 BLOCKCHAINS 都留空
```

**币种数量建议**：
- 如果每小时事件较少（< 20 个）：可以订阅 5-10 个币种
- 如果每小时事件较多（20-50 个）：建议订阅 3-5 个币种
- 如果每小时事件很多（> 50 个）：建议订阅 1-3 个币种，避免超过每小时 100 条警报的限制

## 注意事项

1. **API 密钥**: 需要有效的 Whale Alert API 密钥（Custom Alerts API 订阅）
2. **数据量**: 确保有足够的数据点（建议至少 50 个完成的事件）才能进行可靠的统计分析
3. **时间范围**: 实时系统需要运行至少 24 小时才能获得第一批完成的数据
4. **Redis 持久化**: docker-compose 配置了 AOF 持久化，数据会保存到 `redis_data` volume
5. **数据过期**: Redis 数据会自动过期（事件 7 天，结果 30 天）
6. **网络连接**: 确保网络稳定，WebSocket 会自动重连

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
- 参考 `WEBSOCKET_TROUBLESHOOTING.md`

### 数据不足

```python
from src.storage.redis_client import RedisClient

client = RedisClient()
results = client.get_all_results()

print(f"已完成事件数: {len(results)}")
print(f"需要至少 34 个事件才能开始 Granger 检验")
```

## 技术栈

- **数据处理**: pandas, numpy
- **统计分析**: statsmodels, scipy
- **API调用**: requests, websocket-client
- **数据存储**: redis
- **可视化**: matplotlib, seaborn, plotly
- **时间序列分析**: statsmodels

## 下一步

1. **收集数据**: 运行 `main_ws.py` 持续收集数据
2. **等待数据**: 至少等待 24 小时获得第一批完成的数据
3. **执行分析**: 使用收集的数据执行 Granger 因果检验
4. **优化策略**: 根据分析结果优化观察参数和策略

## 许可证

MIT License
# WAHLE_ALERT_WS
