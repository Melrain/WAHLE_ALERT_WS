"""
WebSocket主程序：实时监听Whale Alert事件并观察价格变化
"""
import signal
import sys
import time
from datetime import datetime

from src.websocket.whale_alert_ws import WhaleAlertWebSocket
from src.observers.price_observer import PriceObserver
from src.observers.window_manager import WindowManager
from config import settings


class WhaleAlertMonitor:
    """Whale Alert监控主程序"""
    
    def __init__(self):
        self.ws_client = None
        self.observer = None
        self.running = False
    
    def setup_signal_handlers(self):
        """设置信号处理器，优雅退出"""
        def signal_handler(sig, frame):
            print("\n收到退出信号，正在关闭...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """启动监控"""
        print("="*60)
        print("Whale Alert 实时监控系统")
        print("="*60)
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 检查API密钥
        if not settings.WHALE_ALERT_API_KEY:
            print("错误: 未配置 Whale Alert API 密钥")
            print("请在 .env 文件中设置 WHALE_ALERT_API_KEY")
            return
        
        # 初始化组件
        try:
            self.ws_client = WhaleAlertWebSocket(api_key=settings.WHALE_ALERT_API_KEY)
            self.observer = PriceObserver(check_interval=300)  # 每5分钟检查一次
        except Exception as e:
            print(f"初始化错误: {e}")
            return
        
        # 设置信号处理器
        self.setup_signal_handlers()
        
        # 启动价格观察器（后台线程）
        self.observer.start()
        
        # 显示当前状态
        manager = WindowManager()
        stats = manager.get_statistics()
        if stats:
            print("当前统计:")
            print(f"  总事件数: {stats.get('total_events', 0)}")
            print(f"  观察中: {stats.get('observing_count', 0)}")
            print(f"  已完成: {stats.get('completed_count', 0)}")
            print()
        
        # 启动WebSocket（阻塞）
        self.running = True
        print("正在启动WebSocket连接...")
        print("按 Ctrl+C 停止")
        print("-"*60)
        
        try:
            self.ws_client.start()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """停止监控"""
        print("\n正在停止监控系统...")
        self.running = False
        
        if self.observer:
            self.observer.stop()
        
        if self.ws_client:
            self.ws_client.stop()
        
        print("监控系统已停止")


def main():
    """主函数"""
    monitor = WhaleAlertMonitor()
    monitor.start()


if __name__ == '__main__':
    main()

