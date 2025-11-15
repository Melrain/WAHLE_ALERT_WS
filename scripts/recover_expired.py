#!/usr/bin/env python3
"""
恢复过期的观察窗口
用法: python scripts/recover_expired.py

当服务重启后，如果有观察窗口已过期但未完成，运行此脚本可以恢复它们。
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.redis_client import RedisClient
from src.data_collectors.binance import BinanceCollector
from datetime import datetime


def main():
    try:
        print("=" * 60)
        print("恢复过期的观察窗口")
        print("=" * 60)
        
        client = RedisClient()
        binance = BinanceCollector()
        
        # 获取所有活跃的观察窗口
        active_events = client.get_active_observations()
        
        if not active_events:
            print("没有活跃的观察窗口")
            return
        
        print(f"检查 {len(active_events)} 个活跃观察窗口...\n")
        
        recovered = 0
        skipped = 0
        errors = 0
        
        for event_id in active_events:
            observation = client.get_observation(event_id)
            if not observation:
                # 观察窗口不存在，从活跃列表移除
                client.client.zrem("observations:active", event_id)
                skipped += 1
                continue
            
            expires_at_str = observation.get('expires_at')
            if not expires_at_str:
                skipped += 1
                continue
            
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                
                # 如果已过期但状态还是 observing
                if datetime.now() >= expires_at and observation.get('status') == 'observing':
                    # 获取事件信息
                    event = client.get_event(event_id)
                    if not event:
                        print(f"⚠️  事件 {event_id[:16]}... 不存在，跳过")
                        skipped += 1
                        continue
                    
                    currency = event.get('currency', 'btc')
                    baseline_price = float(event.get('baseline_price', 0))
                    
                    if baseline_price == 0:
                        print(f"⚠️  事件 {event_id[:16]}... 基准价格为0，跳过")
                        skipped += 1
                        continue
                    
                    # 获取当前价格
                    current_price = binance.get_current_price(currency)
                    if not current_price or current_price == 0:
                        print(f"⚠️  无法获取 {currency.upper()} 价格，跳过事件 {event_id[:16]}...")
                        skipped += 1
                        continue
                    
                    # 计算变化
                    change_pct = ((current_price - baseline_price) / baseline_price) * 100
                    
                    # 获取所有快照计算最大最小
                    snapshots = client.get_price_snapshots(event_id)
                    max_change = change_pct
                    min_change = change_pct
                    
                    if snapshots:
                        changes = [float(s.get('change_pct', 0)) for s in snapshots]
                        if changes:
                            max_change = max(changes)
                            min_change = min(changes)
                    
                    direction = "up" if change_pct > 0 else "down"
                    
                    # 完成观察
                    client.complete_observation(
                        event_id=event_id,
                        final_price=current_price,
                        final_change_pct=change_pct,
                        direction=direction,
                        max_change_pct=max_change,
                        min_change_pct=min_change
                    )
                    
                    # 更新统计
                    client.update_stats()
                    
                    print(f"✅ 恢复过期观察: {event_id[:16]}... | 变化: {change_pct:+.2f}% | 方向: {direction}")
                    recovered += 1
                else:
                    # 未过期或已完成
                    skipped += 1
                    
            except Exception as e:
                print(f"❌ 处理 {event_id[:16]}... 时出错: {e}")
                errors += 1
                continue
        
        print("\n" + "=" * 60)
        print(f"恢复完成:")
        print(f"  ✅ 已恢复: {recovered} 个")
        print(f"  ⏭️  跳过: {skipped} 个")
        print(f"  ❌ 错误: {errors} 个")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

