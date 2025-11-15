"""数据聚合模块"""
import pandas as pd
from typing import Optional, List
import numpy as np


def aggregate_events_to_time_series(
    events_df: pd.DataFrame,
    freq: str = '1H',
    amount_col: str = 'amount_usd',
    timestamp_col: str = 'timestamp'
) -> pd.DataFrame:
    """
    将离散的转账事件聚合为时间序列
    
    参数:
    - events_df: 包含转账事件的DataFrame
    - freq: 聚合频率（'1H'=每小时, '1D'=每天, '15T'=每15分钟）
    - amount_col: 金额列名
    - timestamp_col: 时间戳列名
    
    返回:
    - 聚合后的时间序列DataFrame
    """
    if events_df.empty:
        return pd.DataFrame()
    
    # 确保时间戳是datetime类型
    df = events_df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df = df.set_index(timestamp_col)
    
    # 按时间聚合
    aggregated = df.groupby(pd.Grouper(freq=freq)).agg({
        amount_col: ['sum', 'count', 'mean', 'std'],
    })
    
    # 展平列名
    aggregated.columns = [
        f'{amount_col}_{stat}' 
        for stat in ['sum', 'count', 'mean', 'std']
    ]
    
    # 如果有direction列，也进行聚合
    if 'direction' in df.columns:
        direction_agg = df.groupby(pd.Grouper(freq=freq)).agg({
            'direction': lambda x: (x == 'in').sum() - (x == 'out').sum()  # 净流入
        })
        direction_agg.columns = ['net_direction']
        aggregated = pd.concat([aggregated, direction_agg], axis=1)
    
    # 填充缺失值为0
    aggregated = aggregated.fillna(0)
    
    return aggregated


def create_lag_features(
    series: pd.Series,
    max_lag: int = 24,
    prefix: str = 'lag'
) -> pd.DataFrame:
    """
    创建滞后特征
    
    参数:
    - series: 时间序列
    - max_lag: 最大滞后阶数
    - prefix: 列名前缀
    
    返回:
    - 包含滞后特征的DataFrame
    """
    lag_features = pd.DataFrame(index=series.index)
    
    for lag in range(1, max_lag + 1):
        lag_features[f'{prefix}_{lag}'] = series.shift(lag)
    
    return lag_features


def calculate_rolling_features(
    series: pd.Series,
    windows: List[int] = [6, 12, 24],
    functions: List[str] = ['mean', 'std', 'sum']
) -> pd.DataFrame:
    """
    计算滚动窗口特征
    
    参数:
    - series: 时间序列
    - windows: 窗口大小列表
    - functions: 统计函数列表
    
    返回:
    - 包含滚动特征的DataFrame
    """
    rolling_features = pd.DataFrame(index=series.index)
    
    for window in windows:
        for func in functions:
            if func == 'mean':
                rolling_features[f'rolling_{window}_{func}'] = series.rolling(window).mean()
            elif func == 'std':
                rolling_features[f'rolling_{window}_{func}'] = series.rolling(window).std()
            elif func == 'sum':
                rolling_features[f'rolling_{window}_{func}'] = series.rolling(window).sum()
            elif func == 'max':
                rolling_features[f'rolling_{window}_{func}'] = series.rolling(window).max()
            elif func == 'min':
                rolling_features[f'rolling_{window}_{func}'] = series.rolling(window).min()
    
    return rolling_features


if __name__ == '__main__':
    # 测试代码
    import pandas as pd
    from datetime import datetime, timedelta
    
    # 创建示例数据
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    events = pd.DataFrame({
        'timestamp': dates[:50],  # 只有50个事件
        'amount_usd': np.random.uniform(100000, 1000000, 50),
        'direction': np.random.choice(['in', 'out'], 50)
    })
    
    # 聚合
    aggregated = aggregate_events_to_time_series(events, freq='1H')
    print("聚合结果:")
    print(aggregated.head())

