import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class NotificationService:
    def __init__(self, db):
        self.db = db
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self._loop, daemon=True).start()
            print("🔔 Bildirim Servisi Başlatıldı (Arka Plan)")

    def _loop(self):
        while self.is_running:
            try:
                self.check_and_send()
                # 30 saniyede bir kontrol (Test için)
                time.sleep(30) 
            except Exception as e:
                print(f"⚠️ Bildirim Servisi Hatası: {e}")
                time.sleep(30)

    def check_and_send(self):
        try: settings = self.db.get_notification_settings()
        except: return
        if not settings: return
        active_channels = {row[0]: row for row in settings if row[4]} 
        if not active_channels: return

        try: pending = self.db.get_pending_reminders()
        except: pending = []

        for app in pending:
            app_id, p_name, p_phone, p_email, app_date = app
            
            date_str = app_date.strftime("%d.%m.%Y")
            time_str = app_date.strftime("%H:%M")

            # --- SMS ---
            if "sms" in active_channels:
                cfg = active_channels["sms"]
                msg = cfg[5].replace("{hasta}", str(p_name)).replace("{tarih}", str(date_str)).replace("{saat}", str(time_str))
                if self.simulate_sms(p_phone, msg):
                    self.db.mark_reminder_sent(app_id)

            # --- EMAIL ---
            if "email" in active_channels:
                cfg = active_channels["email"]
                my_email = cfg[1] # Gönderici Mail
                my_pass = cfg[2]  # Uygulama Şifresi
                title = cfg[3]
                template = cfg[5]
                body = template.replace("{hasta}", str(p_name)).replace("{tarih}", str(date_str)).replace("{saat}", str(time_str))
                
                # Hastanın maili varsa gönder
                if p_email and "@" in p_email:
                    if self.send_smart_email(my_email, my_pass, title, p_email, body):
                        self.db.mark_reminder_sent(app_id)
                        try: self.db.log_action("Sistem", "Email Gönderimi", f"{p_name} ({p_email}) adresine mail atıldı.")
                        except: pass
                else:
                    # Mail yoksa atla ama log düşme (çok kirlilik olmasın)
                    pass

    def simulate_sms(self, phone, message):
        print(f"📨 [SMS SİMÜLASYONU] -> {phone} : {message}")
        return True

    def send_smart_email(self, sender_mail, sender_pass, subject, receiver_mail, body):
        """
        Gönderici mail adresinin uzantısına göre SMTP sunucusunu otomatik seçer.
        """
        try:
            smtp_server = "smtp.gmail.com" # Varsayılan
            smtp_port = 587

            # --- OTOMATİK ALGILAMA ---
            domain = sender_mail.split("@")[-1].lower()

            if "gmail.com" in domain:
                smtp_server = "smtp.gmail.com"
            elif "icloud.com" in domain or "me.com" in domain or "mac.com" in domain:
                smtp_server = "smtp.mail.me.com"
            elif "outlook.com" in domain or "hotmail.com" in domain or "live.com" in domain:
                smtp_server = "smtp.office365.com"
            elif "yahoo.com" in domain:
                smtp_server = "smtp.mail.yahoo.com"
            elif "yandex.com" in domain:
                smtp_server = "smtp.yandex.com"
                smtp_port = 465 # Yandex genelde SSL sever
            else:
                print(f"⚠️ Bilinmeyen mail sağlayıcı: {domain}. Gmail varsayılıyor.")

            # --- GÖNDERİM ---
            msg = MIMEMultipart()
            msg['From'] = sender_mail
            msg['To'] = receiver_mail
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            if smtp_port == 465:
                # SSL Bağlantı (Yandex vb. için)
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                # TLS Bağlantı (Gmail, iCloud, Outlook için)
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            
            server.login(sender_mail, sender_pass)
            server.sendmail(sender_mail, receiver_mail, msg.as_string())
            server.quit()
            
            print(f"📧 [{domain.upper()} SENT] -> {receiver_mail}")
            return True

        except Exception as e:
            print(f"❌ Mail Hatası ({sender_mail}): {e}")
            return False