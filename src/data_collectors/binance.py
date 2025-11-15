"""Binance API数据收集器"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List
import time

from config import settings


class BinanceCollector:
    """Binance API数据收集器"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        初始化收集器
        
        参数:
        - api_key: Binance API密钥（可选，公开数据可能不需要）
        - api_secret: Binance API密钥（可选）
        """
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_API_SECRET
        self.base_url = settings.BINANCE_BASE_URL
    
    def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        获取K线数据
        
        参数:
        - symbol: 交易对，如 'BTCUSDT'
        - interval: K线间隔，如 '1h', '1d', '1m'
        - start_time: 开始时间
        - end_time: 结束时间
        - limit: 每次请求的最大记录数（最大1000）
        
        返回:
        - DataFrame，包含K线数据
        """
        all_klines = []
        current_start = start_time
        
        while True:
            # 构建请求参数
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            if current_start:
                params['startTime'] = int(current_start.timestamp() * 1000)
            
            if end_time:
                params['endTime'] = int(end_time.timestamp() * 1000)
            
            try:
                response = requests.get(
                    f'{self.base_url}/klines',
                    params=params
                )
                response.raise_for_status()
                
                klines = response.json()
                
                if not klines:
                    break
                
                all_klines.extend(klines)
                
                # 如果返回的记录数少于limit，说明已经获取完数据
                if len(klines) < limit:
                    break
                
                # 更新起始时间为最后一条K线的结束时间
                last_kline_time = datetime.fromtimestamp(klines[-1][6] / 1000)
                current_start = last_kline_time + timedelta(milliseconds=1)
                
                # 如果已经到达结束时间，停止
                if end_time and current_start >= end_time:
                    break
                
                # 避免请求过快
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                print(f"请求错误: {e}")
                break
        
        # 转换为DataFrame
        if not all_klines:
            return pd.DataFrame()
        
        df = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # 数据类型转换
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                          'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 设置时间索引
        df = df.set_index('open_time')
        
        return df
    
    def calculate_price_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算价格变化率
        
        参数:
        - df: K线数据DataFrame
        
        返回:
        - 添加了价格变化列的DataFrame
        """
        df = df.copy()
        
        # 计算价格变化率（百分比）
        df['price_change_pct'] = df['close'].pct_change() * 100
        
        # 计算对数收益率
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
        
        # 计算波动率（滚动窗口）
        df['volatility'] = df['price_change_pct'].rolling(window=24).std()
        
        return df
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格
        
        参数:
        - symbol: 交易对，如 'BTCUSDT'
        
        返回:
        - 当前价格，如果获取失败返回None
        """
        try:
            params = {'symbol': symbol}
            response = requests.get(
                f'{self.base_url}/ticker/price',
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return float(data.get('price', 0))
        except Exception as e:
            print(f"获取价格失败 {symbol}: {e}")
            return None
    
    def get_24h_ticker(self, symbol: str) -> Optional[dict]:
        """
        获取24小时价格统计
        
        参数:
        - symbol: 交易对
        
        返回:
        - 24小时统计数据字典
        """
        try:
            params = {'symbol': symbol}
            response = requests.get(
                f'{self.base_url}/ticker/24hr',
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取24h统计失败 {symbol}: {e}")
            return None


def collect_kline_data(
    symbol: str,
    interval: str,
    start_date: datetime,
    end_date: datetime,
    save_path: Optional[str] = None
) -> pd.DataFrame:
    """
    便捷函数：收集Binance K线数据
    
    参数:
    - symbol: 交易对
    - interval: K线间隔
    - start_date: 开始日期
    - end_date: 结束日期
    - save_path: 保存路径（可选）
    
    返回:
    - DataFrame
    """
    collector = BinanceCollector()
    df = collector.get_klines(
        symbol=symbol,
        interval=interval,
        start_time=start_date,
        end_time=end_date
    )
    
    # 计算价格变化
    df = collector.calculate_price_changes(df)
    
    # 保存数据
    if save_path:
        df.to_csv(save_path, index=True)
        print(f"数据已保存到: {save_path}")
    
    return df


if __name__ == '__main__':
    # 测试代码
    collector = BinanceCollector()
    
    # 测试获取当前价格
    print("测试获取当前价格...")
    price = collector.get_current_price('BTCUSDT')
    if price:
        print(f"BTC当前价格: ${price:,.2f}")
    
    # 测试获取K线数据
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print("\n测试获取K线数据...")
    df = collector.get_klines(
        symbol='BTCUSDT',
        interval='1h',
        start_time=start_date,
        end_time=end_date
    )
    print(f"获取到 {len(df)} 条K线数据")
    if not df.empty:
        print(df.head())

