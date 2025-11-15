#!/usr/bin/env python3
"""
手动更新统计信息
用法: python scripts/update_stats.py

当需要立即查看最新统计信息时，可以运行此脚本强制更新。
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.redis_client import RedisClient


def main():
    try:
        client = RedisClient()
        print("正在更新统计信息...")
        client.update_stats()
        
        stats = client.get_stats()
        
        print("\n" + "=" * 60)
        print("更新后的统计信息")
        print("=" * 60)
        print(f"总事件数: {stats.get('total_events', 0)}")
        print(f"正在观察中: {stats.get('observing_count', 0)}")
        print(f"已完成观察: {stats.get('completed_count', 0)}")
        print(f"价格上涨: {stats.get('up_count', 0)}")
        print(f"价格下跌: {stats.get('down_count', 0)}")
        print(f"更新时间: {stats.get('updated_at', 'N/A')}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

