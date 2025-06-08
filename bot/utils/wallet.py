import io
from typing import Tuple, Optional, List, Dict
import qrcode
from qrcode.constants import ERROR_CORRECT_L
from tronpy import Tron
from tronpy.exceptions import BadAddress, TaposError
from decimal import Decimal
import logging
import aiohttp
from datetime import datetime, timedelta, timezone
import time

from bot.config import get_config
from tronpy.defaults import CONF_NILE

config = get_config()
logger = logging.getLogger(__name__)

# Tron 网络客户端
# tron_client = Tron(network='mainnet')  # 主网
tron_client = Tron(network='nile')  # 测试网

# USDT-TRC20 合约地址
# USDT_CONTRACT_ADDRESS = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # 主网 USDT 合约地址
USDT_CONTRACT_ADDRESS = "TC9wtcWAZzZ5squ5DB8x9UAQ1nYNP25RDW"  # Nile 测试网 USDT 合约地址

# TronGrid API Key
TRON_GRID_API_KEY = '6653feb4-1d45-45f7-a692-d7e91427830c'

# API URL
# API_URL = "https://api.trongrid.io"  # 主网 API URL
API_URL = "https://nile.trongrid.io"  # 测试网 API URL

# USDT-TRC20 合约 ABI (部分关键事件和函数)
USDT_CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "constant": True,
        "inputs": [{"name": "who", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

def generate_qr_code(address: str, amount: Optional[float] = None) -> Tuple[bytes, str]:
    """
    生成 USDT-TRC20 充值二维码
    """
    # 只显示地址，不带合约和金额
    qr_content = address

    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    # 创建图片
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 转换为字节
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr, qr_content

def validate_tron_address(address: str) -> bool:
    """
    验证 Tron 地址是否有效
    
    Args:
        address: Tron 钱包地址
        
    Returns:
        bool: 地址是否有效
    """
    try:
        tron_client.get_account(address)
        return True
    except BadAddress:
        return False
    except Exception:
        return False

def get_tron_balance(address: str) -> float:
    """
    获取 Tron 地址的 USDT-TRC20 余额
    
    Args:
        address: Tron 钱包地址
        
    Returns:
        float: USDT 余额
    """
    try:
        # USDT-TRC20 合约地址
        # contract_address = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
        # 使用 ABI 获取合约
        # contract = tron_client.get_contract(USDT_CONTRACT_ADDRESS, abi=USDT_CONTRACT_ABI)
        
        # 先获取合约对象，再设置ABI
        contract = tron_client.get_contract(USDT_CONTRACT_ADDRESS)
        contract.abi = USDT_CONTRACT_ABI
        
        # 调用合约的 balanceOf 方法
        # balance = contract.functions.balanceOf(address) / 1_000_000  # USDT 有 6 位小数
        balance = contract.functions.balanceOf(address).call() / (10**6) # USDT 有 6 位小数
        return float(balance)
    except Exception as e:
        print(f"获取余额失败: {e}")
        return 0.0

async def check_recharge_status(address: str, start_timestamp: Optional[str] = None, end_timestamp: Optional[str] = None) -> List[Dict]:
    """
    获取指定地址在特定时间范围内的 USDT (TRC20) 交易记录
    """
    logger.info(f"开始获取 USDT (TRC20) 交易记录 - 地址: {address}, 时间范围: {start_timestamp}-{end_timestamp}")
    try:
        # 使用 TronGrid v1 API 查询 TRC20 交易端点
        api_url = API_URL
        logger.debug(f"使用 API 地址: {api_url}")

        # 获取 TronGrid API Key
        tron_grid_api_key = TRON_GRID_API_KEY
        headers = {}
        if tron_grid_api_key:
            headers['TRON-PRO-API-KEY'] = tron_grid_api_key
            logger.debug("使用 TronGrid API Key")
        else:
            logger.warning("未配置 TronGrid API Key，请求可能会受到限制或失败。")

        # 使用 aiohttp 发送请求获取账户 TRC20 交易列表
        async with aiohttp.ClientSession() as session:
            list_url = f"{api_url}/v1/accounts/{address}/transactions/trc20"
            list_params = {
                "only_confirmed": "true",  # 只查询已确认的交易
                "limit": 200,  # 提高 limit 到最大 200
            }
            # 添加时间戳过滤参数（如果提供）
            if start_timestamp is not None:
                list_params['min_timestamp'] = start_timestamp
            if end_timestamp is not None:
                list_params['max_timestamp'] = end_timestamp

            logger.info(f"正在获取账户 TRC20 交易列表: {list_url} with params {list_params}")

            async with session.get(list_url, params=list_params, headers=headers) as response:
                response_text = await response.text()
                logger.info(f"获取 TRC20 交易列表响应状态码: {response.status}")
                logger.debug(f"获取 TRC20 交易列表响应内容: {response_text}")

                if response.status != 200:
                    logger.error(f"获取 TRC20 交易列表失败 - 状态码: {response.status}, 响应内容: {response_text}")
                    return []

                try:
                    list_data = await response.json()
                except aiohttp.ContentTypeError:
                    logger.error(f"获取 TRC20 交易列表响应内容不是有效的 JSON: {response_text}")
                    return []

                if not isinstance(list_data, dict) or "data" not in list_data:
                    logger.warning(f"TRC20 交易列表数据格式错误: {list_data}")
                    return []

                transactions = []
                tx_list = list_data.get("data", [])
                logger.info(f"获取到 {len(tx_list)} 条 TRC20 交易记录")

                # 解析时间参数为毫秒时间戳
                def parse_iso8601_to_ms(dt_str):
                    try:
                        # 解析 UTC 时间字符串
                        dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')
                        # 确保时间是 UTC 时区
                        dt = dt.replace(tzinfo=timezone.utc)
                        # 转换为毫秒时间戳
                        return int(dt.timestamp() * 1000)
                    except Exception as e:
                        logger.error(f"解析时间字符串失败: {dt_str}, 错误: {str(e)}")
                        return None

                min_ts_ms = parse_iso8601_to_ms(start_timestamp) if start_timestamp else None
                max_ts_ms = parse_iso8601_to_ms(end_timestamp) if end_timestamp else None

                logger.info(f"时间范围: {start_timestamp} - {end_timestamp}")
                logger.info(f"转换为毫秒时间戳: {min_ts_ms} - {max_ts_ms}")
                if min_ts_ms and max_ts_ms:
                    logger.info(f"时间范围跨度: {(max_ts_ms - min_ts_ms) / 1000} 秒")

                # 遍历 TRC20 交易列表，查找转入交易
                for tx in tx_list:
                    tx_timestamp = tx.get("block_timestamp")
                    logger.info(f"链上交易时间: {datetime.utcfromtimestamp(tx_timestamp/1000)} (block_timestamp={tx_timestamp})")
                    # 检查是否是 USDT 交易
                    token_info = tx.get("token_info", {})
                    if token_info.get("symbol") != "USDT":
                        continue

                    # 检查交易类型
                    if tx.get("type") != "Transfer":
                        continue

                    tx_hash = tx.get("transaction_id")
                    if not tx_hash:
                        continue

                    # 检查主要的字段是否存在
                    tx_from = tx.get("from")
                    tx_to = tx.get("to")
                    tx_value = tx.get("value")

                    # 检查必要字段
                    if not all([tx_hash, tx_from, tx_to, tx_value is not None]):
                        logger.debug(f"跳过不符合条件的 TRC20 交易 {tx_hash} - 缺少字段")
                        continue

                    # 检查收款地址是否匹配
                    if tx_to != address:
                        logger.debug(f"跳过非收款 TRC20 交易 {tx_hash} - 期望收款地址: {address}, 实际收款地址: {tx_to}")
                        continue

                    # Python端二次过滤时间范围
                    if min_ts_ms and tx_timestamp < min_ts_ms:
                        continue
                    if max_ts_ms and tx_timestamp > max_ts_ms:
                        continue

                    try:
                        # 获取代币精度
                        decimals = token_info.get("decimals", 6)  # 默认 6 位小数
                        # 将交易金额从最小单位字符串转换为 USDT Decimal
                        tx_amount_usdt_decimal = Decimal(tx_value) / Decimal(10 ** decimals)
                        logger.debug(f"TRC20 交易 {tx_hash} 金额: {tx_value} (最小单位), 转换为 {tx_amount_usdt_decimal} USDT")

                        # 添加到结果列表
                        transactions.append({
                            'tx_hash': tx_hash,
                            'amount': float(tx_amount_usdt_decimal),
                            'timestamp': tx_timestamp
                        })

                    except Exception as parse_error:
                        logger.warning(f"解析 TRC20 交易 {tx_hash} 数据失败: {str(parse_error)}", exc_info=True)
                        continue

                logger.info(f"USDT (TRC20) 交易记录获取完成 - 找到 {len(transactions)} 笔转入交易 (二次过滤后)")
                return transactions

    except Exception as e:
        logger.error(f"检查 USDT (TRC20) 充值状态时发生错误: {str(e)}", exc_info=True)
        return [] 