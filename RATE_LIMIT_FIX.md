# Whale Alert 速率限制问题解决方案

## 问题描述

当看到以下错误时：
```
✗ 订阅错误: alert rate limit exceeded
```

这表示你订阅的币种和区块链组合产生的警报数量超过了 Whale Alert API 的限制。

## 速率限制说明

**Whale Alert API 限制：**
- 每小时最多接收 **100 条警报**
- 如果订阅的币种和区块链组合产生超过 100 条/小时的警报，会触发速率限制

## 解决方案

### 方案 1: 减少订阅的币种数量（推荐）

**当前配置可能订阅了太多币种：**
```
币种=['btc', 'eth', 'sol', 'doge', 'ltc', 'bnb', 'okb', 'usdt', 'usdc']
```

**建议配置（在 Railway 环境变量中设置）：**

```env
# 只订阅 3-5 个主要币种
SYMBOLS=btc,eth,sol

# 区块链留空（监测所有链上的这些币种）
BLOCKCHAINS=

# 保持或增加最小金额
WHALE_ALERT_MIN_VALUE_USD=500000
```

### 方案 2: 增加最小转账金额

如果不想减少币种，可以增加最小转账金额来减少警报数量：

```env
# 增加到 100 万美元
WHALE_ALERT_MIN_VALUE_USD=1000000

# 或更高
WHALE_ALERT_MIN_VALUE_USD=2000000
```

### 方案 3: 减少区块链数量

如果指定了区块链，可以减少区块链数量：

```env
# 只监测主要区块链
BLOCKCHAINS=bitcoin,ethereum,solana

# 或留空以监测所有链（推荐）
BLOCKCHAINS=
```

## 推荐配置

### 配置 A: 保守配置（适合测试）

```env
SYMBOLS=btc,eth
BLOCKCHAINS=
WHALE_ALERT_MIN_VALUE_USD=1000000
```

**预期警报数：** 每小时 20-50 条

### 配置 B: 平衡配置（推荐）

```env
SYMBOLS=btc,eth,sol
BLOCKCHAINS=
WHALE_ALERT_MIN_VALUE_USD=500000
```

**预期警报数：** 每小时 50-80 条

### 配置 C: 积极配置（需要监控）

```env
SYMBOLS=btc,eth,sol,avax,matic
BLOCKCHAINS=
WHALE_ALERT_MIN_VALUE_USD=500000
```

**预期警报数：** 每小时 80-100 条（接近限制）

## 如何在 Railway 中修改配置

1. **登录 Railway 项目**
2. **进入项目设置 → Variables**
3. **修改或添加以下环境变量：**
   - `SYMBOLS` - 币种列表（逗号分隔，小写）
   - `BLOCKCHAINS` - 区块链列表（留空以监测所有链）
   - `WHALE_ALERT_MIN_VALUE_USD` - 最小转账金额（美元）
4. **保存并重新部署**

## 币种选择建议

### 高价值币种（推荐）
- `btc` - Bitcoin（最多大额转账）
- `eth` - Ethereum（第二多）
- `sol` - Solana（快速增长）

### 中等价值币种
- `avax` - Avalanche
- `matic` - Polygon
- `bnb` - Binance Coin

### 稳定币（通常价格变化小）
- `usdt` - Tether
- `usdc` - USD Coin

**注意：** 稳定币的价格变化通常很小（接近 0%），对分析价值有限。

## 监控警报数量

订阅成功后，日志会显示：
```
✓ 订阅成功: ID=..., 币种=[...], 最小金额=$500,000
```

如果频繁看到 `alert rate limit exceeded` 错误，说明需要调整配置。

## 自动处理

代码已经更新，当遇到速率限制错误时会：
1. ✅ 显示详细的错误信息和解决方案
2. ✅ 显示当前配置
3. ✅ 提供建议配置

## 验证修复

修改配置后，重新部署服务。应该看到：
- ✅ 不再出现 `alert rate limit exceeded` 错误
- ✅ 正常接收警报事件
- ✅ 价格获取成功（包括稳定币）

## 其他注意事项

1. **稳定币处理：** 代码已更新，USDT、USDC 等稳定币会自动使用 1.00 作为价格，不会尝试获取不存在的交易对。

2. **价格获取：** 如果某个币种在 Binance 没有对应的 USDT 交易对，会显示警告但不会崩溃。

3. **数据质量：** 减少币种数量可能会错过一些事件，但可以确保在速率限制内稳定运行。

