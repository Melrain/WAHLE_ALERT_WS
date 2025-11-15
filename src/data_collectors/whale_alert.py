"""Whale Alert API数据收集器"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import time
import urllib3

# 禁用SSL警告（仅在必要时使用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import settings


class WhaleAlertCollector:
    """Whale Alert API数据收集器"""
    
    # Developer API限制：最多30天（2592000秒）
    MAX_HISTORY_SECONDS = 2592000  # 30天
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化收集器
        
        参数:
        - api_key: Whale Alert API密钥，如果不提供则从配置文件读取
        """
        self.api_key = api_key or settings.WHALE_ALERT_API_KEY
        if not self.api_key:
            raise ValueError("需要提供Whale Alert API密钥")
        
        self.base_url = settings.WHALE_ALERT_BASE_URL
        self.headers = {
            'X-WA-API-KEY': self.api_key
        }
    
    def get_transactions(
        self,
        start: datetime,
        end: datetime,
        min_value: int = 500000,  # 最小转账金额（美元）
        currency: str = 'btc',
        limit: int = 100
    ) -> pd.DataFrame:
        """
        获取指定时间范围内的转账数据
        
        根据Whale Alert API文档，使用cursor机制来防止重复或丢失交易。
        Developer API计划最多只能获取30天的历史数据。
        参考: https://developer.whale-alert.io/documentation/
        
        参数:
        - start: 开始时间
        - end: 结束时间
        - min_value: 最小转账金额（美元）
        - currency: 币种（btc, eth等）
        - limit: 每次请求的最大记录数（最大100）
        
        返回:
        - DataFrame，包含转账数据
        """
        # 检查start时间是否超过30天前
        now = datetime.now()
        max_start_time = now - timedelta(seconds=self.MAX_HISTORY_SECONDS)
        
        # 确保start时间不早于30天前（API限制）
        if start < max_start_time:
            print(f"警告: 开始时间 ({start.strftime('%Y-%m-%d %H:%M:%S')}) 超过API限制 (最多30天前)")
            print(f"将开始时间调整为: {max_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            start = max_start_time
        
        # 确保end时间不超过当前时间
        if end > now:
            print(f"警告: 结束时间 ({end.strftime('%Y-%m-%d %H:%M:%S')}) 超过当前时间，将调整为当前时间")
            end = now
        
        # 确保start不晚于end
        if start >= end:
            print(f"错误: 开始时间 ({start.strftime('%Y-%m-%d %H:%M:%S')}) 不早于结束时间 ({end.strftime('%Y-%m-%d %H:%M:%S')})")
            return pd.DataFrame()
        
        # 检查时间范围
        time_diff = (end - start).total_seconds()
        
        # 再次验证：确保start时间不早于30天前（双重检查）
        if (now - start).total_seconds() > self.MAX_HISTORY_SECONDS:
            print(f"错误: 开始时间仍然超出范围。当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}, 开始时间: {start.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"时间差: {(now - start).total_seconds() / 86400:.1f} 天，最大允许: {self.MAX_HISTORY_SECONDS / 86400} 天")
            # 强制调整为30天前
            start = max_start_time
            time_diff = (end - start).total_seconds()
        
        if time_diff > self.MAX_HISTORY_SECONDS:
            print(f"警告: 请求的时间范围 ({time_diff/86400:.1f} 天) 超过API限制 (30天)")
            print(f"将自动分割成多个30天的请求...")
            
            # 分割成多个30天的请求
            all_transactions = []
            current_start = start
            
            while current_start < end:
                current_end = min(current_start + timedelta(seconds=self.MAX_HISTORY_SECONDS), end)
                print(f"正在获取: {current_start.strftime('%Y-%m-%d')} 到 {current_end.strftime('%Y-%m-%d')}")
                
                batch_data = self._get_transactions_single_batch(
                    current_start, current_end, min_value, currency, limit
                )
                
                if not batch_data.empty:
                    all_transactions.extend(batch_data.to_dict('records'))
                
                current_start = current_end
                
                # 避免请求过快
                if current_start < end:
                    time.sleep(1.0)
            
            # 转换为DataFrame
            if not all_transactions:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_transactions)
            return self._process_transactions_df(df)
        
        # 时间范围在限制内，直接获取
        return self._get_transactions_single_batch(start, end, min_value, currency, limit)
    
    def _get_transactions_single_batch(
        self,
        start: datetime,
        end: datetime,
        min_value: int,
        currency: str,
        limit: int
    ) -> pd.DataFrame:
        """
        获取单个批次（30天内）的转账数据
        
        参数:
        - start: 开始时间
        - end: 结束时间（必须在start的30天内）
        - min_value: 最小转账金额
        - currency: 币种
        - limit: 每次请求的最大记录数
        
        返回:
        - DataFrame，包含转账数据
        """
        all_transactions = []
        
        # 最终验证：使用最新的当前时间重新计算，确保start时间戳不超过30天前
        now = datetime.now()
        now_timestamp = int(now.timestamp())
        max_start_timestamp = now_timestamp - self.MAX_HISTORY_SECONDS
        
        # 重新计算start_timestamp，确保不超过限制
        start_timestamp = int(start.timestamp())
        if start_timestamp < max_start_timestamp:
            print(f"最终验证: start时间戳 ({start_timestamp}) 早于允许的最小时间戳 ({max_start_timestamp})")
            print(f"将start时间戳调整为: {max_start_timestamp} (当前时间: {now_timestamp})")
            start_timestamp = max_start_timestamp
            # 重新计算start datetime
            start = datetime.fromtimestamp(start_timestamp)
        
        # 重新计算end_timestamp，确保不超过当前时间
        end_timestamp = int(end.timestamp())
        if end_timestamp > now_timestamp:
            print(f"最终验证: end时间戳 ({end_timestamp}) 超过当前时间戳 ({now_timestamp})")
            print(f"将end时间戳调整为: {now_timestamp}")
            end_timestamp = now_timestamp
            end = datetime.fromtimestamp(end_timestamp)
        
        # 确保时间范围不超过30天
        if end_timestamp - start_timestamp > self.MAX_HISTORY_SECONDS:
            print(f"最终验证: 时间范围 ({end_timestamp - start_timestamp}秒) 超过30天限制，将end调整为start+30天")
            end_timestamp = start_timestamp + self.MAX_HISTORY_SECONDS
            end = datetime.fromtimestamp(end_timestamp)
        
        # 最终检查：确保start时间戳不早于30天前（使用最新时间）
        # 添加1秒的安全边距，避免时间戳计算误差
        final_now_timestamp = int(datetime.now().timestamp())
        final_max_start = final_now_timestamp - self.MAX_HISTORY_SECONDS + 1  # 加1秒安全边距
        if start_timestamp < final_max_start:
            print(f"最终检查: start时间戳 ({start_timestamp}) 早于允许的最小时间戳 ({final_max_start})")
            print(f"将start时间戳调整为: {final_max_start} (当前时间: {final_now_timestamp})")
            start_timestamp = final_max_start
            start = datetime.fromtimestamp(start_timestamp)
            # 重新调整end
            if end_timestamp - start_timestamp > self.MAX_HISTORY_SECONDS:
                end_timestamp = start_timestamp + self.MAX_HISTORY_SECONDS
                end = datetime.fromtimestamp(end_timestamp)
        
        # 最后一次验证：确保时间差不超过30天（留1秒安全边距）
        actual_time_diff = end_timestamp - start_timestamp
        if actual_time_diff >= self.MAX_HISTORY_SECONDS:
            print(f"警告: 实际时间差 ({actual_time_diff}秒) 达到或超过30天限制，调整为29天23小时59秒")
            end_timestamp = start_timestamp + self.MAX_HISTORY_SECONDS - 1  # 减1秒确保不超过
            end = datetime.fromtimestamp(end_timestamp)
        
        cursor = None  # cursor用于分页，防止重复或丢失交易
        
        # 构建基础请求参数（start时间在使用cursor时保持不变）
        base_params = {
            'start': start_timestamp,
            'min_value': min_value,
            'currency': currency,
            'limit': limit
        }
        
        print(f"请求参数: start={start_timestamp} ({start.strftime('%Y-%m-%d %H:%M:%S')}), end={end_timestamp} ({end.strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"时间差: {(end_timestamp - start_timestamp) / 86400:.2f} 天")
        
        # 第一次请求不使用end参数，后续使用cursor时也不使用end
        # 只在需要限制结束时间时，在最后一批请求中使用end
        use_end = True  # 是否使用end参数
        
        while True:
            # 构建当前请求的参数
            params = base_params.copy()
            
            # 如果接近结束时间，添加end参数
            if use_end:
                params['end'] = end_timestamp
            
            # 如果有cursor，添加cursor参数
            if cursor:
                params['cursor'] = cursor
                # 使用cursor时，不添加end参数（根据文档建议）
                params.pop('end', None)
            
            # 重试逻辑 - 简化版本，避免卡住
            max_retries = 2  # 减少重试次数，避免长时间等待
            retry_count = 0
            success = False
            response_data = None
            
            while retry_count < max_retries and not success:
                try:
                    # 先尝试正常SSL验证
                    verify_ssl = retry_count == 0  # 第一次尝试使用SSL验证
                    
                    response = requests.get(
                        f'{self.base_url}/transactions',
                        headers=self.headers,
                        params=params,
                        timeout=30,  # 30秒超时，避免卡住
                        verify=verify_ssl,
                        allow_redirects=True
                    )
                    
                    # 检查HTTP状态码
                    if response.status_code == 400:
                        # 400错误通常是参数问题，不重试
                        error_data = response.json() if response.content else {}
                        error_msg = error_data.get('message', 'Bad Request')
                        print(f"400错误（参数问题）: {error_msg}")
                        # 如果是时间范围问题，返回空DataFrame
                        if 'out of range' in error_msg.lower() or 'maximum transaction history' in error_msg.lower():
                            print("提示: 时间范围超出API限制，请缩短时间范围")
                        return pd.DataFrame()
                    
                    response.raise_for_status()
                    response_data = response.json()
                    success = True
                    
                    if not verify_ssl:
                        print("警告: 使用未验证的SSL连接成功，建议检查网络配置")
                    
                except requests.exceptions.SSLError as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        # 第二次尝试禁用SSL验证
                        print(f"SSL错误，尝试禁用SSL验证重试 ({retry_count}/{max_retries})")
                        time.sleep(2)  # 短暂等待
                    else:
                        print(f"SSL错误，所有重试都失败")
                        print(f"错误详情: {str(e)[:150]}")
                        print(f"建议: 检查网络连接或稍后重试")
                        return pd.DataFrame()
                        
                except requests.exceptions.Timeout as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"请求超时，{2}秒后重试 ({retry_count}/{max_retries})")
                        time.sleep(2)
                    else:
                        print(f"请求超时，已达到最大重试次数")
                        return pd.DataFrame()
                        
                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code if e.response else 0
                    
                    # 处理可重试的HTTP错误
                    if status_code in [429, 500, 502, 503, 504]:
                        # 429: Too Many Requests
                        # 500, 502, 503, 504: 服务器错误，可以重试
                        retry_count += 1
                        if retry_count < max_retries:
                            if status_code == 429:
                                wait_time = 10  # 429错误等待更长时间
                            else:
                                wait_time = 5  # 服务器错误等待5秒
                            
                            error_name = {
                                429: "请求过于频繁",
                                500: "服务器内部错误",
                                502: "网关错误",
                                503: "服务不可用",
                                504: "网关超时"
                            }.get(status_code, f"HTTP {status_code}")
                            
                            print(f"{error_name}({status_code})，{wait_time}秒后重试 ({retry_count}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            error_name = {
                                429: "请求过于频繁",
                                500: "服务器内部错误",
                                502: "网关错误",
                                503: "服务不可用",
                                504: "网关超时"
                            }.get(status_code, f"HTTP {status_code}")
                            print(f"{error_name}({status_code})，已达到最大重试次数")
                            print("建议: 稍后重试或检查API服务状态")
                            return pd.DataFrame()
                    else:
                        # 其他HTTP错误（如400, 401, 403等），不重试
                        print(f"HTTP错误 {status_code}: {str(e)[:100]}")
                        if status_code == 401:
                            print("提示: 可能是API密钥无效或过期")
                        elif status_code == 403:
                            print("提示: 可能是API权限不足")
                        return pd.DataFrame()
                        
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"请求错误，{2}秒后重试 ({retry_count}/{max_retries}): {str(e)[:80]}")
                        time.sleep(2)
                    else:
                        print(f"请求错误，已达到最大重试次数: {str(e)[:80]}")
                        return pd.DataFrame()
            
            # 如果所有重试都失败，返回已收集的数据
            if not success or not response_data:
                break
            
            # 处理响应数据
            if response_data.get('result') == 'success' and 'transactions' in response_data:
                transactions = response_data['transactions']
                
                # 过滤掉超过结束时间的交易
                filtered_transactions = [
                    tx for tx in transactions 
                    if tx.get('timestamp', 0) <= end_timestamp
                ]
                
                if not filtered_transactions:
                    # 没有更多在时间范围内的交易
                    break
                
                all_transactions.extend(filtered_transactions)
                
                # 获取cursor用于下一次请求
                cursor = response_data.get('cursor')
                
                # 如果返回的交易数少于limit，或者没有cursor，说明已经获取完数据
                if len(transactions) < limit or not cursor:
                    break
                
                # 检查是否已经超过结束时间
                last_timestamp = max(tx.get('timestamp', 0) for tx in filtered_transactions)
                if last_timestamp >= end_timestamp:
                    break
                
            else:
                # API返回失败
                error_msg = response_data.get('message', 'Unknown error')
                if response_data.get('result') != 'success':
                    print(f"API返回错误: {error_msg}")
                break
            
            # 避免请求过快
            time.sleep(1.5)  # 1.5秒间隔，减少请求频率
        
        # 转换为DataFrame
        if not all_transactions:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_transactions)
        return self._process_transactions_df(df)
    
    def _process_transactions_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理交易DataFrame：清洗和格式化
        
        参数:
        - df: 原始交易DataFrame
        
        返回:
        - 处理后的DataFrame
        """
        if df.empty:
            return pd.DataFrame()
        
        # 数据清洗和格式化
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # 提取关键字段
        columns_to_keep = [
            'timestamp', 'hash', 'amount', 'amount_usd', 
            'from', 'to', 'blockchain'
        ]
        available_columns = [col for col in columns_to_keep if col in df.columns]
        df = df[available_columns]
        
        # 重命名列
        df = df.rename(columns={
            'from': 'from_address',
            'to': 'to_address'
        })
        
        return df
    
    def detect_exchange_direction(self, address: str) -> Optional[str]:
        """
        检测地址是否为交易所（简单版本）
        注意：实际应用中需要维护交易所地址列表
        
        参数:
        - address: 钱包地址
        
        返回:
        - 'in': 转入交易所
        - 'out': 转出交易所
        - None: 无法判断
        """
        # 这里应该维护一个交易所地址列表
        # 简化版本，实际需要从Whale Alert或其他来源获取
        exchange_addresses = {
            # 示例：Binance热钱包地址（需要实际维护）
            # '34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo': 'binance',
        }
        
        # 如果地址在交易所列表中，判断方向
        # 这里简化处理，实际需要根据from/to地址判断
        return None
    
    def enrich_with_direction(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为数据添加方向信息（转入/转出交易所）
        
        参数:
        - df: 转账数据DataFrame
        
        返回:
        - 添加了direction列的DataFrame
        """
        # 简化版本：根据from/to地址判断
        # 实际应用中需要维护交易所地址数据库
        df['direction'] = 'unknown'
        
        # 这里可以添加更复杂的逻辑来判断方向
        # 例如：检查from_address或to_address是否在交易所地址列表中
        
        return df


def collect_whale_data(
    start_date: datetime,
    end_date: datetime,
    currency: str = 'btc',
    min_value: int = 500000,
    save_path: Optional[str] = None
) -> pd.DataFrame:
    """
    便捷函数：收集Whale Alert数据
    
    参数:
    - start_date: 开始日期
    - end_date: 结束日期
    - currency: 币种
    - min_value: 最小转账金额（美元）
    - save_path: 保存路径（可选）
    
    返回:
    - DataFrame
    """
    collector = WhaleAlertCollector()
    df = collector.get_transactions(
        start=start_date,
        end=end_date,
        min_value=min_value,
        currency=currency
    )
    
    # 添加方向信息
    df = collector.enrich_with_direction(df)
    
    # 保存数据
    if save_path:
        df.to_csv(save_path, index=False)
        print(f"数据已保存到: {save_path}")
    
    return df


if __name__ == '__main__':
    # 测试代码
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print("开始收集Whale Alert数据...")
    df = collect_whale_data(
        start_date=start_date,
        end_date=end_date,
        currency='btc',
        min_value=1000000
    )
    
    print(f"收集到 {len(df)} 条记录")
    print(df.head())

