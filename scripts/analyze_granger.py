#!/usr/bin/env python3
"""
执行 Granger 因果检验分析
用法: python scripts/analyze_granger.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.redis_client import RedisClient
from src.analyzers.granger_test import granger_causality_test
import pandas as pd


def main():
    try:
        print("=" * 60)
        print("Granger 因果检验分析")
        print("=" * 60)
        
        # 获取数据
        client = RedisClient()
        results = client.get_all_results()
        
        if len(results) < 34:
            print(f"❌ 数据不足: 只有 {len(results)} 个完成的事件")
            print("需要至少 34 个完成的事件")
            sys.exit(1)
        
        print(f"✅ 数据充足: {len(results)} 个完成的事件\n")
        
        # 构建时间序列
        events = []
        price_changes = []
        timestamps = []
        
        print("正在构建时间序列...")
        for result in results:
            event_id = result.get('event_id', '')
            if not event_id:
                continue
            
            event = client.get_event(event_id)
            if not event:
                continue
            
            timestamp_str = event.get('timestamp', '')
            if not timestamp_str:
                continue
            
            try:
                timestamp = pd.to_datetime(timestamp_str)
                timestamps.append(timestamp)
                events.append(float(event.get('amount_usd', 0)))
                price_changes.append(float(result.get('final_change_pct', 0)))
            except Exception as e:
                print(f"⚠️  处理事件 {event_id[:16]}... 时出错: {e}")
                continue
        
        if len(events) < 34:
            print(f"❌ 有效数据不足: 只有 {len(events)} 个有效事件")
            print("需要至少 34 个有效事件")
            sys.exit(1)
        
        # 创建时间序列
        X = pd.Series(events, index=timestamps, name='转账金额')
        Y = pd.Series(price_changes, index=timestamps, name='价格变化')
        
        # 按时间排序
        X = X.sort_index()
        Y = Y.sort_index()
        
        print(f"✅ 数据点数量: {len(X)}")
        print(f"时间范围: {X.index.min()} 到 {X.index.max()}\n")
        
        # 执行 Granger 因果检验
        print("执行 Granger 因果检验...")
        print("-" * 60)
        
        result = granger_causality_test(
            X=X,
            Y=Y,
            max_lag=24,
            significance_level=0.05,
            verbose=True,
            auto_stationary=True
        )
        
        # 显示结果
        print("\n" + "=" * 60)
        if result.get('has_causality', False):
            print("✅ 发现因果关系！")
            print(f"最优滞后阶数: {result.get('optimal_lag')}")
            print(f"最小 p-value: {result.get('min_p_value'):.4f}")
            print("\n结论: 鲸鱼转账事件对价格变化有预测能力")
        else:
            print("❌ 未发现因果关系")
            print(f"最小 p-value: {result.get('min_p_value', 1.0):.4f}")
            print("\n结论: 未发现鲸鱼转账事件对价格变化的预测能力")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

