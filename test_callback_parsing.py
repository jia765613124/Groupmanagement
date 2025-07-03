#!/usr/bin/env python3
"""测试回调数据解析逻辑"""

def test_callback_parsing():
    """测试不同的回调数据格式"""
    
    test_cases = [
        "lottery_bet_type_-1002882701368_大",
        "lottery_bet_amount_-1002882701368_大_100",
        "lottery_menu_-1002882701368",
        "lottery_bet_-1002882701368"
    ]
    
    for data in test_cases:
        print(f"\n测试回调数据: {data}")
        
        parts = data.split("_")
        if len(parts) < 3:
            print(f"  ❌ 格式错误: 长度不足")
            continue
        
        action = parts[1]
        
        try:
            # 根据不同的action类型解析group_id
            if action == "bet" and len(parts) >= 4:
                # 格式: lottery_bet_type_{group_id}_{bet_type} 或 lottery_bet_amount_{group_id}_{bet_type}_{amount}
                sub_action = parts[2]  # 'type' 或 'amount'
                group_id = int(parts[3])
                
                if sub_action == "type":
                    # 格式: lottery_bet_type_{group_id}_{bet_type}
                    if len(parts) >= 5:
                        bet_type = parts[4]
                        print(f"  ✅ 投注类型回调: action={action}, sub_action={sub_action}, group_id={group_id}, bet_type={bet_type}")
                    else:
                        print(f"  ❌ 投注类型回调数据格式错误")
                elif sub_action == "amount":
                    # 格式: lottery_bet_amount_{group_id}_{bet_type}_{amount}
                    if len(parts) >= 7:
                        bet_type = parts[4]
                        bet_amount = int(parts[5])
                        print(f"  ✅ 投注金额回调: action={action}, sub_action={sub_action}, group_id={group_id}, bet_type={bet_type}, amount={bet_amount}")
                    else:
                        print(f"  ❌ 投注金额回调数据格式错误")
                else:
                    print(f"  ❌ 未知的投注子操作: {sub_action}")
            else:
                # 格式: lottery_{action}_{group_id}_...
                group_id = int(parts[2])
                print(f"  ✅ 普通回调: action={action}, group_id={group_id}")
                
        except ValueError as e:
            print(f"  ❌ 解析错误: {e}")
        except Exception as e:
            print(f"  ❌ 其他错误: {e}")

if __name__ == "__main__":
    test_callback_parsing() 