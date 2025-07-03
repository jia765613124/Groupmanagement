# 获取Telegram群组ID和名称

## 方法1：使用命令行脚本（推荐）

### 1. 设置环境变量

```bash
export TELEGRAM_API_ID="你的API_ID"
export TELEGRAM_API_HASH="你的API_HASH"
export TELEGRAM_BOT_TOKEN="你的BOT_TOKEN"
```

### 2. 运行脚本

```bash
# 获取所有群组信息
python get_group_info.py

# 获取特定群组信息
python get_group_info.py -1001234567890
```

### 3. 输出示例

```
✅ 已连接到Telegram

📋 正在获取群组列表...

🎯 **群组列表** (共 3 个)
==================================================
1. 开奖群组1
   ID: -1001234567890
   用户名: @lottery_group1
   成员数: 1,234

2. 测试群组
   ID: -1001234567891
   成员数: 567

3. 官方群组
   ID: -1001234567892
   用户名: @official_group
   成员数: 2,345

🔧 **配置代码**
==================================================
在 multi_game_config.py 中添加群组配置：

GroupConfig(
    group_id=-1001234567890,
    group_name="开奖群组1",
    game_type="lottery",
    enabled=True,
    admin_only=False,
    min_bet=1,
    max_bet=100000,
    auto_draw=True,
    notification_groups=[-1001234567890]
),

GroupConfig(
    group_id=-1001234567891,
    group_name="测试群组",
    game_type="lottery",
    enabled=True,
    admin_only=False,
    min_bet=1,
    max_bet=100000,
    auto_draw=True,
    notification_groups=[-1001234567891]
),
```

## 方法2：在机器人中使用命令

### 1. 机器人命令

在群组中发送以下命令：

- `/groupid` - 获取当前群组ID和配置示例
- `/groupinfo` - 获取当前群组详细信息（仅管理员）
- `/mygroups` - 获取机器人所在的所有群组（仅管理员）
- `/searchgroup 关键词` - 搜索包含关键词的群组（仅管理员）

### 2. 命令示例

```
/groupid

📋 **当前群组信息**

🆔 **群组ID:** `-1001234567890`
📝 **群组名称:** 开奖群组1
🔗 **用户名:** @lottery_group1
📊 **类型:** group

🔧 **配置示例:**
```python
GroupConfig(
    group_id=-1001234567890,
    group_name="开奖群组1",
    game_type="lottery",
    enabled=True,
    admin_only=False,
    min_bet=1,
    max_bet=100000,
    auto_draw=True,
    notification_groups=[-1001234567890]
),
```
```

## 方法3：使用代码获取

### 1. 在代码中使用

```python
from bot.utils.group_info import get_chat_info, get_my_groups

# 获取特定群组信息
group_info = await get_chat_info(client, -1001234567890)
if group_info:
    print(f"群组ID: {group_info['id']}")
    print(f"群组名称: {group_info['title']}")
    print(f"用户名: @{group_info['username']}")

# 获取所有群组
groups = await get_my_groups(client)
for group in groups:
    print(f"{group['title']}: {group['id']}")
```

### 2. 使用GroupInfoHelper类

```python
from bot.utils.group_info import GroupInfoHelper

helper = GroupInfoHelper(client)

# 获取群组信息
group_info = await helper.get_chat_info(-1001234567890)

# 格式化显示
message = helper.format_group_info(group_info)
print(message)

# 获取群组列表
groups = await helper.get_my_groups()
message = helper.format_group_list(groups)
print(message)
```

## 方法4：手动获取群组ID

### 1. 通过转发消息

1. 在群组中发送一条消息
2. 将消息转发给 @userinfobot
3. 机器人会返回群组信息，包括群组ID

### 2. 通过网页版Telegram

1. 打开 [web.telegram.org](https://web.telegram.org)
2. 进入群组
3. 查看URL中的群组ID

### 3. 通过第三方机器人

- @getidsbot - 获取各种ID
- @userinfobot - 获取用户和群组信息
- @RawDataBot - 获取原始数据

## 群组ID说明

### 1. 群组ID格式

- **普通群组**: `-100xxxxxxxxxx` (12位数字)
- **超级群组**: `-100xxxxxxxxxx` (12位数字)
- **频道**: `-100xxxxxxxxxx` (12位数字)

### 2. 注意事项

- 群组ID是负数
- 必须以 `-100` 开头
- 总长度为13位（包括负号）

## 配置群组

### 1. 在 multi_game_config.py 中添加群组

```python
# 在 _init_default_groups 方法中添加
GroupConfig(
    group_id=-1001234567890,  # 从上面获取的群组ID
    group_name="开奖群组1",    # 群组名称
    game_type="lottery",      # 游戏类型
    enabled=True,             # 是否启用
    admin_only=False,         # 是否仅管理员可操作
    min_bet=1,               # 最小投注金额
    max_bet=100000,          # 最大投注金额
    auto_draw=True,          # 是否自动开奖
    notification_groups=[-1001234567890]  # 通知群组列表
),
```

### 2. 环境变量配置

```bash
# 设置管理员ID（用于机器人命令权限）
export TELEGRAM_ADMIN_IDS="123456789,987654321"

# 设置通知群组
export LOTTERY_NOTIFICATION_GROUPS="-1001234567890,-1001234567891"
```

## 常见问题

### 1. 无法获取群组信息

**可能原因：**
- 机器人不在群组中
- 群组已删除或机器人被踢出
- API凭据错误

**解决方法：**
- 确保机器人已加入群组
- 检查API凭据是否正确
- 确认群组仍然存在

### 2. 群组ID不正确

**可能原因：**
- 复制了错误的ID
- 群组类型不是群组而是频道

**解决方法：**
- 使用 `/groupid` 命令重新获取
- 确认群组类型

### 3. 权限不足

**可能原因：**
- 不是群组管理员
- 机器人权限不足

**解决方法：**
- 联系群组管理员
- 确保机器人有必要的权限

## 总结

推荐使用 **方法1（命令行脚本）** 来获取群组信息，因为它：

1. **简单易用** - 一条命令即可获取所有信息
2. **信息完整** - 包含群组ID、名称、用户名、成员数等
3. **自动生成配置** - 直接生成可用的配置代码
4. **批量处理** - 可以一次性获取所有群组信息

获取群组信息后，记得在 `multi_game_config.py` 中正确配置群组，然后重启机器人即可使用多群组开奖功能。 