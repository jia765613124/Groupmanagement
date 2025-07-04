#!/usr/bin/env python3
"""
测试数字投注解析问题
"""

import re

def test_number_bet_parsing():
    """测试数字投注解析"""
    print("🧪 测试数字投注解析")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        "数字8 押100",
        "数字8押100", 
        "8 100",
        "8押100",
        "数字8 100",
        "数字8",
        "8",
    ]
    
    # 当前的正则表达式
    pattern2 = r'^(?:数字)?([0-9零一二三四五六七八九])(?:押|下|注|买)?(\d+)$'
    
    print("📝 当前正则表达式:")
    print(f"pattern2 = {pattern2}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}: '{test_case}'")
        
        # 测试正则匹配
        match = re.match(pattern2, test_case)
        if match:
            print(f"    ✅ 匹配成功")
            print(f"    组1 (数字): '{match.group(1)}'")
            print(f"    组2 (金额): '{match.group(2)}'")
        else:
            print(f"    ❌ 匹配失败")
        
        print()
    
    print("🔧 问题分析:")
    print("对于 '数字8 押100':")
    print("1. 正则表达式期望格式: 数字8押100 (无空格)")
    print("2. 但实际输入: 数字8 押100 (有空格)")
    print("3. 空格导致匹配失败")
    print()
    
    print("💡 解决方案:")
    print("需要修改正则表达式，在'押'字前允许空格")
    print("新正则: r'^(?:数字)?([0-9零一二三四五六七八九])\s*(?:押|下|注|买)?(\d+)$'")
    print()
    
    # 测试修复后的正则表达式
    pattern2_fixed = r'^(?:数字)?([0-9零一二三四五六七八九])\s*(?:押|下|注|买)?(\d+)$'
    
    print("📝 修复后的正则表达式:")
    print(f"pattern2_fixed = {pattern2_fixed}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}: '{test_case}'")
        
        # 测试修复后的正则匹配
        match = re.match(pattern2_fixed, test_case)
        if match:
            print(f"    ✅ 匹配成功")
            print(f"    组1 (数字): '{match.group(1)}'")
            print(f"    组2 (金额): '{match.group(2)}'")
        else:
            print(f"    ❌ 匹配失败")
        
        print()

if __name__ == "__main__":
    test_number_bet_parsing() 