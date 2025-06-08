from bot.crud.base import CRUDBase
from bot.models.recharge_order import RechargeOrder


class CRUDRechargeOrder(CRUDBase[RechargeOrder]):
    pass


recharge_order = CRUDRechargeOrder(RechargeOrder) 