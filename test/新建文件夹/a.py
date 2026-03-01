import imaplib
import email
from email.header import decode_header

# 登录信息
IMAP_SERVER = "outlook.office365.com"  # Office365/Outlook.imap服务器
EMAIL = "liuSundong1980@outlook.com"
PASSWORD = "LPX20060125o"  # 演示用，实际建议用专用应用密码或OAuth授权

# 连接登录
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(EMAIL, PASSWORD)

# 选择收件箱
mail.select("INBOX")

# 搜索所有邮件
typ, data = mail.search(None, "ALL")

mail_ids = data[0].split()
for num in mail_ids[-5:]:  # 取最近5封
    typ, msg_data = mail.fetch(num, "(RFC822)")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            # 主题解析
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
            print("主题：", subject)
            print("发件人：", msg.get("From"))
            # 内容正文
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True)
                        print("正文：", body.decode("utf-8", errors="ignore"))
                        break
            else:
                body = msg.get_payload(decode=True)
                print("正文：", body.decode("utf-8", errors="ignore"))
            print("=" * 30)

mail.logout()