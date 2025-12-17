import uuid
import hashlib
import base64
import datetime
import json

class LicenseManager:
    def __init__(self, db):
        self.db = db
        # BU SENİN GİZLİ ŞİFREN (Bunu kimseyle paylaşma, keygen'de de aynısı olmalı)
        self.SECRET_KEY = "RNDV5_SUPER_GIZLI_ANAHTAR_2025"

    def get_hardware_id(self):
        """Bilgisayarın benzersiz donanım kimliğini (MAC Adresi) alır"""
        node = uuid.getnode()
        # Görünümü güzelleştirelim: 1234-5678-90AB
        h = hashlib.md5(str(node).encode()).hexdigest().upper()
        return f"{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"

    def check_license(self):
        """Lisans geçerli mi kontrol eder"""
        # Veritabanından kayıtlı lisansı çek
        stored_key = self.db.get_setting("license_key")
        if not stored_key:
            return False, "Lisans anahtarı bulunamadı."

        try:
            # 1. Base64 çöz
            decoded = base64.b64decode(stored_key).decode()
            
            # 2. İçeriği ayır (HWID | Bitiş Tarihi | İmza)
            hwid, expiry_str, signature = decoded.split("|")
            
            # 3. HWID Kontrolü (Bu bilgisayar mı?)
            current_hwid = self.get_hardware_id()
            if hwid != current_hwid:
                return False, "Bu lisans başka bir bilgisayara ait!"

            # 4. Tarih Kontrolü (Süresi dolmuş mu?)
            expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d").date()
            if datetime.date.today() > expiry_date:
                return False, f"Lisans süresi doldu! (Bitiş: {expiry_str})"

            # 5. İmza Kontrolü (Müşteri tarihi elle mi değiştirdi?)
            # Bizim hesapladığımız imza ile ondaki tutuyor mu?
            expected_sig = self._generate_signature(hwid, expiry_str)
            if signature != expected_sig:
                return False, "Geçersiz lisans anahtarı (İmza Hatası)!"

            return True, f"Lisans Aktif (Bitiş: {expiry_str})"

        except Exception as e:
            return False, f"Lisans okuma hatası: {e}"

    def activate_license(self, key_input):
        """Yeni girilen anahtarı dener ve kaydeder"""
        # Veritabanına geçici olarak kaydet ve kontrol et
        self.db.set_setting("license_key", key_input)
        is_valid, msg = self.check_license()
        
        if is_valid:
            return True, msg
        else:
            # Geçersizse sil
            self.db.set_setting("license_key", "")
            return False, msg

    def _generate_signature(self, hwid, expiry):
        """Verileri gizli anahtarla karıştırıp imza üretir"""
        data = f"{hwid}{expiry}{self.SECRET_KEY}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()