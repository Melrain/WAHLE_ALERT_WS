"""Whale Alert WebSocket客户端"""
import websocket
import json
import threading
from datetime import datetime
from typing import Optional
import time

from src.storage.redis_client import RedisClient
from src.data_collectors.binance import BinanceCollector
from config import settings


class WhaleAlertWebSocket:
    """Whale Alert WebSocket客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化WebSocket客户端
        
        参数:
        - api_key: Whale Alert API密钥
        """
        self.api_key = api_key or settings.WHALE_ALERT_API_KEY
        if not self.api_key:
            raise ValueError("需要提供Whale Alert API密钥")
        
        # WebSocket URL - 根据官方文档：wss://leviathan.whale-alert.io/ws?api_key={api_key}
        # 如果配置了自定义端点，优先使用
        custom_ws_url = settings.WHALE_ALERT_WS_URL
        if custom_ws_url:
            self.ws_url = custom_ws_url
        else:
            # 官方端点
            self.ws_url = f"wss://leviathan.whale-alert.io/ws?api_key={self.api_key}"
        
        # 初始化Redis和Binance客户端
        self.redis_client = RedisClient()
        self.binance = BinanceCollector()
        
        self.ws = None
        self.running = False
        self.reconnect_delay = 5  # 重连延迟（秒）
        self.subscribed = False  # 订阅状态
    
    def on_message(self, ws, message):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            
            # 检查是否有错误
            if 'error' in data:
                error_msg = data.get('error', 'Unknown error')
                print(f"✗ 订阅错误: {error_msg}")
                print(f"完整错误信息: {data}")
                
                # 处理不同类型的错误
                error_lower = error_msg.lower()
                
                if 'rate limit' in error_lower or 'limit exceeded' in error_lower:
                    print("\n⚠️  警报速率限制超出！")
                    print("Whale Alert API 每小时最多接收 100 条警报")
                    print("\n解决方案：")
                    print("1. 减少订阅的币种数量（建议 3-5 个主要币种）")
                    print("2. 减少订阅的区块链数量（或留空以监测所有链）")
                    print("3. 增加最小转账金额（WHALE_ALERT_MIN_VALUE_USD）")
                    print("\n当前订阅配置：")
                    print(f"  - 币种: {settings.SYMBOLS if settings.SYMBOLS else '所有币种'}")
                    print(f"  - 区块链: {settings.BLOCKCHAINS if settings.BLOCKCHAINS else '所有链'}")
                    print(f"  - 最小金额: ${settings.WHALE_ALERT_MIN_VALUE_USD:,.0f}")
                    print("\n建议配置（在 Railway 环境变量中设置）：")
                    print("  SYMBOLS=btc,eth,sol")
                    print("  BLOCKCHAINS=  # 留空，监测所有链")
                    print("  WHALE_ALERT_MIN_VALUE_USD=1000000  # 增加到 100 万美元")
                    
                elif 'blockchain' in error_lower:
                    print("\n提示: 可能某些区块链名称不正确")
                    print("常见正确的区块链名称: bitcoin, ethereum, solana, avalanche, polygon, bsc, ripple, tron")
                    print("如果只想订阅币种，可以尝试不提供 blockchains 参数")
                    
                elif 'api' in error_lower or 'key' in error_lower or 'auth' in error_lower:
                    print("\n⚠️  API 认证错误")
                    print("请检查 WHALE_ALERT_API_KEY 环境变量是否正确设置")
                    
                return
            
            # 根据官方文档，消息类型通过 'type' 字段判断
            msg_type = data.get('type', '')
            
            if msg_type == 'subscribed_alerts':
                # 订阅确认消息（注意：返回的是 'subscribed_alerts' 不是 'subscribe_alerts'）
                self.subscribed = True
                print(f"✓ 订阅成功: ID={data.get('id', 'N/A')}, "
                      f"区块链={data.get('blockchains', [])}, "
                      f"币种={data.get('symbols', [])}, "
                      f"交易类型={data.get('tx_types', [])}, "
                      f"最小金额=${data.get('min_value_usd', 0):,.0f}")
            elif 'channel_id' in data or 'transaction' in data:
                # 这是实际的警报消息（AlertJSON格式）
                self.handle_alert(data)
            else:
                # 其他类型的消息
                print(f"收到消息: {data}")
                
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}, 消息: {message[:100]}")
        except Exception as e:
            print(f"处理消息错误: {e}")
    
    def handle_alert(self, alert_data: dict):
        """
        处理警报数据（AlertJSON格式）
        
        参数:
        - alert_data: 警报数据字典，格式参考官方文档的 AlertJSON
        """
        # 根据官方文档，使用 transaction.hash 作为 event_id
        transaction = alert_data.get('transaction', {})
        event_id = transaction.get('hash', '')
        
        if not event_id:
            print("警告: 收到的事件没有交易哈希")
            return
        
        try:
            # 获取 amounts 数组（可能包含多个币种）
            amounts = alert_data.get('amounts', [])
            if not amounts:
                print(f"警告: 事件 {event_id[:8]}... 没有金额信息")
                return
            
            # 处理第一个币种（如果有多个，可以扩展处理）
            first_amount = amounts[0]
            currency = first_amount.get('symbol', 'btc').lower()
            amount = float(first_amount.get('amount', 0))
            amount_usd = float(first_amount.get('value_usd', 0))
            
            # 获取当前价格（BinanceCollector 会处理稳定币和交易对转换）
            current_price = self.binance.get_current_price(currency)
            
            if not current_price:
                print(f"无法获取价格: {currency.upper()}，跳过事件 {event_id[:8]}...")
                return
            
            # 准备事件数据
            timestamp = alert_data.get('timestamp', 0)
            if isinstance(timestamp, (int, float)) and timestamp > 0:
                timestamp = datetime.fromtimestamp(timestamp).isoformat()
            else:
                timestamp = datetime.now().isoformat()
            
            event_data = {
                "timestamp": timestamp,
                "amount": str(amount),
                "amount_usd": str(amount_usd),
                "currency": currency,
                "from_address": alert_data.get('from', ''),
                "to_address": alert_data.get('to', ''),
                "blockchain": alert_data.get('blockchain', ''),
                "transaction_type": alert_data.get('transaction_type', ''),
                "channel_id": alert_data.get('channel_id', ''),
                "text": alert_data.get('text', ''),
                "baseline_price": str(current_price),
                "baseline_time": datetime.now().isoformat(),
                "status": "observing"
            }
            
            # 保存事件到Redis
            self.redis_client.save_event(event_id, event_data)
            
            # 创建观察窗口（默认24小时）
            self.redis_client.create_observation(
                event_id=event_id,
                baseline_price=current_price,
                window_hours=24
            )
            
            # 格式化显示转账方向
            from_addr = alert_data.get('from', 'Unknown')
            to_addr = alert_data.get('to', 'Unknown')
            # 如果地址太长，截断显示
            from_display = from_addr[:20] + '...' if len(from_addr) > 20 else from_addr
            to_display = to_addr[:20] + '...' if len(to_addr) > 20 else to_addr
            
            print(f"✓ 新事件: {event_id[:16]}... | "
                  f"从 {from_display} → {to_display} | "
                  f"{amount:,.2f} {currency.upper()} (${amount_usd:,.0f}) | "
                  f"价格: ${current_price:,.2f}")
            
        except Exception as e:
            print(f"处理警报错误: {e}, 数据: {alert_data}")
    
    def on_error(self, ws, error):
        """处理错误"""
        error_str = str(error)
        print(f"WebSocket错误: {error_str}")
        
        # 如果是握手错误，提供更详细的诊断信息
        if "Handshake status" in error_str or "200 OK" in error_str:
            print("\n⚠️  WebSocket 握手失败 - 可能的原因：")
            print("1. API 密钥无效或已过期")
            print("2. API 密钥没有 WebSocket 权限")
            print("3. WebSocket 端点不正确")
            print("4. 需要不同的认证方式")
            print("\n建议检查：")
            print(f"- 确认 WHALE_ALERT_API_KEY 环境变量已正确设置")
            print(f"- 登录 Whale Alert 控制台确认 API 密钥状态")
            print(f"- 确认订阅计划支持 WebSocket/Custom Alerts")
            print(f"- 尝试在本地测试连接以排除网络问题")
    
    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        close_msg_str = str(close_msg) if close_msg else ""
        print(f"WebSocket连接关闭 (code: {close_status_code}, msg: {close_msg_str})")
        
        # 解释关闭代码
        if close_status_code == 1000:
            print("正常关闭")
        elif close_status_code == 1001:
            print("端点离开（服务器关闭或浏览器导航）")
        elif close_status_code == 1006:
            print("异常关闭（连接未正常关闭）")
        elif close_status_code == 1008:
            print("策略违规")
        elif close_status_code == 1011:
            print("服务器错误")
        elif close_status_code == 4001:
            print("认证失败 - 请检查 API 密钥")
        elif close_status_code == 4003:
            print("订阅错误 - 请检查订阅参数")
        else:
            print(f"未知关闭代码: {close_status_code}")
        
        self.subscribed = False
        
        # 自动重连（非正常关闭且仍在运行）
        if close_status_code != 1000 and self.running:  # 非正常关闭
            print(f"{self.reconnect_delay}秒后尝试重连...")
            time.sleep(self.reconnect_delay)
            if self.running:  # 如果还在运行，尝试重连
                self.start()
    
    def on_open(self, ws):
        """连接建立后订阅"""
        try:
            # 根据官方文档，订阅消息格式：
            # type: "subscribe_alerts" (必需)
            # id: string (可选) - 用于重连后接收错过的警报
            # blockchains: []string (可选) - 如果省略，自动包含所有区块链
            # symbols: []string (可选) - 如果省略，自动包含所有币种
            # tx_types: []string (可选) - 如果省略，自动包含所有交易类型
            # min_value_usd: float (必需) - 最小转账金额（美元）
            
            # 构建订阅消息
            subscription = {
                "type": "subscribe_alerts",
                "min_value_usd": settings.WHALE_ALERT_MIN_VALUE_USD  # 必需参数
            }
            
            # 添加可选参数（如果配置了）
            if settings.SYMBOLS:
                subscription["symbols"] = settings.SYMBOLS
            # 注意：如果不提供 symbols，API 会自动包含所有币种
            
            if settings.BLOCKCHAINS:
                subscription["blockchains"] = settings.BLOCKCHAINS
            # 注意：如果不提供 blockchains，API 会自动包含所有区块链
            
            ws.send(json.dumps(subscription))
            
            # 显示订阅信息
            blockchain_info = f", 区块链={settings.BLOCKCHAINS}" if settings.BLOCKCHAINS else " (所有链)"
            symbol_info = f"币种={settings.SYMBOLS}" if settings.SYMBOLS else "所有币种"
            print(f"已发送订阅请求: {symbol_info}{blockchain_info}, 最小金额=${settings.WHALE_ALERT_MIN_VALUE_USD:,.0f}")
            
            self.subscribed = False  # 等待确认
        except Exception as e:
            print(f"订阅错误: {e}")
    
    def start(self):
        """启动WebSocket连接"""
        # 根据官方文档，API key 在 URL 中传递：wss://leviathan.whale-alert.io/ws?api_key={key}
        # 不需要额外的 header
        
        # 验证 API 密钥格式（基本检查）
        if not self.api_key or len(self.api_key.strip()) < 10:
            print("⚠️  警告: API 密钥似乎无效（太短）")
            print("请检查 WHALE_ALERT_API_KEY 环境变量是否正确设置")
        
        # 尝试添加额外的 headers（某些 API 可能需要）
        headers = {}
        # 某些 WebSocket 服务可能需要 User-Agent
        headers['User-Agent'] = 'WhaleAlertTrends/1.0'
        
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            header=headers
        )
        self.running = True
        # 不显示完整的URL（包含API key）
        display_url = self.ws_url.split('?')[0] if '?' in self.ws_url else self.ws_url
        print(f"正在连接到 {display_url}...")
        print(f"API 密钥长度: {len(self.api_key)} 字符")
        
        try:
            self.ws.run_forever(
                ping_interval=30,  # 每30秒发送ping保持连接
                ping_timeout=10     # ping超时10秒
            )
        except Exception as e:
            print(f"WebSocket 运行错误: {e}")
            if self.running:
                print(f"{self.reconnect_delay}秒后尝试重连...")
                time.sleep(self.reconnect_delay)
                if self.running:
                    self.start()  # 递归重连
    
    def stop(self):
        """停止WebSocket连接"""
        self.running = False
        if self.ws:
            self.ws.close()


if __name__ == '__main__':
    # 测试代码
    client = WhaleAlertWebSocket()
    try:
        client.start()
    except KeyboardInterrupt:
        print("\n正在停止...")
        client.stop()

