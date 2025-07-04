"""
投注消息监控处理器
监控用户发送的投注消息，解析投注信息并自动下单
支持格式：大1000 大单100 数字8 押100
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.filters import Command

from bot.config.multi_game_config import MultiGameConfig
from bot.common.lottery_service import LotteryService
from bot.common.uow import UoW
from bot.database.db import SessionFactory

logger = logging.getLogger(__name__)

# 创建投注消息监控路由器
bet_message_monitor_router = Router(name="bet_message_monitor")

# 投注消息统计数据
bet_message_stats = {
    "total_bet_messages": 0,
    "successful_bets": 0,
    "failed_bets": 0,
    "bet_errors": {},  # 错误类型统计
    "start_time": datetime.now()
}

class BetMessageParser:
    """投注消息解析器"""
    
    def __init__(self):
        self.multi_config = MultiGameConfig()
        
        # 投注类型映射
        self.bet_type_mapping = {
            "大": "大", "小": "小", "单": "单", "双": "双",
            "大单": "大单", "大双": "大双", "小单": "小单", "小双": "小双",
            "豹子": "豹子"
        }
        
        # 数字映射
        self.number_mapping = {
            "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
            "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
            "零": "0", "一": "1", "二": "2", "三": "3", "四": "4",
            "五": "5", "六": "6", "七": "7", "八": "8", "九": "9"
        }
    
    def parse_bet_message(self, content: str) -> List[Dict[str, Any]]:
        """解析投注消息"""
        bets = []
        content = content.strip()
        # 匹配所有投注片段
        pattern = r'(?:[大小单双豹子]+\d+|\d+[大小单双豹子]+|(?:数字)?[0-9零一二三四五六七八九]\s*(?:押|下|注|买)?\d+|\d+(?:押|下|注|买)?[0-9零一二三四五六七八九])'
        matches = re.findall(pattern, content)
        for part in matches:
            part = part.strip()
            if not part:
                continue
            bet_info = self._parse_single_bet(part)
            if bet_info:
                bets.append(bet_info)
        return bets
    
    def _parse_single_bet(self, bet_text: str) -> Optional[Dict[str, Any]]:
        """解析单个投注"""
        try:
            original_text = bet_text
            # 不要移除投注相关词汇，保留用于正则匹配
            bet_text = bet_text.strip()
            
            # 匹配模式1: 投注类型 + 金额 (如: 大1000, 大单100, 豹子50)
            pattern1 = r'^([大小单双豹子]+)(\d+)$'
            match1 = re.match(pattern1, bet_text)
            if match1:
                bet_type = match1.group(1)
                amount = int(match1.group(2))
                if bet_type in self.bet_type_mapping and amount > 0:
                    return {
                        "type": "bet_type",
                        "bet_type": self.bet_type_mapping[bet_type],
                        "amount": amount,
                        "original_text": original_text
                    }
                else:
                    return None
            
            # 匹配模式2: 数字 + 金额 (如: 数字8 押100, 8 100)
            pattern2 = r'^(?:数字)?([0-9零一二三四五六七八九])\s*(?:押|下|注|买)?(\d+)$'
            match2 = re.match(pattern2, bet_text)
            if match2:
                number_str = match2.group(1)
                amount = int(match2.group(2))
                if number_str in self.number_mapping and amount > 0:
                    number = self.number_mapping[number_str]
                    return {
                        "type": "number",
                        "number": number,
                        "amount": amount,
                        "original_text": original_text
                    }
                else:
                    return None
            
            # 匹配模式3: 金额 + 投注类型 (如: 1000大, 100大单, 50豹子)
            pattern3 = r'^(\d+)([大小单双豹子]+)$'
            match3 = re.match(pattern3, bet_text)
            if match3:
                amount = int(match3.group(1))
                bet_type = match3.group(2)
                if bet_type in self.bet_type_mapping and amount > 0:
                    return {
                        "type": "bet_type",
                        "bet_type": self.bet_type_mapping[bet_type],
                        "amount": amount,
                        "original_text": original_text
                    }
                else:
                    return None
            
            # 匹配模式4: 金额 + 数字 (如: 1008, 1000押8)
            pattern4 = r'^(\d+)(?:押|下|注|买)?([0-9零一二三四五六七八九])$'
            match4 = re.match(pattern4, bet_text)
            if match4:
                amount = int(match4.group(1))
                number_str = match4.group(2)
                if number_str in self.number_mapping and amount > 0:
                    number = self.number_mapping[number_str]
                    return {
                        "type": "number",
                        "number": number,
                        "amount": amount,
                        "original_text": original_text
                    }
                else:
                    return None
            
            # 匹配模式5: 纯数字投注 (如: 8, 五)，但必须忽略"100"这种金额
            pattern5 = r'^([0-9零一二三四五六七八九])$'
            match5 = re.match(pattern5, bet_text)
            if match5:
                number_str = match5.group(1)
                # 只允许1位数字，且不能是金额（如100、200等）
                if number_str in self.number_mapping:
                    number = self.number_mapping[number_str]
                    return {
                        "type": "number",
                        "number": number,
                        "amount": 1,  # 默认金额为1
                        "original_text": original_text
                    }
                else:
                    return None
            
            # 其它情况全部视为无效投注
            return None
        except Exception as e:
            logger.error(f"解析投注文本失败: {bet_text}, 错误: {e}")
            return None

class BetMessageMonitor:
    """投注消息监控器"""
    
    def __init__(self):
        self.parser = BetMessageParser()
        self.multi_config = MultiGameConfig()
    
    async def process_bet_message(self, message: Message, content: str):
        """处理投注消息"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            # 更新统计
            bet_message_stats["total_bet_messages"] += 1
            
            logger.info(f"收到投注消息 | 用户: {message.from_user.full_name} (ID: {user_id}) | 群组: {message.chat.title} (ID: {chat_id}) | 内容: {content}")
            
            # 解析投注信息
            bets = self.parser.parse_bet_message(content)
            
            if not bets:
                logger.warning(f"投注消息解析失败: {content}")
                bet_message_stats["failed_bets"] += 1
                bet_message_stats["bet_errors"]["parse_failed"] = bet_message_stats["bet_errors"].get("parse_failed", 0) + 1
                return
            
            # 获取群组配置
            group_config = self.multi_config.get_group_config(chat_id)
            if not group_config:
                logger.warning(f"群组 {chat_id} 未配置游戏")
                bet_message_stats["failed_bets"] += 1
                bet_message_stats["bet_errors"]["group_not_configured"] = bet_message_stats["bet_errors"].get("group_not_configured", 0) + 1
                return
            
            if not group_config.enabled:
                logger.warning(f"群组 {chat_id} 游戏已禁用")
                bet_message_stats["failed_bets"] += 1
                bet_message_stats["bet_errors"]["game_disabled"] = bet_message_stats["bet_errors"].get("game_disabled", 0) + 1
                return
            
            # 执行投注
            success_count = 0
            failed_bets = []  # 记录失败的投注和原因
            
            for bet in bets:
                result = await self._place_bet(user_id, chat_id, group_config, bet)
                if result["success"]:
                    success_count += 1
                    bet_message_stats["successful_bets"] += 1
                    logger.info(f"投注成功: 用户={user_id}, 群组={chat_id}, 投注={bet}")
                else:
                    bet_message_stats["failed_bets"] += 1
                    error_type = result.get("error_type", "unknown")
                    bet_message_stats["bet_errors"][error_type] = bet_message_stats["bet_errors"].get(error_type, 0) + 1
                    logger.error(f"投注失败: 用户={user_id}, 群组={chat_id}, 投注={bet}, 错误={result['message']}")
                    
                    # 记录失败的投注和原因
                    failed_bet_info = {
                        "bet": bet,
                        "reason": result["message"]
                    }
                    failed_bets.append(failed_bet_info)
            
            # 发送投注结果反馈
            await self._send_bet_feedback(message, bets, success_count, failed_bets)
            
        except Exception as e:
            logger.error(f"处理投注消息失败: {e}")
            bet_message_stats["failed_bets"] += 1
            bet_message_stats["bet_errors"]["system_error"] = bet_message_stats["bet_errors"].get("system_error", 0) + 1
    
    async def _place_bet(self, user_id: int, group_id: int, group_config, bet: Dict[str, Any]) -> Dict[str, Any]:
        """执行投注"""
        try:
            async with SessionFactory() as session:
                uow = UoW(session)
                lottery_service = LotteryService(uow)
                
                if bet["type"] == "bet_type":
                    # 投注类型投注
                    result = await lottery_service.place_bet(
                        group_id=group_id,
                        telegram_id=user_id,
                        bet_type=bet["bet_type"],
                        bet_amount=bet["amount"]
                    )
                elif bet["type"] == "number":
                    # 数字投注
                    result = await lottery_service.place_bet(
                        group_id=group_id,
                        telegram_id=user_id,
                        bet_type=bet["number"],
                        bet_amount=bet["amount"]
                    )
                else:
                    return {
                        "success": False,
                        "message": "无效的投注类型",
                        "error_type": "invalid_bet_type"
                    }
                
                return result
                
        except Exception as e:
            logger.error(f"执行投注失败: {e}")
            return {
                "success": False,
                "message": f"系统错误: {e}",
                "error_type": "system_error"
            }
    
    async def _send_bet_feedback(self, message: Message, bets: List[Dict], success_count: int, failed_bets: List[Dict] = None):
        """发送投注反馈"""
        try:
            total_bets = len(bets)
            failed_bets = failed_bets or []
            
            if success_count == 0:
                feedback = f"❌ 投注失败\n\n"
                feedback += f"📝 解析到 {total_bets} 个投注，但全部失败\n\n"
                
                # 显示每个失败投注的具体原因
                feedback += f"🔍 失败原因:\n"
                for failed_bet in failed_bets:
                    bet = failed_bet["bet"]
                    reason = failed_bet["reason"]
                    
                    # 格式化投注信息
                    if bet["type"] == "bet_type":
                        bet_info = f"{bet['bet_type']} {bet['amount']}积分"
                    else:
                        bet_info = f"数字{bet['number']} {bet['amount']}积分"
                    
                    feedback += f"   • {bet_info}: {reason}\n"
                
                feedback += f"\n💡 请检查投注格式和余额"
                
            elif success_count == total_bets:
                feedback = f"✅ 投注成功\n\n"
                feedback += f"📝 成功投注 {success_count} 个\n"
                feedback += f"💰 投注详情:\n"
                for bet in bets:
                    if bet["type"] == "bet_type":
                        feedback += f"   • {bet['bet_type']}: {bet['amount']}积分\n"
                    else:
                        feedback += f"   • 数字{bet['number']}: {bet['amount']}积分\n"
            else:
                feedback = f"⚠️ 部分投注成功\n\n"
                feedback += f"📝 成功: {success_count}/{total_bets}\n"
                
                # 显示成功的投注
                feedback += f"💰 成功投注:\n"
                for bet in bets:
                    # 检查这个投注是否在失败列表中
                    is_failed = any(fb["bet"] == bet for fb in failed_bets)
                    if not is_failed:
                        if bet["type"] == "bet_type":
                            feedback += f"   • {bet['bet_type']}: {bet['amount']}积分\n"
                        else:
                            feedback += f"   • 数字{bet['number']}: {bet['amount']}积分\n"
                
                # 显示失败的投注和原因
                if failed_bets:
                    feedback += f"\n❌ 失败投注:\n"
                    for failed_bet in failed_bets:
                        bet = failed_bet["bet"]
                        reason = failed_bet["reason"]
                        
                        # 格式化投注信息
                        if bet["type"] == "bet_type":
                            bet_info = f"{bet['bet_type']} {bet['amount']}积分"
                        else:
                            bet_info = f"数字{bet['number']} {bet['amount']}积分"
                        
                        feedback += f"   • {bet_info}: {reason}\n"
            
            await message.reply(feedback)
            
        except Exception as e:
            logger.error(f"发送投注反馈失败: {e}")

