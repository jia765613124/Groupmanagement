# 文字消息监控功能

## 概述

文字消息监控功能专门监控群组中的文字消息，提供关键词检测、敏感词过滤、消息分析等功能。该功能可以帮助管理员更好地管理和分析群组中的文字内容。

## 功能特性

### 1. 文字消息监控
- **实时监控**: 监控群组中所有文字消息
- **内容分析**: 分析消息内容、长度、关键词等
- **统计功能**: 提供详细的文字消息统计信息

### 2. 关键词检测
- **预设关键词**: 包含常用关键词列表
- **动态添加**: 支持运行时添加新关键词
- **统计功能**: 统计关键词使用频率

### 3. 敏感词过滤
- **预设敏感词**: 包含常见敏感词列表
- **动态管理**: 支持添加/移除敏感词
- **自动检测**: 实时检测敏感词并记录

### 4. 消息分析
- **长度分析**: 统计消息长度分布
- **链接检测**: 自动检测消息中的链接
- **表情符号检测**: 识别消息中的表情符号
- **数字检测**: 提取消息中的数字
- **英文单词检测**: 识别英文单词

## 管理命令

### `/text_stats` - 显示文字消息统计
显示文字消息的详细统计信息，包括：
- 总文字消息数
- 活跃群组和用户数
- 最常用关键词
- 运行时间

**权限**: 仅管理员可用

### `/add_keyword 关键词` - 添加关键词
添加新的关键词到监控列表。

**格式**: `/add_keyword 关键词`
**权限**: 仅管理员可用

**示例**:
```
/add_keyword 重要通知
/add_keyword 紧急
```

### `/add_sensitive 敏感词` - 添加敏感词
添加新的敏感词到过滤列表。

**格式**: `/add_sensitive 敏感词`
**权限**: 仅管理员可用

**示例**:
```
/add_sensitive 垃圾广告
/add_sensitive 诈骗
```

## 技术实现

### 文件结构
```
bot/handlers/text_message_monitor.py  # 主要监控处理器
```

### 核心组件

#### TextMessageMonitor 类
负责文字消息监控和分析的主要类。

#### 主要方法
- `log_text_message()`: 记录和分析文字消息
- `detect_keywords()`: 检测关键词
- `detect_sensitive_words()`: 检测敏感词
- `add_keyword()`: 添加关键词
- `add_sensitive_word()`: 添加敏感词

### 预设关键词列表
```python
keywords = [
    "你好", "大家好", "谢谢", "再见", "欢迎",
    "问题", "帮助", "支持", "信息", "通知",
    "重要", "紧急", "注意", "提醒", "更新"
]
```

### 预设敏感词列表
```python
sensitive_words = [
    "垃圾", "广告", "诈骗", "色情", "暴力",
    "政治", "敏感", "违法", "违规", "不当"
]
```

## 消息处理逻辑

### 1. 敏感词处理
当检测到敏感词时：
- 记录警告日志
- 统计敏感词使用次数
- 可以扩展为自动删除或警告

### 2. 关键词响应
当检测到关键词时：
- 记录信息日志
- 统计关键词使用频率
- 可以扩展为自动回复

### 3. 长消息处理
当消息长度超过500字符时：
- 记录长消息日志
- 可以添加特殊处理逻辑

### 4. 链接检测
当检测到链接时：
- 记录链接日志
- 可以添加链接验证或过滤

### 5. 表情符号检测
使用正则表达式检测表情符号：
- 支持Unicode表情符号
- 记录表情符号使用情况

### 6. 数字检测
提取消息中的数字：
- 使用正则表达式 `\d+`
- 记录数字使用情况

### 7. 英文单词检测
识别英文单词：
- 使用正则表达式 `\b[a-zA-Z]+\b`
- 记录英文单词使用情况

## 自定义处理逻辑

您可以在 `process_text_message()` 函数中添加自定义的处理逻辑：

```python
async def process_text_message(message: Message, content: str, analysis_result: Dict[str, Any]):
    """处理文字消息"""
    
    # 1. 敏感词处理
    if analysis_result["sensitive_words"]:
        # 添加您的敏感词处理逻辑
        await handle_sensitive_words(message, analysis_result["sensitive_words"])
    
    # 2. 关键词响应
    if analysis_result["keywords"]:
        # 添加您的关键词响应逻辑
        await handle_keywords(message, analysis_result["keywords"])
    
    # 3. 长消息处理
    if analysis_result["message_length"] > 500:
        # 添加您的长消息处理逻辑
        await handle_long_message(message, content)
    
    # 4. 链接处理
    if "http" in content or "www." in content:
        # 添加您的链接处理逻辑
        await handle_links(message, content)
    
    # 5. 添加更多自定义处理逻辑
    # ...
```

## 统计信息

### 数据结构
```python
text_message_stats = {
    "total_text_messages": 0,        # 总文字消息数
    "group_text_messages": {},       # 按群组统计
    "user_text_messages": {},        # 按用户统计
    "keyword_stats": {},             # 关键词统计
    "message_length_stats": {},      # 消息长度统计
    "start_time": datetime.now()     # 开始时间
}
```

### 群组统计
每个群组包含：
- `total`: 总消息数
- `users`: 活跃用户集合
- `keywords`: 关键词使用统计
- `sensitive_count`: 敏感词计数
- `last_message`: 最后消息时间

### 用户统计
每个用户包含：
- `total`: 总消息数
- `groups`: 活跃群组集合
- `keywords`: 关键词使用统计
- `sensitive_count`: 敏感词计数
- `last_message`: 最后消息时间

## 使用示例

### 1. 启动监控
文字消息监控会在机器人启动时自动启用。

### 2. 查看统计
发送 `/text_stats` 命令查看文字消息统计。

### 3. 添加关键词
发送 `/add_keyword 重要通知` 添加新关键词。

### 4. 添加敏感词
发送 `/add_sensitive 垃圾广告` 添加新敏感词。

## 日志记录

监控功能会记录详细的日志信息：
```
文字消息 | 用户: 用户名 (ID: 用户ID) | 群组: 群组名 (ID: 群组ID) | 长度: 消息长度 | 内容: 消息内容 | 关键词: 检测到的关键词 | 敏感词: 检测到的敏感词
```

## 扩展功能建议

1. **自动回复**: 基于关键词的自动回复功能
2. **消息过滤**: 自动删除包含敏感词的消息
3. **用户警告**: 对使用敏感词的用户发送警告
4. **内容审核**: 更复杂的内容审核算法
5. **情感分析**: 分析消息的情感倾向
6. **语言检测**: 检测消息的语言类型
7. **垃圾消息检测**: 基于模式的垃圾消息识别
8. **用户行为分析**: 分析用户的发消息模式

## 注意事项

1. **性能考虑**: 关键词检测使用简单的字符串匹配，大量关键词可能影响性能
2. **隐私保护**: 只记录消息摘要，不存储完整内容
3. **误报处理**: 关键词和敏感词检测可能存在误报，需要人工审核
4. **内存使用**: 统计数据存储在内存中，长时间运行需要定期清理
5. **权限控制**: 所有管理命令仅限管理员使用

## 故障排除

### 常见问题

1. **命令无响应**
   - 检查机器人权限
   - 确认命令格式正确

2. **关键词检测不准确**
   - 检查关键词是否包含在预设列表中
   - 确认关键词格式正确

3. **统计数据显示异常**
   - 尝试重启机器人
   - 检查日志文件

### 调试方法

1. 查看日志文件 `logs/bot.log`
2. 使用 `/text_stats` 命令检查统计信息
3. 测试关键词和敏感词添加功能 