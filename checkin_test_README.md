# 连续签到奖励测试工具

本目录包含用于测试连续签到奖励系统的工具脚本。

## 1. 测试数据生成工具 (test_sign_in_data.py)

该工具用于批量生成测试数据，创建多个测试用户并为其生成不同天数的连续签到记录。

### 测试用户列表

| 用户ID | 名称 | 连续签到天数 | 触发奖励 |
|-------|-----|------------|--------|
| 10000001 | 测试用户1 | 2天 | 无特殊奖励 |
| 10000002 | 测试用户2 | 3天 | 3天奖励(+200积分) |
| 10000003 | 测试用户3 | 7天 | 7天奖励(+500积分) |
| 10000004 | 测试用户4 | 14天 | 14天奖励(+1000积分) |
| 10000005 | 测试用户5 | 21天 | 21天奖励(+1500积分) |
| 10000006 | 测试用户6 | 30天 | 1个月奖励(+2000积分) |
| 10000007 | 测试用户7 | 60天 | 2个月奖励(+5000积分) |
| 10000008 | 测试用户8 | 90天 | 3个月奖励(+8000积分) |
| 10000009 | 测试用户9 | 179天 | 即将达到半年(无特殊奖励) |
| 10000010 | 测试用户10 | 180天 | 半年奖励(+20000积分) |
| 10000011 | 测试用户11 | 364天 | 即将达到一年(无特殊奖励) |
| 10000012 | 测试用户12 | 365天 | 一年奖励(+50000积分) |

### 使用方法

1. 执行脚本生成测试数据:
```bash
python test_sign_in_data.py
```

2. 在机器人测试环境中，使用这些用户ID登录并发送"签到"命令

## 2. 签到测试工具 (test_checkin.py)

该工具可以模拟特定用户进行签到，方便测试连续签到奖励机制。

### 使用方法

1. 运行签到测试工具:
```bash
python test_checkin.py
```

2. 按提示输入要测试的用户Telegram ID
3. 工具将模拟用户签到并显示奖励结果

## 3. 数据重置工具 (reset_checkin_data.py)

用于清除签到数据，方便重新测试。

### 功能选项

- **重置特定用户的签到数据**: 删除指定用户的所有签到记录和交易记录
- **重置特定用户的签到数据并重置积分**: 删除记录并将积分重置为初始值
- **重置所有用户的签到数据**: 清除所有用户的签到相关数据（慎用）

### 使用方法

```bash
python reset_checkin_data.py
```

按照菜单提示进行操作。

## 测试流程示例

以下是一个完整的测试流程示例:

1. 生成测试数据:
```bash
python test_sign_in_data.py
```

2. 在Telegram中使用测试用户ID登录，然后发送"签到"命令测试奖励

3. 或者使用签到测试工具模拟签到:
```bash
python test_checkin.py
```
输入要测试的用户ID (例如 10000002) 进行测试

4. 需要重新测试时，重置数据:
```bash
python reset_checkin_data.py
```
选择相应的重置选项

## 注意事项

1. 这些脚本直接操作数据库，请勿在生产环境中使用
2. 测试前建议备份数据库
3. 重置功能会删除数据，请谨慎使用 