# 全局投注消息监控器实例
bet_monitor = BetMessageMonitor()

@bet_message_monitor_router.message(
    F.text,
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP})
)
async def monitor_bet_messages(message: Message) -> None:
    """监控投注消息"""
    try:
        content = message.text.strip()
        
        # 跳过空消息
        if not content:
            return
        
        # 检查是否包含投注相关关键词
        bet_keywords = ['大', '小', '单', '双', '豹子', '数字', '押', '下', '注', '买']
        has_bet_keyword = any(keyword in content for keyword in bet_keywords)
        
        # 检查是否包含数字
        has_number = bool(re.search(r'\d+', content))
        
        # 如果包含投注关键词和数字，则处理为投注消息
        if has_bet_keyword and has_number:
            await bet_monitor.process_bet_message(message, content)
        
    except Exception as e:
        logger.error(f"监控投注消息时出错: {e}")

def get_bet_message_stats() -> Dict[str, Any]:
    """获取投注消息统计信息"""
    stats = bet_message_stats.copy()
    
    # 计算成功率
    if stats["total_bet_messages"] > 0:
        stats["success_rate"] = stats["successful_bets"] / stats["total_bet_messages"]
    else:
        stats["success_rate"] = 0
    
    # 计算运行时间
    stats["uptime_seconds"] = (datetime.now() - stats["start_time"]).total_seconds()
    
    return stats

