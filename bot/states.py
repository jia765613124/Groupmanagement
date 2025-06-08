from aiogram.fsm.state import State, StatesGroup


class Menu(StatesGroup):
    """
    菜单状态组
    定义机器人菜单的不同状态
    """
    lang = State()  # 语言设置状态
    help = State()  # 帮助信息状态
    waiting_for_link = State()  # 等待输入链接状态
    waiting_for_amount = State()  # 等待输入充值金额状态
    waiting_for_usdt_exchange_amount = State() # 等待用户输入 USDT 兑换数量
    waiting_for_order_identifiers = State() # 等待用户输入订单标识符列表
