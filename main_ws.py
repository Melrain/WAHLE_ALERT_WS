"""
WebSocket主程序：实时监听Whale Alert事件并观察价格变化
"""
import signal
import sys
import os
import time
from datetime import datetime

# 强制无缓冲输出，确保日志实时显示（特别是 Railway 等云平台）
os.environ['PYTHONUNBUFFERED'] = '1'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

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
        print("="*60, flush=True)
        print("Whale Alert 实时监控系统", flush=True)
        print("="*60, flush=True)
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(flush=True)
        
        # 检查API密钥
        if not settings.WHALE_ALERT_API_KEY:
            print("错误: 未配置 Whale Alert API 密钥", flush=True)
            print("请在 .env 文件中设置 WHALE_ALERT_API_KEY", flush=True)
            return
        
        # 初始化组件
        try:
            self.ws_client = WhaleAlertWebSocket(api_key=settings.WHALE_ALERT_API_KEY)
            self.observer = PriceObserver(check_interval=300)  # 每5分钟检查一次
        except Exception as e:
            print(f"初始化错误: {e}", flush=True)
            return
        
        # 设置信号处理器
        self.setup_signal_handlers()
        
        # 启动价格观察器（后台线程）
        self.observer.start()
        
        # 显示当前状态
        manager = WindowManager()
        stats = manager.get_statistics()
        if stats:
            print("当前统计:", flush=True)
            print(f"  总事件数: {stats.get('total_events', 0)}", flush=True)
            print(f"  观察中: {stats.get('observing_count', 0)}", flush=True)
            print(f"  已完成: {stats.get('completed_count', 0)}", flush=True)
            print(flush=True)
        
        # 启动WebSocket（阻塞）
        self.running = True
        print("正在启动WebSocket连接...", flush=True)
        print("按 Ctrl+C 停止", flush=True)
        print("-"*60, flush=True)
        
        try:
            self.ws_client.start()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """停止监控"""
        print("\n正在停止监控系统...", flush=True)
        self.running = False
        
        if self.observer:
            self.observer.stop()
        
        if self.ws_client:
            self.ws_client.stop()
        
        print("监控系统已停止", flush=True)


def main():
    """主函数"""
    monitor = WhaleAlertMonitor()
    monitor.start()


if __name__ == '__main__':
    main()

