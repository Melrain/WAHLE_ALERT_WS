"""Redis客户端封装"""
import redis
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from config import settings


class RedisClient:
    """Redis客户端封装，用于存储事件和观察数据"""
    
    def __init__(self, redis_url: Optional[str] = None, host: Optional[str] = None, 
                 port: int = 6379, db: int = 0, password: Optional[str] = None):
        """
        初始化Redis客户端
        
        参数:
        - redis_url: Redis连接URL（优先使用），格式: redis://[:password@]host[:port][/db]
        - host: Redis主机地址（如果未提供redis_url时使用）
        - port: Redis端口（如果未提供redis_url时使用）
        - db: Redis数据库编号（如果未提供redis_url时使用）
        - password: Redis密码（如果未提供redis_url时使用）
        """
        # 优先使用 redis_url
        if redis_url:
            self.redis_url = redis_url
        elif getattr(settings, 'REDIS_URL', ''):
            self.redis_url = settings.REDIS_URL
        else:
            self.redis_url = None
            # 使用旧的配置方式（向后兼容）
            self.host = host or getattr(settings, 'REDIS_HOST', 'localhost')
            self.port = port or getattr(settings, 'REDIS_PORT', 6379)
            self.db = db or getattr(settings, 'REDIS_DB', 0)
            self.password = password or getattr(settings, 'REDIS_PASSWORD', None)
        
        try:
            if self.redis_url:
                # 使用 URL 连接
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # 从 URL 中提取信息用于显示
                from urllib.parse import urlparse
                parsed = urlparse(self.redis_url)
                display_info = f"{parsed.hostname or 'localhost'}:{parsed.port or 6379}{parsed.path or '/0'}"
            else:
                # 使用旧的连接方式
                self.client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                display_info = f"{self.host}:{self.port}/{self.db}"
            
            # 测试连接
            self.client.ping()
            print(f"Redis连接成功: {display_info}", flush=True)
        except redis.ConnectionError as e:
            print(f"Redis连接失败: {e}", flush=True)
            print(f"请确保Redis服务正在运行: docker-compose up -d", flush=True)
            raise
    
    def save_event(self, event_id: str, event_data: dict):
        """
        保存事件数据
        
        参数:
        - event_id: 事件ID
        - event_data: 事件数据字典
        """
        key = f"event:{event_id}"
        # 确保所有值都是字符串
        event_data_str = {k: str(v) for k, v in event_data.items()}
        self.client.hset(key, mapping=event_data_str)
        self.client.expire(key, 86400 * 7)  # 7天过期
    
    def get_event(self, event_id: str) -> Optional[Dict]:
        """
        获取事件数据
        
        参数:
        - event_id: 事件ID
        
        返回:
        - 事件数据字典，如果不存在返回None
        """
        key = f"event:{event_id}"
        data = self.client.hgetall(key)
        return data if data else None
    
    def create_observation(self, event_id: str, baseline_price: float, 
                          window_hours: int = 24):
        """
        创建观察窗口
        
        参数:
        - event_id: 事件ID
        - baseline_price: 基准价格
        - window_hours: 观察窗口小时数
        """
        baseline_time = datetime.now()
        expires_at = baseline_time + timedelta(hours=window_hours)
        
        # 保存观察窗口详情
        obs_key = f"observation:{event_id}"
        obs_data = {
            "baseline_price": str(baseline_price),
            "baseline_time": baseline_time.isoformat(),
            "window_hours": str(window_hours),
            "status": "observing",
            "expires_at": expires_at.isoformat()
        }
        self.client.hset(obs_key, mapping=obs_data)
        # TTL设置为窗口时间 + 1小时缓冲
        self.client.expire(obs_key, window_hours * 3600 + 3600)
        
        # 添加到活跃观察列表（使用时间戳作为score，便于排序）
        self.client.zadd("observations:active", {
            event_id: baseline_time.timestamp()
        })
    
    def get_observation(self, event_id: str) -> Optional[Dict]:
        """
        获取观察窗口详情
        
        参数:
        - event_id: 事件ID
        
        返回:
        - 观察窗口数据字典
        """
        key = f"observation:{event_id}"
        data = self.client.hgetall(key)
        return data if data else None
    
    def add_price_snapshot(self, event_id: str, price: float, change_pct: float):
        """
        添加价格快照
        
        参数:
        - event_id: 事件ID
        - price: 当前价格
        - change_pct: 价格变化百分比
        """
        key = f"snapshots:{event_id}"
        snapshot = {
            "time": datetime.now().isoformat(),
            "price": str(price),
            "change_pct": str(change_pct)
        }
        self.client.rpush(key, json.dumps(snapshot))
        self.client.expire(key, 86400 * 7)  # 7天过期
    
    def get_price_snapshots(self, event_id: str) -> List[Dict]:
        """
        获取价格快照列表
        
        参数:
        - event_id: 事件ID
        
        返回:
        - 价格快照列表
        """
        key = f"snapshots:{event_id}"
        snapshots = self.client.lrange(key, 0, -1)
        return [json.loads(s) for s in snapshots]
    
    def complete_observation(self, event_id: str, final_price: float, 
                            final_change_pct: float, direction: str,
                            max_change_pct: Optional[float] = None,
                            min_change_pct: Optional[float] = None):
        """
        完成观察窗口
        
        参数:
        - event_id: 事件ID
        - final_price: 最终价格
        - final_change_pct: 最终变化百分比
        - direction: 方向（'up'或'down'）
        - max_change_pct: 最大变化百分比
        - min_change_pct: 最小变化百分比
        """
        # 保存结果
        result_key = f"result:{event_id}"
        result_data = {
            "final_price": str(final_price),
            "final_change_pct": str(final_change_pct),
            "direction": direction,
            "completed_at": datetime.now().isoformat()
        }
        if max_change_pct is not None:
            result_data["max_change_pct"] = str(max_change_pct)
        if min_change_pct is not None:
            result_data["min_change_pct"] = str(min_change_pct)
        
        self.client.hset(result_key, mapping=result_data)
        self.client.expire(result_key, 86400 * 30)  # 30天过期
        
        # 更新观察窗口状态
        obs_key = f"observation:{event_id}"
        self.client.hset(obs_key, "status", "completed")
        
        # 从活跃列表移除
        self.client.zrem("observations:active", event_id)
    
    def get_active_observations(self) -> List[str]:
        """
        获取所有活跃的观察窗口
        
        返回:
        - 事件ID列表
        """
        return self.client.zrange("observations:active", 0, -1)
    
    def get_result(self, event_id: str) -> Optional[Dict]:
        """
        获取观察结果
        
        参数:
        - event_id: 事件ID
        
        返回:
        - 结果数据字典
        """
        key = f"result:{event_id}"
        data = self.client.hgetall(key)
        return data if data else None
    
    def get_all_results(self) -> List[Dict]:
        """
        获取所有完成的结果
        
        返回:
        - 结果列表
        """
        results = []
        for key in self.client.scan_iter("result:*"):
            result = self.client.hgetall(key)
            result['event_id'] = key.replace('result:', '')
            results.append(result)
        return results
    
    def update_stats(self):
        """更新统计信息"""
        total_events = len(list(self.client.scan_iter("event:*")))
        active_count = len(self.get_active_observations())
        completed_count = len(list(self.client.scan_iter("result:*")))
        
        # 统计方向
        up_count = 0
        down_count = 0
        for result in self.get_all_results():
            if result.get('direction') == 'up':
                up_count += 1
            elif result.get('direction') == 'down':
                down_count += 1
        
        stats = {
            "total_events": str(total_events),
            "observing_count": str(active_count),
            "completed_count": str(completed_count),
            "up_count": str(up_count),
            "down_count": str(down_count),
            "updated_at": datetime.now().isoformat()
        }
        
        self.client.hset("stats:summary", mapping=stats)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.client.hgetall("stats:summary")
        return stats if stats else {}