def format_bet_message_stats() -> str:
    """格式化投注消息统计信息"""
    stats = get_bet_message_stats()
    
    # 格式化运行时间
    uptime_seconds = stats["uptime_seconds"]
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_str = f"{hours}小时{minutes}分钟{seconds}秒"
    
    message = f"🎲 **投注消息监控统计**\n\n"
    message += f"⏱️ **运行时间:** {uptime_str}\n"
    message += f"📈 **总投注消息:** {stats['total_bet_messages']}\n"
    message += f"✅ **成功投注:** {stats['successful_bets']}\n"
    message += f"❌ **失败投注:** {stats['failed_bets']}\n"
    message += f"📊 **成功率:** {stats['success_rate']:.2%}\n\n"
    
    if stats["bet_errors"]:
        message += f"🔍 **错误类型统计:**\n"
        for error_type, count in stats["bet_errors"].items():
            message += f"• {error_type}: {count}次\n"
    
    return message

# 添加统计命令
@bet_message_monitor_router.message(Command("bet_stats"))
async def show_bet_stats_command(message: Message) -> None:
    """显示投注消息统计信息"""
    try:
        # 检查权限（仅管理员）
        from bot.config import get_config
        config = get_config()
        
        if message.from_user.id not in config.ADMIN_IDS:
            await message.reply("❌ 此命令仅限管理员使用")
            return
        
        stats_message = format_bet_message_stats()
        await message.reply(stats_message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"显示投注消息统计信息失败: {e}")
        await message.reply("❌ 获取统计信息失败")

