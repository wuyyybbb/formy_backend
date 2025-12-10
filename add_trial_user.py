"""
快速添加试用白名单用户

使用方法:
1. 直接运行查看当前白名单: python add_trial_user.py
2. 添加单个用户: python add_trial_user.py newuser@example.com
3. 添加多个用户: python add_trial_user.py user1@test.com user2@test.com
"""
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings


def display_current_whitelist():
    """显示当前白名单配置"""
    print("\n" + "="*60)
    print("当前白名单配置")
    print("="*60)
    
    print("\n🌟 VIP 白名单 (10000 积分):")
    vip_emails = settings.get_vip_whitelist_emails
    if vip_emails:
        for email in sorted(vip_emails):
            print(f"  ✓ {email}")
    else:
        print("  (无)")
    
    print("\n🎁 试用白名单 (1000 积分):")
    trial_emails = settings.get_trial_whitelist_emails
    if trial_emails:
        for email in sorted(trial_emails):
            print(f"  ✓ {email}")
    else:
        print("  (无)")
    
    print("\n👥 普通用户:")
    print("  ✓ 所有其他用户 (100 积分)")
    print("="*60 + "\n")


def validate_email(email: str) -> bool:
    """简单验证邮箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def add_trial_users(new_emails: list):
    """添加试用白名单用户到环境变量配置建议"""
    print("\n" + "="*60)
    print("添加试用白名单用户")
    print("="*60 + "\n")
    
    # 验证邮箱格式
    valid_emails = []
    for email in new_emails:
        email = email.strip().lower()
        if validate_email(email):
            valid_emails.append(email)
            print(f"✓ 有效邮箱: {email}")
        else:
            print(f"✗ 无效邮箱: {email} (已跳过)")
    
    if not valid_emails:
        print("\n❌ 没有有效的邮箱地址")
        return
    
    # 获取当前试用白名单
    current_trial = settings.get_trial_whitelist_emails
    
    # 合并新旧邮箱
    all_trial_emails = current_trial | set(valid_emails)
    
    # 生成新的环境变量值
    new_trial_value = ",".join(sorted(all_trial_emails))
    
    print("\n" + "="*60)
    print("📋 更新后的配置")
    print("="*60 + "\n")
    
    print("请在 Render Dashboard 中设置以下环境变量:\n")
    print(f"TRIAL_WHITELIST_EMAILS={new_trial_value}\n")
    
    print("或者在本地 .env 文件中添加:\n")
    print(f"TRIAL_WHITELIST_EMAILS={new_trial_value}\n")
    
    print("="*60)
    print("新增的试用用户:")
    print("="*60 + "\n")
    
    for email in valid_emails:
        if email not in current_trial:
            print(f"  🎁 {email}")
    
    print("\n" + "="*60)
    print("✅ 配置已生成，请在 Render Dashboard 中更新环境变量")
    print("="*60 + "\n")


def main():
    """主函数"""
    # 显示当前配置
    display_current_whitelist()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        new_emails = sys.argv[1:]
        add_trial_users(new_emails)
    else:
        print("💡 提示: 使用 'python add_trial_user.py 邮箱@example.com' 添加试用用户\n")


if __name__ == "__main__":
    main()
