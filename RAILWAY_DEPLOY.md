# Railway 部署指南

本指南将帮助你将 Whale Alert Trends 项目部署到 Railway。

## 前置要求

1. Railway 账号（https://railway.app）
2. GitHub 仓库（Railway 支持从 GitHub 部署）
3. Whale Alert API 密钥

## 部署步骤

### 1. 准备项目

确保项目已推送到 GitHub 仓库。

### 2. 在 Railway 创建新项目

1. 登录 Railway（https://railway.app）
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择你的仓库

### 3. 添加 Redis 服务

Railway 需要单独添加 Redis 服务：

1. 在项目页面点击 "+ New"
2. 选择 "Database" → "Add Redis"
3. Railway 会自动创建 Redis 实例并设置 `REDIS_URL` 环境变量

### 4. 配置环境变量

在 Railway 项目设置中添加以下环境变量：

#### 必需的环境变量

```env
# Whale Alert API 密钥（必需）
WHALE_ALERT_API_KEY=your_api_key_here

# Redis 配置（Railway 会自动设置 REDIS_URL，通常不需要手动配置）
# REDIS_URL=redis://...  # Railway 会自动提供
```

#### 可选的环境变量

```env
# 订阅的币种列表（逗号分隔，小写）
# 例如: "btc,eth,xrp,usdt"
# 如果留空，API 会自动包含所有币种
SYMBOLS=btc,eth,sol

# 订阅的区块链列表（逗号分隔，小写）
# 例如: "bitcoin,ethereum,ripple"
# 如果留空，API 会自动包含所有区块链（推荐）
BLOCKCHAINS=

# 最小转账金额（美元）
# 默认值: 500000（50万美元）
WHALE_ALERT_MIN_VALUE_USD=500000

# Binance API（可选，如果不需要高级功能可以不设置）
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret

# 默认交易对
DEFAULT_SYMBOL=BTCUSDT

# 时区
DEFAULT_TIMEZONE=UTC
```

### 5. 部署配置

Railway 会自动检测并使用以下文件：
- `Dockerfile` - 用于构建 Docker 镜像
- `Procfile` - 用于指定启动命令
- `railway.json` - Railway 特定配置（可选）

### 6. 部署

Railway 会在你推送代码到 GitHub 时自动部署。你也可以：

1. 在 Railway 项目页面点击 "Deploy"
2. 或者推送代码到 GitHub，Railway 会自动触发部署

## 重要注意事项

### 1. Redis 配置

- Railway 会自动创建 Redis 服务并设置 `REDIS_URL` 环境变量
- 你的代码已经支持通过 `REDIS_URL` 连接 Redis
- **不需要**手动配置 `REDIS_HOST`、`REDIS_PORT` 等

### 2. 长期运行

- 这是一个长期运行的后台服务（WebSocket 监控）
- Railway 会保持服务运行，即使没有 HTTP 请求
- 如果服务崩溃，Railway 会自动重启（根据 `railway.json` 配置）
- **注意**: 这是一个 `worker` 类型的服务，不是 `web` 服务，所以不需要监听 HTTP 端口

### 3. 日志查看

在 Railway 项目页面可以查看实时日志：
- 点击服务名称
- 查看 "Logs" 标签页

### 4. 数据持久化

- Redis 数据会持久化到 Railway 的存储
- 如果删除 Redis 服务，数据会丢失
- 建议定期备份重要数据

### 5. 资源限制

Railway 免费版有一些限制：
- 每月 $5 免费额度
- 服务可能会在空闲时休眠（对于 worker 服务，通常不会休眠）
- 建议升级到付费计划以确保 24/7 运行
- Worker 服务通常比 Web 服务更稳定，因为不需要处理 HTTP 请求

### 6. 环境变量安全

- **不要**在代码中硬编码 API 密钥
- 使用 Railway 的环境变量功能
- 敏感信息（如 API 密钥）会自动加密

## 验证部署

部署成功后，检查日志确认：

1. ✅ Redis 连接成功
2. ✅ WebSocket 连接成功
3. ✅ 订阅成功
4. ✅ 开始接收事件

示例日志：
```
Redis连接成功: ...
正在连接到 wss://leviathan.whale-alert.io/ws...
✓ 订阅成功: ID=..., 币种=[...], 最小金额=$500,000
✓ 新事件: ...
```

## 故障排除

### 问题 1: Redis 连接失败

**错误信息**: `Redis连接失败: ...`

**解决方案**:
1. 确认已添加 Redis 服务
2. 检查 `REDIS_URL` 环境变量是否正确设置
3. 查看 Railway Redis 服务的日志

### 问题 2: WebSocket 连接失败

**错误信息**: `WebSocket错误: Handshake status 200 OK`

**这是最常见的 WebSocket 问题，可能的原因：**

1. **API 密钥问题**
   - 检查 `WHALE_ALERT_API_KEY` 是否正确设置
   - 确认密钥未过期
   - 确认订阅计划支持 WebSocket/Custom Alerts

2. **端点问题**
   - 当前使用: `wss://leviathan.whale-alert.io/ws?api_key={key}`
   - 如果不行，尝试设置 `WHALE_ALERT_WS_URL` 环境变量使用其他端点

3. **认证方式**
   - 某些 API 版本可能需要不同的认证方式
   - 检查 Whale Alert 官方文档

**详细解决方案请参考**: [RAILWAY_WEBSOCKET_FIX.md](./RAILWAY_WEBSOCKET_FIX.md)

**快速检查**:
1. 在 Railway 日志中查看 "API 密钥长度" 信息
2. 如果看到 "API 密钥似乎无效"，检查环境变量
3. 尝试在本地运行相同代码，确认是否是 Railway 环境问题

### 问题 3: 服务频繁重启

**可能原因**:
- 代码错误导致崩溃
- 内存不足
- Redis 连接问题

**解决方案**:
1. 查看日志找出崩溃原因
2. 检查资源使用情况
3. 优化代码减少内存使用

### 问题 4: 没有收到事件

**可能原因**:
- 订阅配置不正确
- 最小金额设置过高
- API 密钥权限不足

**解决方案**:
1. 检查订阅日志（应该显示 "✓ 订阅成功"）
2. 降低 `WHALE_ALERT_MIN_VALUE_USD` 测试
3. 确认 API 密钥有 WebSocket 权限

## 监控和维护

### 查看统计信息

可以通过日志或 Redis 查看统计信息。如果需要，可以添加一个简单的 HTTP 端点来查看统计信息。

### 更新代码

1. 推送代码到 GitHub
2. Railway 会自动检测并重新部署
3. 查看部署日志确认成功

### 备份数据

定期从 Redis 导出重要数据：
- 使用 Railway CLI 或 Web UI
- 或者添加定期备份脚本

## 成本估算

### Railway 免费版
- $5 免费额度/月
- 适合测试和小规模使用

### Railway 付费版
- 按使用量计费
- 长期运行的服务建议使用付费版

### 建议
- 开发/测试：使用免费版
- 生产环境：使用付费版或考虑其他平台（如 Render、Fly.io）

## 相关资源

- [Railway 文档](https://docs.railway.app)
- [Railway 定价](https://railway.app/pricing)
- [项目 README](./README.md)

