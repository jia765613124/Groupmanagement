import logging
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from bot.misc import bot

logger = logging.getLogger(__name__)
commands_router = Router()

# 基本命令（所有用户可见）
BASIC_COMMANDS = [
    BotCommand(command="start", description="开始使用"),
    BotCommand(command="help", description="获取帮助信息"),
    BotCommand(command="fish", description="🎣 钓鱼游戏"),
    BotCommand(command="bets", description="🎲 查看投注记录"),
]

# 管理员命令（仅管理员可见）
ADMIN_COMMANDS = [
    BotCommand(command="draws", description="📊 查看开奖记录"),
]

async def setup_bot_commands():
    """
    设置机器人命令菜单（清理所有作用域并重新设置基本命令）
    """
    try:
        # 先删除所有作用域的命令
        scopes = [
            BotCommandScopeDefault(),
            BotCommandScopeAllPrivateChats(),
            BotCommandScopeAllGroupChats(),
        ]
        for scope in scopes:
            await bot.delete_my_commands(scope=scope)
            logger.info(f"✅ 已清理作用域命令: {scope.type}")

        # 设置基本命令（所有用户可见）
        await bot.set_my_commands(
            commands=BASIC_COMMANDS,
            scope=BotCommandScopeDefault()
        )
        logger.info("✅ 成功设置基本命令：%s", [cmd.command for cmd in BASIC_COMMANDS])

        # 设置管理员命令（仅管理员可见）
        # 注意：Telegram Bot API 不支持按用户角色设置命令，这里只是记录
        logger.info("✅ 管理员命令：%s", [cmd.command for cmd in ADMIN_COMMANDS])

    except Exception as e:
        logger.error("❌ 设置机器人命令失败: %s", e, exc_info=True)
        raise

