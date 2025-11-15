"""
主程序：Whale Alert与Binance价格关联性分析
"""
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data_collectors.whale_alert import collect_whale_data
from src.data_collectors.binance import collect_kline_data
from src.data_processors.aggregator import aggregate_events_to_time_series
from src.data_processors.aligner import align_time_series, resample_to_common_freq
from src.analyzers.granger_test import granger_causality_test, bidirectional_granger_test
from src.analyzers.correlation import calculate_correlation, calculate_lagged_correlation
from src.utils.visualizer import (
    plot_time_series,
    plot_granger_results,
    plot_correlation_heatmap,
    plot_lagged_correlation
)
from config import settings


def main():
    """主函数"""
    print("="*60)
    print("Whale Alert 与 Binance 价格关联性分析")
    print("="*60)
    
    # 配置参数
    symbol = settings.DEFAULT_SYMBOL
    currency = 'btc'  # Whale Alert中的币种代码
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # 分析最近30天的数据
    
    print(f"\n分析时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    print(f"交易对: {symbol}")
    print(f"币种: {currency.upper()}\n")
    
    # 步骤1: 收集数据
    print("步骤1: 收集数据...")
    print("-" * 60)
    
    try:
        # 收集Whale Alert数据
        print("正在收集Whale Alert数据...")
        whale_data = collect_whale_data(
            start_date=start_date,
            end_date=end_date,
            currency=currency,
            min_value=500000,  # 最小50万美元的转账
            save_path=str(settings.RAW_DATA_DIR / f'whale_alert_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv')
        )
        print(f"收集到 {len(whale_data)} 条Whale Alert记录")
        
        if whale_data.empty:
            print("警告: 未收集到Whale Alert数据，请检查API配置")
            return
        
        # 收集Binance K线数据
        print("\n正在收集Binance K线数据...")
        kline_data = collect_kline_data(
            symbol=symbol,
            interval='1h',  # 1小时K线
            start_date=start_date,
            end_date=end_date,
            save_path=str(settings.RAW_DATA_DIR / f'binance_{symbol}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv')
        )
        print(f"收集到 {len(kline_data)} 条K线数据")
        
        if kline_data.empty:
            print("警告: 未收集到K线数据")
            return
        
    except Exception as e:
        print(f"数据收集出错: {e}")
        return
    
    # 步骤2: 数据处理
    print("\n步骤2: 数据处理...")
    print("-" * 60)
    
    # 聚合Whale Alert事件为时间序列
    print("聚合Whale Alert事件...")
    event_series = aggregate_events_to_time_series(
        whale_data,
        freq='1H',  # 按小时聚合
        amount_col='amount_usd'
    )
    print(f"聚合后得到 {len(event_series)} 个时间点")
    
    # 提取价格变化序列
    print("提取价格变化序列...")
    price_change_series = kline_data['price_change_pct'].dropna()
    print(f"价格变化序列有 {len(price_change_series)} 个数据点")
    
    # 对齐时间序列
    print("对齐时间序列...")
    aligned_data = align_time_series(
        event_series['amount_usd_sum'],
        price_change_series,
        method='inner'
    )
    aligned_data.columns = ['whale_amount', 'price_change']
    print(f"对齐后得到 {len(aligned_data)} 个共同时间点")
    
    if len(aligned_data) < 50:
        print("警告: 对齐后的数据点太少，无法进行可靠的统计分析")
        return
    
    # 保存处理后的数据
    processed_path = settings.PROCESSED_DATA_DIR / f'aligned_data_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
    aligned_data.to_csv(processed_path)
    print(f"处理后的数据已保存到: {processed_path}")
    
    # 步骤3: 相关性分析
    print("\n步骤3: 相关性分析...")
    print("-" * 60)
    
    corr_pearson, p_pearson = calculate_correlation(
        aligned_data['whale_amount'],
        aligned_data['price_change'],
        method='pearson'
    )
    print(f"Pearson相关系数: {corr_pearson:.4f}, p-value: {p_pearson:.4f}")
    
    corr_spearman, p_spearman = calculate_correlation(
        aligned_data['whale_amount'],
        aligned_data['price_change'],
        method='spearman'
    )
    print(f"Spearman相关系数: {corr_spearman:.4f}, p-value: {p_spearman:.4f}")
    
    # 滞后相关性分析
    print("\n进行滞后相关性分析...")
    lagged_corr = calculate_lagged_correlation(
        aligned_data['whale_amount'],
        aligned_data['price_change'],
        max_lag=24  # 最多24小时滞后
    )
    
    # 找到最大相关性
    max_corr_idx = lagged_corr['correlation'].abs().idxmax()
    max_corr_lag = lagged_corr.loc[max_corr_idx, 'lag']
    max_corr_value = lagged_corr.loc[max_corr_idx, 'correlation']
    print(f"最大相关性: {max_corr_value:.4f} (滞后 {max_corr_lag} 小时)")
    
    # 步骤4: Granger因果检验
    print("\n步骤4: Granger因果检验...")
    print("-" * 60)
    
    print("检验方向: 转账事件 -> 价格变化")
    granger_result = granger_causality_test(
        X=aligned_data['whale_amount'],
        Y=aligned_data['price_change'],
        max_lag=24,
        verbose=True,
        auto_stationary=True
    )
    
    # 双向检验
    print("\n进行双向Granger因果检验...")
    bidirectional_result = bidirectional_granger_test(
        aligned_data['whale_amount'],
        aligned_data['price_change'],
        max_lag=24,
        verbose=True
    )
    
    # 步骤5: 可视化
    print("\n步骤5: 生成可视化图表...")
    print("-" * 60)
    
    # 时间序列图
    plot_time_series(
        {
            '转账金额(USD)': aligned_data['whale_amount'],
            '价格变化(%)': aligned_data['price_change']
        },
        title="转账事件与价格变化时间序列",
        save_path=str(settings.RESULTS_DIR / 'time_series.png')
    )
    
    # Granger检验结果
    if granger_result.get('success', False):
        plot_granger_results(
            granger_result,
            title="Granger因果检验: 转账事件 -> 价格变化",
            save_path=str(settings.RESULTS_DIR / 'granger_test.png')
        )
    
    # 滞后相关性图
    plot_lagged_correlation(
        lagged_corr,
        title="滞后相关性分析",
        save_path=str(settings.RESULTS_DIR / 'lagged_correlation.png')
    )
    
    # 相关性热力图
    plot_correlation_heatmap(
        aligned_data,
        title="相关性热力图",
        save_path=str(settings.RESULTS_DIR / 'correlation_heatmap.png')
    )
    
    # 步骤6: 保存结果
    print("\n步骤6: 保存分析结果...")
    print("-" * 60)
    
    # 保存Granger检验结果
    if granger_result.get('success', False):
        results_path = settings.RESULTS_DIR / f'granger_results_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
        granger_result['results'].to_csv(results_path, index=False)
        print(f"Granger检验结果已保存到: {results_path}")
    
    # 保存滞后相关性结果
    lagged_corr_path = settings.RESULTS_DIR / f'lagged_correlation_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
    lagged_corr.to_csv(lagged_corr_path, index=False)
    print(f"滞后相关性结果已保存到: {lagged_corr_path}")
    
    # 生成总结报告
    summary = {
        '分析时间范围': f"{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}",
        'Whale Alert记录数': len(whale_data),
        'K线数据点数': len(kline_data),
        '对齐后数据点数': len(aligned_data),
        'Pearson相关系数': f"{corr_pearson:.4f} (p={p_pearson:.4f})",
        'Spearman相关系数': f"{corr_spearman:.4f} (p={p_spearman:.4f})",
        '最大滞后相关性': f"{max_corr_value:.4f} (滞后{max_corr_lag}小时)",
        'Granger因果关系': '是' if granger_result.get('has_causality', False) else '否',
        '最优滞后阶数': granger_result.get('optimal_lag', 'N/A'),
        '最小p-value': f"{granger_result.get('min_p_value', 1.0):.4f}"
    }
    
    summary_path = settings.RESULTS_DIR / f'summary_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.txt'
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("分析结果总结\n")
        f.write("="*60 + "\n\n")
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")
    
    print(f"分析总结已保存到: {summary_path}")
    
    print("\n" + "="*60)
    print("分析完成！")
    print("="*60)


if __name__ == '__main__':
    main()

