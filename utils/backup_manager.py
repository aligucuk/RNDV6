import os
import subprocess
import datetime
import zipfile
import threading

class BackupManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_backup_path(self):
        """Ayarlardan yedekleme yolunu getirir"""
        path = self.db.get_setting("backup_path")
        return path if path and os.path.exists(path) else None

    def create_backup(self):
        """Yedeklemeyi başlatır"""
        folder = self.get_backup_path()
        if not folder:
            print("Yedekleme klasörü ayarlanmamış!")
            return False, "Klasör Yok"

        try:
            # Dosya İsimleri
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            sql_file = os.path.join(folder, f"backup_{timestamp}.sql")
            zip_file = os.path.join(folder, f"RNDV4_Yedek_{timestamp}.zip")

            # 1. pg_dump ile SQL oluştur (PostgreSQL kurulu olmalı)
            # PGPASSWORD environment variable ile şifre geçiyoruz
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db.DB_PASS
            
            # Komut: pg_dump -h localhost -U postgres -d klinik_db > dosya.sql
            cmd = [
                "pg_dump",
                "-h", self.db.DB_HOST,
                "-p", self.db.DB_PORT,
                "-U", self.db.DB_USER,
                self.db.DB_NAME
            ]

            with open(sql_file, "w") as f:
                subprocess.run(cmd, stdout=f, env=env, check=True)

            # 2. Dosyayı ZIP'le
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(sql_file, os.path.basename(sql_file))

            # 3. SQL dosyasını sil (Sadece zip kalsın)
            os.remove(sql_file)

            return True, zip_file

        except Exception as e:
            print(f"Yedekleme Hatası: {e}")
            return False, str(e)