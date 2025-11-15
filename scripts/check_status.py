#!/usr/bin/env python3
"""
快速检查数据收集状态
用法: python scripts/check_status.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.redis_client import RedisClient
from src.observers.window_manager import WindowManager
from datetime import datetime


def main():
    try:
        manager = WindowManager()
        stats = manager.get_statistics()
        
        print("=" * 60)
        print("数据收集状态")
        print("=" * 60)
        print(f"总事件数: {stats.get('total_events', 0)}")
        print(f"正在观察中: {stats.get('observing_count', 0)}")
        print(f"已完成观察: {stats.get('completed_count', 0)}")
        print(f"价格上涨: {stats.get('up_count', 0)}")
        print(f"价格下跌: {stats.get('down_count', 0)}")
        
        completed_count = int(stats.get('completed_count', 0))
        if completed_count < 34:
            print(f"\n⚠️  数据不足: 只有 {completed_count} 个完成的事件")
            print(f"需要至少 34 个完成的事件才能进行 Granger 因果检验")
            print(f"还需要: {34 - completed_count} 个事件")
        else:
            print(f"\n✅ 数据充足: 有 {completed_count} 个完成的事件")
            print("可以开始进行 Granger 因果检验分析！")
        
        # 查看最近完成的结果
        print("\n" + "=" * 60)
        print("最近完成的结果（前5个）")
        print("=" * 60)
        completed = manager.get_completed_results(limit=5)
        
        if not completed:
            print("暂无完成的结果")
        else:
            for i, result in enumerate(completed, 1):
                event_id = result.get('event_id', 'N/A')
                change_pct = result.get('final_change_pct', 'N/A')
                direction = result.get('direction', 'N/A')
                completed_at = result.get('completed_at', 'N/A')
                print(f"{i}. 事件: {event_id[:16]}... | 变化: {change_pct}% | 方向: {direction} | 完成时间: {completed_at}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

