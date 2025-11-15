"""Granger因果检验模块"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from statsmodels.tsa.vector_ar.var_model import VAR
import warnings

warnings.filterwarnings('ignore')


def check_stationarity(
    series: pd.Series,
    significance_level: float = 0.05,
    verbose: bool = False
) -> Tuple[bool, float]:
    """
    检查时间序列是否平稳（ADF检验）
    
    参数:
    - series: 时间序列
    - significance_level: 显著性水平
    - verbose: 是否打印详细信息
    
    返回:
    - (is_stationary, p_value)
    """
    # 移除缺失值
    series_clean = series.dropna()
    
    if len(series_clean) < 10:
        return False, 1.0
    
    try:
        result = adfuller(series_clean, autolag='AIC')
        p_value = result[1]
        is_stationary = p_value <= significance_level
        
        if verbose:
            print(f"ADF检验结果:")
            print(f"  p-value: {p_value:.4f}")
            print(f"  是否平稳: {is_stationary}")
        
        return is_stationary, p_value
    except Exception as e:
        if verbose:
            print(f"ADF检验出错: {e}")
        return False, 1.0


def make_stationary(
    series: pd.Series,
    method: str = 'diff',
    verbose: bool = False
) -> pd.Series:
    """
    使时间序列平稳化
    
    参数:
    - series: 时间序列
    - method: 方法（'diff'=差分, 'log_diff'=对数差分）
    - verbose: 是否打印信息
    
    返回:
    - 平稳化后的序列
    """
    if method == 'diff':
        stationary = series.diff().dropna()
    elif method == 'log_diff':
        # 确保值都是正数
        if (series <= 0).any():
            series = series - series.min() + 1
        stationary = np.log(series).diff().dropna()
    else:
        stationary = series
    
    if verbose:
        is_stationary, p_value = check_stationarity(stationary)
        print(f"平稳化后 - 是否平稳: {is_stationary}, p-value: {p_value:.4f}")
    
    return stationary


def granger_causality_test(
    X: pd.Series,
    Y: pd.Series,
    max_lag: int = 24,
    significance_level: float = 0.05,
    verbose: bool = False,
    auto_stationary: bool = True
) -> Dict:
    """
    执行Granger因果检验
    
    参数:
    - X: 自变量时间序列（转账事件序列）
    - Y: 因变量时间序列（价格变化序列）
    - max_lag: 最大滞后阶数
    - significance_level: 显著性水平
    - verbose: 是否打印详细信息
    - auto_stationary: 是否自动进行平稳化处理
    
    返回:
    - 包含检验结果的字典
    """
    # 对齐数据
    data = pd.DataFrame({'X': X, 'Y': Y}).dropna()
    
    if len(data) < max_lag + 10:
        raise ValueError(f"数据点太少（{len(data)}），需要至少 {max_lag + 10} 个数据点")
    
    # 检查平稳性
    if auto_stationary:
        x_stationary, x_p = check_stationarity(data['X'], verbose=verbose)
        y_stationary, y_p = check_stationarity(data['Y'], verbose=verbose)
        
        if not x_stationary:
            if verbose:
                print("X序列不平稳，进行差分处理...")
            data['X'] = make_stationary(data['X'], verbose=verbose)
        
        if not y_stationary:
            if verbose:
                print("Y序列不平稳，进行差分处理...")
            data['Y'] = make_stationary(data['Y'], verbose=verbose)
        
        # 再次对齐（差分后可能产生新的缺失值）
        data = data.dropna()
    
    if len(data) < max_lag + 10:
        raise ValueError(f"平稳化后数据点太少（{len(data)}）")
    
    # 准备数据（VAR模型需要Y在前，X在后）
    var_data = data[['Y', 'X']]
    
    # 执行Granger因果检验
    try:
        test_result = grangercausalitytests(
            var_data,
            max_lag,
            verbose=verbose
        )
    except Exception as e:
        if verbose:
            print(f"Granger检验出错: {e}")
        return {
            'success': False,
            'error': str(e),
            'results': None
        }
    
    # 提取结果
    results = []
    for lag in range(1, max_lag + 1):
        try:
            # 提取p-value（使用ssr_ftest）
            p_value = test_result[lag][0]['ssr_ftest'][1]
            f_statistic = test_result[lag][0]['ssr_ftest'][0]
            
            results.append({
                'lag': lag,
                'p_value': p_value,
                'f_statistic': f_statistic,
                'significant': p_value <= significance_level
            })
        except KeyError:
            # 如果某个lag没有结果，跳过
            continue
    
    results_df = pd.DataFrame(results)
    
    # 找到最显著的滞后阶数
    significant_results = results_df[results_df['significant']]
    if not significant_results.empty:
        optimal_lag = significant_results.loc[significant_results['p_value'].idxmin(), 'lag']
        min_p_value = significant_results['p_value'].min()
    else:
        optimal_lag = None
        min_p_value = results_df['p_value'].min()
    
    # 总结
    summary = {
        'success': True,
        'total_lags_tested': len(results),
        'significant_lags': len(significant_results),
        'optimal_lag': optimal_lag,
        'min_p_value': min_p_value,
        'has_causality': not significant_results.empty,
        'results': results_df
    }
    
    if verbose:
        print("\n" + "="*50)
        print("Granger因果检验结果总结")
        print("="*50)
        print(f"检验的滞后阶数: 1 到 {max_lag}")
        print(f"显著的滞后阶数: {summary['significant_lags']}")
        if optimal_lag:
            print(f"最优滞后阶数: {optimal_lag}")
            print(f"最小p-value: {min_p_value:.4f}")
            print(f"结论: X 对 Y 有 Granger 因果关系 (p < {significance_level})")
        else:
            print(f"最小p-value: {min_p_value:.4f}")
            print(f"结论: 未发现显著的 Granger 因果关系 (p >= {significance_level})")
        print("="*50)
    
    return summary


def bidirectional_granger_test(
    X: pd.Series,
    Y: pd.Series,
    max_lag: int = 24,
    significance_level: float = 0.05,
    verbose: bool = False
) -> Dict:
    """
    双向Granger因果检验
    
    参数:
    - X: 第一个时间序列
    - Y: 第二个时间序列
    - max_lag: 最大滞后阶数
    - significance_level: 显著性水平
    - verbose: 是否打印详细信息
    
    返回:
    - 包含双向检验结果的字典
    """
    # X -> Y
    if verbose:
        print("\n检验方向: X -> Y")
    result_xy = granger_causality_test(
        X, Y, max_lag, significance_level, verbose=False, auto_stationary=True
    )
    
    # Y -> X
    if verbose:
        print("\n检验方向: Y -> X")
    result_yx = granger_causality_test(
        Y, X, max_lag, significance_level, verbose=False, auto_stationary=True
    )
    
    # 总结
    summary = {
        'X_to_Y': result_xy,
        'Y_to_X': result_yx,
        'bidirectional': result_xy.get('has_causality', False) and result_yx.get('has_causality', False),
        'X_to_Y_only': result_xy.get('has_causality', False) and not result_yx.get('has_causality', False),
        'Y_to_X_only': result_yx.get('has_causality', False) and not result_xy.get('has_causality', False),
        'no_causality': not result_xy.get('has_causality', False) and not result_yx.get('has_causality', False)
    }
    
    if verbose:
        print("\n" + "="*50)
        print("双向Granger因果检验总结")
        print("="*50)
        if summary['bidirectional']:
            print("结论: 双向因果关系（X ↔ Y）")
        elif summary['X_to_Y_only']:
            print("结论: 单向因果关系（X → Y）")
        elif summary['Y_to_X_only']:
            print("结论: 单向因果关系（Y → X）")
        else:
            print("结论: 未发现因果关系")
        print("="*50)
    
    return summary


if __name__ == '__main__':
    # 测试代码
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # 创建示例数据
    dates = pd.date_range(start='2024-01-01', periods=500, freq='1H')
    
    # 模拟数据：X对Y有因果关系
    np.random.seed(42)
    X = pd.Series(np.random.randn(500).cumsum(), index=dates, name='X')
    Y = pd.Series(
        X.shift(1).fillna(0) * 0.5 + np.random.randn(500) * 0.5,
        index=dates,
        name='Y'
    )
    
    # 执行检验
    print("执行Granger因果检验...")
    result = granger_causality_test(X, Y, max_lag=10, verbose=True)
    
    print("\n检验结果:")
    print(result['results'])

