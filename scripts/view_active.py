#!/usr/bin/env python3
"""
查看当前活跃的观察窗口
用法: python scripts/view_active.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.observers.window_manager import WindowManager
from datetime import datetime


def main():
    try:
        manager = WindowManager()
        active = manager.get_active_windows()
        
        print("=" * 60)
        print(f"活跃观察窗口: {len(active)} 个")
        print("=" * 60)
        
        if not active:
            print("当前没有活跃的观察窗口")
            return
        
        for i, window in enumerate(active[:10], 1):  # 只显示前10个
            event = window.get('event', {})
            observation = window.get('observation', {})
            
            event_id = window.get('event_id', 'N/A')
            currency = event.get('currency', 'N/A').upper()
            amount_usd = float(event.get('amount_usd', 0))
            baseline_price = float(observation.get('baseline_price', 0))
            expires_at = observation.get('expires_at', 'N/A')
            
            # 计算剩余时间
            try:
                expires = datetime.fromisoformat(expires_at)
                remaining = expires - datetime.now()
                if remaining.total_seconds() > 0:
                    remaining_str = f"{remaining.total_seconds()/3600:.1f} 小时"
                else:
                    remaining_str = "已过期"
            except:
                remaining_str = "N/A"
            
            snapshots_count = len(window.get('snapshots', []))
            
            print(f"\n{i}. 事件ID: {event_id[:16]}...")
            print(f"   币种: {currency}")
            print(f"   金额: ${amount_usd:,.0f}")
            print(f"   基准价格: ${baseline_price:,.2f}")
            print(f"   剩余时间: {remaining_str}")
            print(f"   快照数量: {snapshots_count}")
        
        if len(active) > 10:
            print(f"\n... 还有 {len(active) - 10} 个活跃窗口未显示")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