@commands_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    处理 /start 命令
    """
    logger.info(f"用户 {message.from_user.id} 发送了 /start 命令")
    
    # 创建内联键盘
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎣 钓鱼游戏",
                    callback_data="fishing_menu"
                ),
                InlineKeyboardButton(
                    text="📚 查看帮助",
                    callback_data="show_help"
                )
            ]
        ]
    )
    
    await message.answer(
        "👋 欢迎使用群管理机器人！\n\n"
        "🤖 我是一个功能强大的群管理助手，可以帮助你管理群组。\n\n"
        "📚 主要功能：\n"
        "• 用户管理：封禁、解封、禁言、踢出\n"
        "• 消息管理：置顶、删除\n"
        "• 警告系统：警告、撤销警告\n"
        "• 群组设置：权限、规则等\n"
        "• 🎣 钓鱼游戏：娱乐功能\n\n"
        "点击下方按钮开始使用：",
        reply_markup=keyboard
    )

@commands_router.message(Command("fish"))
async def fish_command_handler(message: Message) -> None:
    """
    处理 /fish 命令 - 直接进入钓鱼菜单
    """
    logger.info(f"用户 {message.from_user.id} 发送了 /fish 命令")
    
    # 创建钓鱼菜单键盘
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎣 开始钓鱼",
                    callback_data="fishing_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 钓鱼记录",
                    callback_data="fishing_history"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 返回主菜单",
                    callback_data="back_to_main"
                )
            ]
        ]
    )
    
    await message.answer(
        "🎣 欢迎来到钓鱼游戏！\n\n"
        "🎮 游戏规则：\n"
        "• 使用不同等级的鱼竿钓鱼\n"
        "• 每次钓鱼消耗相应积分\n"
        "• 钓到的鱼可以获得积分奖励\n"
        "• 稀有鱼类有更高奖励\n\n"
        "选择你的操作：",
        reply_markup=keyboard
    )

@commands_router.callback_query(lambda c: c.data == "fishing_menu")
async def fishing_menu_callback(callback_query: CallbackQuery):
    """
    处理钓鱼菜单回调
    """
    try:
        # 这里会调用钓鱼处理器来处理具体的钓鱼逻辑
        # 由于钓鱼逻辑在 fishing_handler.py 中，我们需要导入并调用
        from bot.handlers.fishing_handler import show_fishing_rods
        
        await show_fishing_rods(callback_query.message, callback_query.from_user.id)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"处理钓鱼菜单回调失败: {e}")
        await callback_query.answer("❌ 操作失败，请重试！")

@commands_router.callback_query(lambda c: c.data == "fishing_history")
async def fishing_history_callback(callback_query: CallbackQuery):
    """
    处理钓鱼记录回调
    """
    try:
        # 调用钓鱼处理器中的历史记录功能
        from bot.handlers.fishing_handler import show_fishing_history
        
        await show_fishing_history(callback_query.message, callback_query.from_user.id)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"处理钓鱼记录回调失败: {e}")
        await callback_query.answer("❌ 操作失败，请重试！")

@commands_router.callback_query(lambda c: c.data == "show_help")
async def show_help_callback(callback_query: CallbackQuery):
    """
    处理显示帮助信息的回调
    """
    try:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎣 钓鱼游戏",
                        callback_data="fishing_menu"
                    ),
                    InlineKeyboardButton(
                        text="🔙 返回主菜单",
                        callback_data="back_to_main"
                    )
                ]
            ]
        )
        
        await callback_query.message.edit_text(
            "📚 群管理机器人使用说明：\n\n"
            "👥 用户管理命令：\n"
            "• /ban - 封禁用户\n"
            "• /unban - 解封用户\n"
            "• /mute - 禁言用户\n"
            "• /unmute - 解除禁言\n"
            "• /kick - 踢出用户\n"
            "• /warn - 警告用户\n"
            "• /unwarn - 撤销警告\n\n"
            "📌 消息管理命令：\n"
            "• /pin - 置顶消息\n"
            "• /unpin - 取消置顶\n\n"
            "🎣 娱乐功能：\n"
            "• /fish - 钓鱼游戏\n\n"
            "⚙️ 设置命令：\n"
            "• /settings - 群组设置\n\n"
            "💡 使用说明：\n"
            "1. 回复用户消息或使用用户ID\n"
            "2. 可以添加时间参数，如：/mute 1h\n"
            "3. 可以添加原因，如：/ban 原因：违规\n"
            "4. 钓鱼游戏需要消耗积分",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"处理显示帮助信息回调失败: {e}")
        await callback_query.answer("❌ 操作失败，请重试！")

@commands_router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_callback(callback_query: CallbackQuery):
    """
    处理返回主菜单的回调
    """
    try:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎣 钓鱼游戏",
                        callback_data="fishing_menu"
                    ),
                    InlineKeyboardButton(
                        text="📚 查看帮助",
                        callback_data="show_help"
                    )
                ]
            ]
        )
        
        await callback_query.message.edit_text(
            "👋 欢迎使用群管理机器人！\n\n"
            "🤖 我是一个功能强大的群管理助手，可以帮助你管理群组。\n\n"
            "📚 主要功能：\n"
            "• 用户管理：封禁、解封、禁言、踢出\n"
            "• 消息管理：置顶、删除\n"
            "• 警告系统：警告、撤销警告\n"
            "• 群组设置：权限、规则等\n"
            "• 🎣 钓鱼游戏：娱乐功能\n\n"
            "点击下方按钮开始使用：",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"处理返回主菜单回调失败: {e}")
        await callback_query.answer("❌ 操作失败，请重试！")

@commands_router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """
    处理 /help 命令
    """
    logger.info(f"用户 {message.from_user.id} 发送了 /help 命令")
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎣 钓鱼游戏",
                    callback_data="fishing_menu"
                )
            ]
        ]
    )
    
    await message.answer(
        "📚 群管理机器人使用说明：\n\n"
        "👥 用户管理命令：\n"
        "• /ban - 封禁用户\n"
        "• /unban - 解封用户\n"
        "• /mute - 禁言用户\n"
        "• /unmute - 解除禁言\n"
        "• /kick - 踢出用户\n"
        "• /warn - 警告用户\n"
        "• /unwarn - 撤销警告\n\n"
        "📌 消息管理命令：\n"
        "• /pin - 置顶消息\n"
        "• /unpin - 取消置顶\n\n"
        "🎣 娱乐功能：\n"
        "• /fish - 钓鱼游戏\n"
        "• /bets - 查看投注记录\n\n"
        "⚙️ 设置命令：\n"
        "• /settings - 群组设置\n\n"
        "💡 使用说明：\n"
        "1. 回复用户消息或使用用户ID\n"
        "2. 可以添加时间参数，如：/mute 1h\n"
        "3. 可以添加原因，如：/ban 原因：违规\n"
        "4. 钓鱼游戏需要消耗积分",
        reply_markup=keyboard
    )

@commands_router.message(Command("bets"))
async def bets_handler(message: Message) -> None:
    """
    处理 /bets 命令 - 查看投注记录（第一页）
    """
    logger.info(f"用户 {message.from_user.id} 发送了 /bets 命令")
    
    # 调用彩票处理器显示第一页
    from bot.handlers.lottery_handler import show_bets_page
    await show_bets_page(message, message.from_user.id, 1)

@commands_router.message(Command("draws"))
async def draws_handler(message: Message) -> None:
    """
    处理 /draws 命令 - 查看最近开奖记录（仅管理员）
    """
    logger.info(f"用户 {message.from_user.id} 发送了 /draws 命令")
    
    # 检查管理员权限
    from bot.config import get_config
    config = get_config()
    
    if message.from_user.id not in config.ADMIN_IDS:
        await message.reply("❌ 此命令仅限管理员使用")
        return
    
    # 调用彩票处理器显示最近开奖记录
    from bot.handlers.lottery_handler import show_recent_draws
    await show_recent_draws(message, limit=10)

@commands_router.callback_query(lambda c: c.data.startswith("fish_"))
async def fishing_rod_callback(callback_query: CallbackQuery):
    """
    处理钓鱼竿选择回调
    """
    try:
        # 解析钓鱼竿类型
        rod_type = callback_query.data.split('_')[1]
        
        # 调用钓鱼处理器处理钓鱼逻辑
        from bot.handlers.fishing_handler import handle_fishing_callback
        
        await handle_fishing_callback(callback_query, rod_type)
        
    except Exception as e:
        logger.error(f"处理钓鱼竿选择回调失败: {e}")
        await callback_query.answer("❌ 操作失败，请重试！")

@commands_router.callback_query(lambda c: c.data.startswith("fishing_history_page_"))
async def fishing_history_page_callback(callback_query: CallbackQuery):
    """
    处理钓鱼历史分页回调
    """
    try:
        # 解析回调数据：fishing_history_page_{telegram_id}_{page}
        parts = callback_query.data.split('_')
        telegram_id = int(parts[3])
        page = int(parts[4])
        
        # 验证用户权限（只能查看自己的历史）
        if callback_query.from_user.id != telegram_id:
            await callback_query.answer("❌ 无权限查看他人历史记录")
            return
        
        # 调用钓鱼处理器显示指定页面的历史记录
        from bot.handlers.fishing_handler import show_fishing_history
        
        await show_fishing_history(callback_query.message, telegram_id, page)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"处理钓鱼历史分页回调失败: {e}")
        await callback_query.answer("❌ 操作失败，请重试！")

@commands_router.callback_query(lambda c: c.data == "fishing_history_info")
async def fishing_history_info_callback(callback_query: CallbackQuery):
    """
    处理钓鱼历史信息回调（页码信息）
    """
    try:
        await callback_query.answer("📄 当前页面信息")
        
    except Exception as e:
        logger.error(f"处理钓鱼历史信息回调失败: {e}")
        await callback_query.answer("❌ 操作失败，请重试！")

@commands_router.callback_query(lambda c: c.data.startswith("bets_page_"))
async def bets_page_callback(callback_query: CallbackQuery):
    """
    处理投注记录分页回调
    """
    try:
        # 解析回调数据：bets_page_{telegram_id}_{page}
        parts = callback_query.data.split('_')
        telegram_id = int(parts[2])
        page = int(parts[3])
        
        # 验证用户权限（只能查看自己的投注记录）
        if callback_query.from_user.id != telegram_id:
            await callback_query.answer("❌ 无权限查看他人投注记录")
            return
        
        # 调用彩票处理器显示指定页面的投注记录
        from bot.handlers.lottery_handler import show_bets_page
        await show_bets_page(callback_query.message, telegram_id, page)
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"处理投注记录分页回调失败: {e}")
        await callback_query.answer("❌ 操作失败，请重试！")