@bet_message_monitor_router.message(Command("bet_help"))
async def show_bet_help_command(message: Message) -> None:
    """显示投注帮助信息"""
    help_text = """
🎲 **投注格式说明**

📊 **投注类型与赔率:**
🔸 **大小单双投注:**
   【小】 1、2、3、4  赔率：2.36倍 
   【大】 6、7、8、9  赔率：2.36倍 
   【单】 1、3、7、9  赔率：2.36倍 
   【双】 2、4、6、8  赔率：2.36倍 

🔸 **组合投注:**
   【小单】 1、3   赔率：4.60倍 
   【小双】 2、4   赔率：4.60倍 
   【大单】 7、9   赔率：4.60倍 
   【大双】 6、8   赔率：4.60倍
   【豹子】 0、5  赔率：4.60倍

🔸 **数字投注:**
   【投注数字】 0-9任意数字  赔率：9倍

📝 **支持格式:**
• 大1000          (大小单双 + 积分)
• 小单100         (组合投注 + 积分)
• 数字8 押100     (数字 + 积分)
• 1000大          (积分 + 投注类型)
• 1008            (积分 + 数字)

💰 **投注积分:**
• 最小投注: 1积分
• 最大投注: 根据群组配置

💡 **示例:**
```
大1000 小单100 数字8 押100
小500 单200 豹子50
1000大 500单 1008
```

⚠️ **注意事项:**
• 投注前请确保积分余额充足
• 投注后不可撤销
• 请合理投注，理性游戏
"""
    
    await message.reply(help_text, parse_mode="Markdown") 