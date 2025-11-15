#!/usr/bin/env python3
"""
导出数据到 CSV
用法: python scripts/export_data.py [输出文件名]
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.redis_client import RedisClient
import pandas as pd


def main():
    try:
        client = RedisClient()
        results = client.get_all_results()
        
        if not results:
            print("❌ 没有数据可导出")
            sys.exit(1)
        
        print(f"正在导出 {len(results)} 条记录...")
        
        # 构建 DataFrame
        data = []
        for result in results:
            event_id = result.get('event_id', '')
            event = client.get_event(event_id)
            
            if not event:
                continue
            
            try:
                data.append({
                    'event_id': event_id,
                    'timestamp': event.get('timestamp', ''),
                    'currency': event.get('currency', ''),
                    'amount_usd': float(event.get('amount_usd', 0)),
                    'baseline_price': float(event.get('baseline_price', 0)),
                    'final_price': float(result.get('final_price', 0)),
                    'final_change_pct': float(result.get('final_change_pct', 0)),
                    'direction': result.get('direction', ''),
                    'max_change_pct': float(result.get('max_change_pct', 0)) if result.get('max_change_pct') else None,
                    'min_change_pct': float(result.get('min_change_pct', 0)) if result.get('min_change_pct') else None,
                    'completed_at': result.get('completed_at', '')
                })
            except Exception as e:
                print(f"⚠️  处理事件 {event_id[:16]}... 时出错: {e}")
                continue
        
        if not data:
            print("❌ 没有有效数据可导出")
            sys.exit(1)
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # 确定输出文件名
        if len(sys.argv) > 1:
            filename = sys.argv[1]
        else:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # 确保文件名有 .csv 扩展名
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # 保存
        output_path = project_root / 'data' / 'results' / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        print(f"✅ 已导出 {len(df)} 条记录到: {output_path}")
        print(f"   文件大小: {output_path.stat().st_size / 1024:.2f} KB")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

