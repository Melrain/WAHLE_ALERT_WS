# Railway WebSocket 连接问题修复指南

## 问题描述

部署到 Railway 后，出现以下错误：
```
正在连接到 wss://leviathan.whale-alert.io/ws...
WebSocket错误: Handshake status 200 OK
```

这表示 WebSocket 握手返回了 HTTP 200，但没有成功升级到 WebSocket 连接。

## 可能的原因和解决方案

### 1. API 密钥问题（最常见）

**检查步骤：**

1. **确认环境变量已正确设置**
   - 在 Railway 项目设置中检查 `WHALE_ALERT_API_KEY`
   - 确认没有多余的空格或换行符
   - 确认密钥完整（通常至少 20-30 个字符）

2. **验证 API 密钥有效性**
   - 登录 Whale Alert 控制台：https://whale-alert.io/
   - 检查 API 密钥状态
   - 确认密钥未过期或被撤销

3. **确认订阅计划支持 WebSocket**
   - 某些免费计划可能不支持 WebSocket
   - 需要 Custom Alerts API 订阅
   - 检查你的订阅计划是否包含 WebSocket 功能

### 2. WebSocket 端点问题

**当前使用的端点：**
```
wss://leviathan.whale-alert.io/ws?api_key={your_key}
```

**如果上述端点不工作，尝试：**

1. **检查官方文档**
   - 访问 Whale Alert API 文档
   - 确认最新的 WebSocket 端点

2. **尝试不同的端点格式**
   在 Railway 环境变量中设置：
   ```env
   WHALE_ALERT_WS_URL=wss://api.whale-alert.io/v1/stream?api_key={your_key}
   ```
   或
   ```env
   WHALE_ALERT_WS_URL=wss://api.whale-alert.io/ws/v1/alerts?api_key={your_key}
   ```

### 3. 认证方式问题

**当前方式：** API 密钥通过 URL 参数传递

**如果 URL 参数方式不工作，可能需要：**

1. **使用 HTTP Header 认证**
   - 某些 API 版本可能需要通过 Header 传递密钥
   - 需要修改代码以支持 Header 认证

2. **使用 Bearer Token**
   - 某些 API 可能需要 `Authorization: Bearer {key}` 格式

### 4. Railway 网络环境问题

**可能的问题：**
- Railway 的 IP 可能被 Whale Alert API 限制
- 某些地区可能有网络限制

**解决方案：**
1. 检查 Railway 日志中的完整错误信息
2. 尝试在本地运行相同的代码，确认是否是 Railway 环境问题
3. 联系 Whale Alert 支持，询问是否有 IP 限制

### 5. WebSocket 库兼容性问题

**当前使用：** `websocket-client`

**如果问题持续，可以尝试：**

1. **升级库版本**
   ```bash
   pip install --upgrade websocket-client
   ```

2. **使用其他 WebSocket 库**
   - `websockets` (异步)
   - `socket.io-client`

## 诊断步骤

### 步骤 1: 验证环境变量

在 Railway 日志中应该看到：
```
API 密钥长度: XX 字符
```

如果看到 "API 密钥似乎无效（太短）"，说明环境变量未正确设置。

### 步骤 2: 检查 API 密钥格式

正确的 API 密钥应该：
- 长度至少 20 个字符
- 不包含空格
- 不包含换行符

### 步骤 3: 本地测试

在本地运行相同的代码：
```bash
# 设置环境变量
export WHALE_ALERT_API_KEY=your_key_here
export REDIS_URL=redis://localhost:6379/0

# 运行
python main_ws.py
```

如果本地可以连接，说明是 Railway 环境问题。
如果本地也无法连接，说明是 API 密钥或端点问题。

### 步骤 4: 测试 API 密钥（使用 REST API）

使用 curl 测试 API 密钥是否有效：
```bash
curl "https://api.whale-alert.io/v1/status?api_key=YOUR_API_KEY"
```

如果返回错误，说明 API 密钥无效。

## 临时解决方案

如果 WebSocket 无法连接，可以考虑：

1. **使用 REST API 轮询**
   - 修改代码使用 REST API 定期查询
   - 虽然不如 WebSocket 实时，但更稳定

2. **使用其他部署平台**
   - 尝试 Render、Fly.io 或其他平台
   - 某些平台可能有更好的网络环境

3. **使用代理或 VPN**
   - 如果确认是网络问题，可能需要使用代理

## 联系支持

如果以上方法都无法解决问题：

1. **Whale Alert 支持**
   - 访问 https://whale-alert.io/support
   - 提供错误日志和 API 密钥信息（不要分享完整密钥）

2. **Railway 支持**
   - 检查 Railway 状态页面
   - 联系 Railway 支持

3. **查看项目 Issues**
   - 在 GitHub 上查看是否有类似问题
   - 创建新的 Issue 描述问题

## 更新后的代码特性

最新版本的代码已经包含：

1. ✅ 更详细的错误诊断信息
2. ✅ API 密钥格式验证
3. ✅ 自动重连机制
4. ✅ Ping/Pong 保持连接
5. ✅ 关闭代码解释

## 验证修复

修复后，应该看到：

```
正在连接到 wss://leviathan.whale-alert.io/ws...
API 密钥长度: XX 字符
已发送订阅请求: ...
✓ 订阅成功: ID=..., 币种=[...], 最小金额=$500,000
```

如果看到 "✓ 订阅成功"，说明连接正常。

