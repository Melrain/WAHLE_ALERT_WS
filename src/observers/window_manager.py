"""观察窗口管理器 - 提供查询和管理功能"""
from datetime import datetime
from typing import List, Dict, Optional
from src.storage.redis_client import RedisClient


class WindowManager:
    """观察窗口管理器"""
    
    def __init__(self):
        self.redis_client = RedisClient()
    
    def get_active_windows(self) -> List[Dict]:
        """
        获取所有活跃的观察窗口
        
        返回:
        - 观察窗口列表，包含事件和观察信息
        """
        active_events = self.redis_client.get_active_observations()
        windows = []
        
        for event_id in active_events:
            event = self.redis_client.get_event(event_id)
            observation = self.redis_client.get_observation(event_id)
            
            if event and observation:
                windows.append({
                    'event_id': event_id,
                    'event': event,
                    'observation': observation,
                    'snapshots': self.redis_client.get_price_snapshots(event_id)
                })
        
        return windows
    
    def get_completed_results(self, limit: int = 100) -> List[Dict]:
        """
        获取已完成的结果
        
        参数:
        - limit: 返回数量限制
        
        返回:
        - 结果列表
        """
        results = self.redis_client.get_all_results()
        # 按完成时间排序（最新的在前）
        results.sort(key=lambda x: x.get('completed_at', ''), reverse=True)
        return results[:limit]
    
    def get_event_history(self, event_id: str) -> Optional[Dict]:
        """
        获取事件的完整历史（事件 + 观察 + 快照 + 结果）
        
        参数:
        - event_id: 事件ID
        
        返回:
        - 完整历史数据
        """
        event = self.redis_client.get_event(event_id)
        if not event:
            return None
        
        observation = self.redis_client.get_observation(event_id)
        snapshots = self.redis_client.get_price_snapshots(event_id)
        result = self.redis_client.get_result(event_id)
        
        return {
            'event': event,
            'observation': observation,
            'snapshots': snapshots,
            'result': result
        }
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        返回:
        - 统计信息字典
        """
        stats = self.redis_client.get_stats()
        if not stats:
            self.redis_client.update_stats()
            stats = self.redis_client.get_stats()
        return stats


if __name__ == '__main__':
    # 测试代码
    manager = WindowManager()
    
    print("活跃观察窗口:")
    active = manager.get_active_windows()
    print(f"数量: {len(active)}")
    for window in active[:5]:  # 只显示前5个
        print(f"  - {window['event_id'][:8]}... | 状态: {window['observation'].get('status')}")
    
    print("\n已完成结果:")
    completed = manager.get_completed_results(limit=10)
    print(f"数量: {len(completed)}")
    for result in completed[:5]:  # 只显示前5个
        print(f"  - {result.get('event_id', 'N/A')[:8]}... | 变化: {result.get('final_change_pct', 'N/A')}% | 方向: {result.get('direction', 'N/A')}")
    
    print("\n统计信息:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

