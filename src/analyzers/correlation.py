"""相关性分析模块"""
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from typing import Tuple, Dict


def calculate_correlation(
    X: pd.Series,
    Y: pd.Series,
    method: str = 'pearson'
) -> Tuple[float, float]:
    """
    计算两个时间序列的相关性
    
    参数:
    - X: 第一个时间序列
    - Y: 第二个时间序列
    - method: 方法（'pearson'或'spearman'）
    
    返回:
    - (correlation_coefficient, p_value)
    """
    # 对齐数据
    data = pd.DataFrame({'X': X, 'Y': Y}).dropna()
    
    if len(data) < 3:
        return np.nan, 1.0
    
    if method == 'pearson':
        corr, p_value = pearsonr(data['X'], data['Y'])
    elif method == 'spearman':
        corr, p_value = spearmanr(data['X'], data['Y'])
    else:
        raise ValueError(f"不支持的方法: {method}")
    
    return corr, p_value


def calculate_lagged_correlation(
    X: pd.Series,
    Y: pd.Series,
    max_lag: int = 24,
    method: str = 'pearson'
) -> pd.DataFrame:
    """
    计算不同滞后阶数的相关性
    
    参数:
    - X: 第一个时间序列
    - Y: 第二个时间序列
    - max_lag: 最大滞后阶数
    - method: 方法
    
    返回:
    - DataFrame，包含各滞后阶数的相关性
    """
    results = []
    
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # Y滞后于X（X领先）
            X_shifted = X.shift(-lag)
            Y_original = Y
        elif lag > 0:
            # X滞后于Y（Y领先）
            X_shifted = X.shift(lag)
            Y_original = Y
        else:
            # 无滞后
            X_shifted = X
            Y_original = Y
        
        corr, p_value = calculate_correlation(X_shifted, Y_original, method)
        
        results.append({
            'lag': lag,
            'correlation': corr,
            'p_value': p_value,
            'interpretation': 'X领先' if lag < 0 else ('Y领先' if lag > 0 else '同步')
        })
    
    return pd.DataFrame(results)


def correlation_matrix(
    data: pd.DataFrame,
    method: str = 'pearson'
) -> pd.DataFrame:
    """
    计算相关性矩阵
    
    参数:
    - data: 包含多个时间序列的DataFrame
    - method: 方法
    
    返回:
    - 相关性矩阵
    """
    if method == 'pearson':
        return data.corr(method='pearson')
    elif method == 'spearman':
        return data.corr(method='spearman')
    else:
        raise ValueError(f"不支持的方法: {method}")


if __name__ == '__main__':
    # 测试代码
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # 创建示例数据
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    X = pd.Series(np.random.randn(100), index=dates, name='X')
    Y = pd.Series(X.shift(1).fillna(0) * 0.5 + np.random.randn(100) * 0.5, index=dates, name='Y')
    
    # 计算相关性
    corr, p_value = calculate_correlation(X, Y)
    print(f"Pearson相关性: {corr:.4f}, p-value: {p_value:.4f}")
    
    # 计算滞后相关性
    lagged_corr = calculate_lagged_correlation(X, Y, max_lag=5)
    print("\n滞后相关性:")
    print(lagged_corr)

