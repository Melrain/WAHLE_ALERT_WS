"""可视化工具模块"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Optional
import matplotlib.dates as mdates

# 设置中文字体（如果需要）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置样式
sns.set_style("whitegrid")
sns.set_palette("husl")


def plot_time_series(
    series_dict: dict,
    title: str = "时间序列图",
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None
):
    """
    绘制多个时间序列
    
    参数:
    - series_dict: {name: series} 字典
    - title: 图表标题
    - figsize: 图表大小
    - save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    for name, series in series_dict.items():
        ax.plot(series.index, series.values, label=name, linewidth=1.5)
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('值', fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # 格式化x轴日期
    if isinstance(series.index, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    plt.show()


def plot_granger_results(
    granger_result: dict,
    title: str = "Granger因果检验结果",
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None
):
    """
    可视化Granger因果检验结果
    
    参数:
    - granger_result: Granger检验结果字典
    - title: 图表标题
    - figsize: 图表大小
    - save_path: 保存路径
    """
    if not granger_result.get('success', False):
        print("Granger检验未成功执行")
        return
    
    results_df = granger_result['results']
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
    
    # 绘制p-value
    ax1.plot(results_df['lag'], results_df['p_value'], 
             marker='o', linewidth=2, markersize=6, label='p-value')
    ax1.axhline(y=0.05, color='r', linestyle='--', linewidth=1.5, label='显著性水平 (0.05)')
    ax1.fill_between(results_df['lag'], 0, 0.05, alpha=0.2, color='green', label='显著区域')
    ax1.set_ylabel('p-value', fontsize=12)
    ax1.set_title(f'{title} - p-value', fontsize=12, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # 绘制F统计量
    ax2.plot(results_df['lag'], results_df['f_statistic'], 
             marker='s', linewidth=2, markersize=6, color='orange', label='F统计量')
    ax2.set_xlabel('滞后阶数', fontsize=12)
    ax2.set_ylabel('F统计量', fontsize=12)
    ax2.set_title('F统计量', fontsize=12, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    plt.show()


def plot_correlation_heatmap(
    data: pd.DataFrame,
    title: str = "相关性热力图",
    figsize: tuple = (10, 8),
    save_path: Optional[str] = None
):
    """
    绘制相关性热力图
    
    参数:
    - data: DataFrame
    - title: 图表标题
    - figsize: 图表大小
    - save_path: 保存路径
    """
    corr_matrix = data.corr()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt='.2f',
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=1,
        cbar_kws={"shrink": 0.8},
        ax=ax
    )
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    plt.show()


def plot_lagged_correlation(
    lagged_corr_df: pd.DataFrame,
    title: str = "滞后相关性分析",
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None
):
    """
    绘制滞后相关性图
    
    参数:
    - lagged_corr_df: 滞后相关性DataFrame
    - title: 图表标题
    - figsize: 图表大小
    - save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(lagged_corr_df['lag'], lagged_corr_df['correlation'], 
            marker='o', linewidth=2, markersize=8, label='相关系数')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax.fill_between(lagged_corr_df['lag'], 0, lagged_corr_df['correlation'], 
                    where=(lagged_corr_df['correlation'] > 0), alpha=0.3, color='green')
    ax.fill_between(lagged_corr_df['lag'], 0, lagged_corr_df['correlation'], 
                    where=(lagged_corr_df['correlation'] < 0), alpha=0.3, color='red')
    
    ax.set_xlabel('滞后阶数', fontsize=12)
    ax.set_ylabel('相关系数', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    plt.show()


def plot_event_impact(
    events_df: pd.DataFrame,
    price_series: pd.Series,
    window_hours: int = 24,
    title: str = "事件影响分析",
    figsize: tuple = (14, 8),
    save_path: Optional[str] = None
):
    """
    可视化事件对价格的影响
    
    参数:
    - events_df: 事件DataFrame，包含timestamp列
    - price_series: 价格时间序列
    - window_hours: 观察窗口（小时）
    - title: 图表标题
    - figsize: 图表大小
    - save_path: 保存路径
    """
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)
    
    # 绘制价格序列
    axes[0].plot(price_series.index, price_series.values, 
                 linewidth=1.5, alpha=0.7, label='价格')
    
    # 标记事件
    for _, event in events_df.iterrows():
        event_time = pd.to_datetime(event['timestamp'])
        if event_time in price_series.index:
            axes[0].axvline(x=event_time, color='red', linestyle='--', 
                           linewidth=1, alpha=0.7)
            axes[0].scatter(event_time, price_series.loc[event_time], 
                           color='red', s=100, zorder=5, marker='v')
    
    axes[0].set_ylabel('价格', fontsize=12)
    axes[0].set_title('价格序列与事件标记', fontsize=12, fontweight='bold')
    axes[0].legend(loc='best')
    axes[0].grid(True, alpha=0.3)
    
    # 绘制事件后的价格变化
    impact_data = []
    for _, event in events_df.iterrows():
        event_time = pd.to_datetime(event['timestamp'])
        if event_time in price_series.index:
            baseline_price = price_series.loc[event_time]
            future_prices = price_series[event_time:event_time + pd.Timedelta(hours=window_hours)]
            if len(future_prices) > 1:
                price_changes = (future_prices - baseline_price) / baseline_price * 100
                impact_data.append({
                    'event_time': event_time,
                    'price_changes': price_changes
                })
    
    if impact_data:
        for impact in impact_data:
            axes[1].plot(impact['price_changes'].index, impact['price_changes'].values,
                        linewidth=1.5, alpha=0.5)
        
        axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        axes[1].set_xlabel('时间', fontsize=12)
        axes[1].set_ylabel('价格变化 (%)', fontsize=12)
        axes[1].set_title(f'事件后{window_hours}小时内的价格变化', fontsize=12, fontweight='bold')
        axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    plt.show()


if __name__ == '__main__':
    # 测试代码
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    series1 = pd.Series(np.random.randn(100).cumsum(), index=dates, name='Series1')
    series2 = pd.Series(np.random.randn(100).cumsum(), index=dates, name='Series2')
    
    plot_time_series({'Series1': series1, 'Series2': series2})

