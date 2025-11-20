"""
Resend 邮件服务
"""
import os
from typing import Optional
import httpx
from app.core.config import settings


class ResendEmailService:
    """Resend 邮件服务类"""
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY", "")
        self.from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
        self.api_url = "https://api.resend.com/emails"
        
        print(f"🔧 邮件服务初始化:")
        print(f"   - API Key: {'已配置' if self.api_key else '❌ 未配置'}")
        print(f"   - From Email: {self.from_email}")
        
        if not self.api_key:
            print("⚠️  警告: RESEND_API_KEY 未设置，邮件功能将无法使用")
            print("⚠️  请在环境变量中设置 RESEND_API_KEY")
    
    async def send_verification_code(self, to_email: str, code: str) -> bool:
        """
        发送验证码邮件
        
        Args:
            to_email: 收件人邮箱
            code: 6位验证码
            
        Returns:
            bool: 是否发送成功
        """
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background-color: #0f172a;
                        color: #e2e8f0;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                        border: 1px solid #334155;
                        border-radius: 8px;
                        padding: 40px;
                    }}
                    .logo {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .logo-box {{
                        display: inline-block;
                        width: 60px;
                        height: 60px;
                        background: linear-gradient(135deg, #00D9FF 0%, #0099cc 100%);
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 32px;
                        font-weight: bold;
                        color: #0f172a;
                    }}
                    .title {{
                        font-size: 24px;
                        font-weight: bold;
                        margin-bottom: 10px;
                        text-align: center;
                    }}
                    .subtitle {{
                        color: #94a3b8;
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .code-box {{
                        background: #1e293b;
                        border: 2px solid #00D9FF;
                        border-radius: 8px;
                        padding: 30px;
                        text-align: center;
                        margin: 30px 0;
                    }}
                    .code {{
                        font-size: 48px;
                        font-weight: bold;
                        letter-spacing: 10px;
                        color: #00D9FF;
                        font-family: 'Courier New', monospace;
                    }}
                    .note {{
                        color: #94a3b8;
                        font-size: 14px;
                        text-align: center;
                        margin-top: 20px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #334155;
                        color: #64748b;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">
                        <div class="logo-box">F</div>
                        <h1 style="margin: 10px 0; font-size: 28px;">Formy｜形我</h1>
                    </div>
                    
                    <div class="title">验证码登录</div>
                    <div class="subtitle">您的登录验证码如下</div>
                    
                    <div class="code-box">
                        <div class="code">{code}</div>
                    </div>
                    
                    <div class="note">
                        ⏱️ 此验证码 <strong>10 分钟</strong> 内有效<br>
                        🔒 请勿将验证码告知他人<br>
                        ⚠️ 如非本人操作，请忽略此邮件
                    </div>
                    
                    <div class="footer">
                        © 2025 Formy｜形我. All rights reserved.<br>
                        AI 视觉创作工具 - 专为服装行业打造
                    </div>
                </div>
            </body>
            </html>
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": f"Formy <{self.from_email}>",
                        "to": [to_email],
                        "subject": f"【Formy】您的验证码是 {code}",
                        "html": html_content,
                    },
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    print(f"✅ 验证码邮件已发送到: {to_email}")
                    return True
                else:
                    print(f"❌ 发送失败: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 发送邮件异常: {e}")
            return False


# 全局邮件服务实例
_email_service: Optional[ResendEmailService] = None


def get_email_service() -> ResendEmailService:
    """获取邮件服务实例（单例）"""
    global _email_service
    if _email_service is None:
        _email_service = ResendEmailService()
    return _email_service

