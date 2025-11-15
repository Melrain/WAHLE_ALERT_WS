"""配置文件"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# API配置
WHALE_ALERT_API_KEY = os.getenv('WHALE_ALERT_API_KEY', '')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')

# 数据配置
DEFAULT_SYMBOL = os.getenv('DEFAULT_SYMBOL', 'BTCUSDT')
DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'UTC')

# 数据目录
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
RESULTS_DIR = DATA_DIR / 'results'

# 创建数据目录（如果不存在）
DATA_DIR.mkdir(exist_ok=True)
RAW_DATA_DIR.mkdir(exist_ok=True)
PROCESSED_DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Whale Alert API配置
WHALE_ALERT_BASE_URL = 'https://api.whale-alert.io/v1'
# WebSocket端点（根据官方文档：wss://leviathan.whale-alert.io/ws?api_key={key}）
# 如果配置了自定义端点，将优先使用
WHALE_ALERT_WS_URL = os.getenv('WHALE_ALERT_WS_URL', '')  # 如果为空，将使用官方默认端点

# WebSocket 订阅配置
# 根据官方文档：blockchains 和 symbols 都是可选参数
# - 如果省略 blockchains，API 会自动包含所有区块链（推荐）
# - 如果省略 symbols，API 会自动包含所有币种

# 币种列表（逗号分隔，小写），例如: "btc,eth,xrp,usdt"
# 注意：如果留空，API 会自动包含所有币种
# 注意：Whale Alert API 每小时最多接收 100 条警报，建议根据需求选择币种数量
symbols_str = os.getenv('SYMBOLS', '').strip()
SYMBOLS = [s.strip().lower() for s in symbols_str.split(',') if s.strip()] if symbols_str else []

# 区块链列表（逗号分隔，小写），例如: "bitcoin,ethereum,ripple"
# 注意：如果留空，API 会自动包含所有区块链（推荐方式）
# 常见正确的区块链名称: bitcoin, ethereum, solana, avalanche, polygon, bsc, ripple, tron
# 默认值：空（不指定区块链，自动监测所有链）
blockchains_str = os.getenv('BLOCKCHAINS', '').strip()
BLOCKCHAINS = [b.strip().lower() for b in blockchains_str.split(',') if b.strip()] if blockchains_str else []

# 最小转账金额（美元）
WHALE_ALERT_MIN_VALUE_USD = float(os.getenv('WHALE_ALERT_MIN_VALUE_USD', '500000'))

# Binance API配置
BINANCE_BASE_URL = 'https://api.binance.com/api/v3'

# Redis配置
# 优先使用 REDIS_URL，格式: redis://[:password@]host[:port][/db]
# 例如: redis://localhost:6379/0 或 redis://:password@localhost:6379/0
REDIS_URL = os.getenv('REDIS_URL', '')

# 如果未设置 REDIS_URL，则使用以下配置（向后兼容）
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)  # 如果Redis有密码

