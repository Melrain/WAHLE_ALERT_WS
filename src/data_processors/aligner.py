"""数据对齐模块"""
import pandas as pd
from typing import Optional
import numpy as np


def align_time_series(
    series1: pd.Series,
    series2: pd.Series,
    method: str = 'inner',
    fill_method: str = 'forward'
) -> pd.DataFrame:
    """
    对齐两个时间序列
    
    参数:
    - series1: 第一个时间序列
    - series2: 第二个时间序列
    - method: 对齐方法（'inner'=交集, 'outer'=并集）
    - fill_method: 填充方法（'forward'=前向填充, 'backward'=后向填充, 'zero'=零填充）
    
    返回:
    - 对齐后的DataFrame
    """
    # 合并两个序列
    aligned = pd.DataFrame({
        'series1': series1,
        'series2': series2
    })
    
    # 根据method选择对齐方式
    if method == 'inner':
        aligned = aligned.dropna()
    elif method == 'outer':
        # 填充缺失值
        if fill_method == 'forward':
            aligned = aligned.fillna(method='ffill')
        elif fill_method == 'backward':
            aligned = aligned.fillna(method='bfill')
        elif fill_method == 'zero':
            aligned = aligned.fillna(0)
    
    return aligned


def align_multiple_series(
    series_dict: dict,
    method: str = 'inner',
    fill_method: str = 'forward'
) -> pd.DataFrame:
    """
    对齐多个时间序列
    
    参数:
    - series_dict: 时间序列字典，{name: series}
    - method: 对齐方法
    - fill_method: 填充方法
    
    返回:
    - 对齐后的DataFrame
    """
    # 合并所有序列
    aligned = pd.DataFrame(series_dict)
    
    # 根据method选择对齐方式
    if method == 'inner':
        aligned = aligned.dropna()
    elif method == 'outer':
        # 填充缺失值
        if fill_method == 'forward':
            aligned = aligned.fillna(method='ffill')
        elif fill_method == 'backward':
            aligned = aligned.fillna(method='bfill')
        elif fill_method == 'zero':
            aligned = aligned.fillna(0)
    
    return aligned


def resample_to_common_freq(
    df: pd.DataFrame,
    target_freq: str = '1H',
    method: str = 'mean'
) -> pd.DataFrame:
    """
    将DataFrame重采样到统一频率
    
    参数:
    - df: 时间序列DataFrame
    - target_freq: 目标频率
    - method: 重采样方法（'mean', 'sum', 'last'等）
    
    返回:
    - 重采样后的DataFrame
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame索引必须是DatetimeIndex")
    
    if method == 'mean':
        resampled = df.resample(target_freq).mean()
    elif method == 'sum':
        resampled = df.resample(target_freq).sum()
    elif method == 'last':
        resampled = df.resample(target_freq).last()
    elif method == 'first':
        resampled = df.resample(target_freq).first()
    else:
        resampled = df.resample(target_freq).agg(method)
    
    return resampled


if __name__ == '__main__':
    # 测试代码
    import pandas as pd
    from datetime import datetime, timedelta
    
    # 创建示例数据
    dates1 = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    dates2 = pd.date_range(start='2024-01-01 00:30', periods=100, freq='1H')
    
    series1 = pd.Series(np.random.randn(100), index=dates1, name='whale_events')
    series2 = pd.Series(np.random.randn(100), index=dates2, name='price_change')
    
    # 对齐
    aligned = align_time_series(series1, series2, method='inner')
    print("对齐结果:")
    print(aligned.head())

