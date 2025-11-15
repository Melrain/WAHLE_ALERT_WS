# WebSocket 连接问题排查指南

## 问题：404 Not Found 错误

如果遇到 `404 Not Found` 错误，说明 WebSocket 端点可能不正确。

## 解决方案

### 1. 查找正确的端点

请查看 Whale Alert 官方文档，确认 Custom Alerts API 的正确 WebSocket 端点。通常可以在以下位置找到：
- API 文档页面
- 开发者控制台
- 支持邮件

### 2. 配置自定义端点

如果找到了正确的端点，可以在 `.env` 文件中配置：

```env
WHALE_ALERT_WS_URL=wss://api.whale-alert.io/正确的路径
```

例如：
```env
WHALE_ALERT_WS_URL=wss://api.whale-alert.io/v1/custom-alerts
```

### 3. 自动尝试多个端点

代码会自动尝试以下端点（按顺序）：
1. `wss://api.whale-alert.io/v1/alerts`
2. `wss://api.whale-alert.io/v1/stream`
3. `wss://api.whale-alert.io/v1/ws`
4. `wss://api.whale-alert.io/ws/v1/alerts`

如果某个端点返回 404，会自动尝试下一个。

### 4. 认证方式

代码会尝试多种认证方式：
- 通过 HTTP Header: `X-API-Key`, `Authorization: Bearer {key}`, `api_key`
- 通过 URL 参数: `?api_key={key}`（如果端点支持）

### 5. 检查 API 密钥

确保 `.env` 文件中的 `WHALE_ALERT_API_KEY` 是正确的，并且：
- 密钥没有多余的空格
- 密钥是 Custom Alerts API 的有效密钥
- 密钥对应的订阅计划支持 WebSocket

### 6. 联系支持

如果所有端点都失败，请：
1. 查看 Whale Alert 官方文档
2. 联系 Whale Alert 技术支持
3. 在 GitHub Issues 中报告问题（如果适用）

## 调试信息

运行程序时，会显示：
- 当前尝试的端点（不包含 API key）
- 连接错误详情
- 自动切换端点的提示

## 常见端点格式

根据不同的 API 提供商，WebSocket 端点可能有以下格式：
- `wss://api.example.com/v1/stream`
- `wss://api.example.com/ws`
- `wss://ws.example.com/v1/alerts`
- `wss://api.example.com/v1/alerts?api_key=xxx`

请根据 Whale Alert 官方文档确认正确的格式。

