"""价格观察器 - 定期检查观察窗口的价格变化"""
import time
import threading
from datetime import datetime, timedelta
from typing import Optional
from src.storage.redis_client import RedisClient
from src.data_collectors.binance import BinanceCollector


class PriceObserver:
    """价格观察器 - 定期检查所有活跃观察窗口的价格变化"""
    
    def __init__(self, check_interval: int = 300, window_hours: int = 24):
        """
        初始化价格观察器
        
        参数:
        - check_interval: 检查间隔（秒），默认5分钟
        - window_hours: 观察窗口小时数，默认24小时
        """
        self.check_interval = check_interval
        self.window_hours = window_hours
        self.redis_client = RedisClient()
        self.binance = BinanceCollector()
        self.running = False
        self.thread = None
    
    def check_observations(self):
        """检查所有活跃的观察窗口"""
        try:
            active_events = self.redis_client.get_active_observations()
            
            if not active_events:
                return
            
            print(f"检查 {len(active_events)} 个活跃观察窗口...")
            
            for event_id in active_events:
                try:
                    # 获取观察窗口详情
                    observation = self.redis_client.get_observation(event_id)
                    if not observation:
                        # 观察窗口不存在，从活跃列表移除
                        self.redis_client.client.zrem("observations:active", event_id)
                        continue
                    
                    if observation.get('status') != 'observing':
                        continue
                    
                    # 获取事件信息
                    event = self.redis_client.get_event(event_id)
                    if not event:
                        continue
                    
                    currency = event.get('currency', 'btc')
                    symbol = f"{currency.upper()}USDT"
                    baseline_price = float(event.get('baseline_price', 0))
                    
                    if baseline_price == 0:
                        continue
                    
                    # 获取当前价格
                    current_price = self.binance.get_current_price(symbol)
                    if not current_price or current_price == 0:
                        continue
                    
                    # 计算变化
                    change_pct = ((current_price - baseline_price) / baseline_price) * 100
                    
                    # 添加快照
                    self.redis_client.add_price_snapshot(event_id, current_price, change_pct)
                    
                    # 检查是否到期
                    expires_at_str = observation.get('expires_at')
                    if expires_at_str:
                        expires_at = datetime.fromisoformat(expires_at_str)
                        if datetime.now() >= expires_at:
                            # 完成观察
                            # 获取所有快照，计算最大最小变化
                            snapshots = self.redis_client.get_price_snapshots(event_id)
                            max_change = change_pct
                            min_change = change_pct
                            
                            if snapshots:
                                changes = [float(s.get('change_pct', 0)) for s in snapshots]
                                if changes:
                                    max_change = max(changes)
                                    min_change = min(changes)
                            
                            direction = "up" if change_pct > 0 else "down"
                            self.redis_client.complete_observation(
                                event_id=event_id,
                                final_price=current_price,
                                final_change_pct=change_pct,
                                direction=direction,
                                max_change_pct=max_change,
                                min_change_pct=min_change
                            )
                            
                            print(f"✓ 观察完成: {event_id[:8]}... | 变化: {change_pct:+.2f}% | 方向: {direction}")
                            
                            # 更新统计
                            self.redis_client.update_stats()
                
                except Exception as e:
                    print(f"检查观察窗口 {event_id} 时出错: {e}")
                    continue
        
        except Exception as e:
            print(f"检查观察窗口时出错: {e}")
    
    def run(self):
        """运行观察器（阻塞）"""
        self.running = True
        print(f"价格观察器启动，每 {self.check_interval} 秒检查一次")
        
        while self.running:
            try:
                self.check_observations()
            except Exception as e:
                print(f"观察器错误: {e}")
            
            # 等待指定间隔
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
        
        print("价格观察器已停止")
    
    def start(self):
        """在后台线程启动观察器"""
        if self.thread and self.thread.is_alive():
            print("观察器已在运行")
            return
        
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        print("价格观察器已在后台启动")
    
    def stop(self):
        """停止观察器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("价格观察器已停止")


if __name__ == '__main__':
    # 测试代码
    observer = PriceObserver(check_interval=60)  # 1分钟检查一次用于测试
    try:
        observer.run()
    except KeyboardInterrupt:
        print("\n正在停止...")
        observer.stop()

