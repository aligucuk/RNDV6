import psycopg2
import hashlib
import datetime
import json

class DatabaseManager:
    def __init__(self):
        self.DB_NAME = "klinik_db"
        self.DB_USER = "postgres"
        self.DB_PASS = "1234" 
        self.DB_HOST = "localhost"
        self.DB_PORT = "5432"
        self.conn = None
        self.connect()
        self.create_tables()
        self._migrate_tables()
        self._init_settings() # Varsayılan modül ayarları

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                database=self.DB_NAME, user=self.DB_USER, 
                password=self.DB_PASS, host=self.DB_HOST, port=self.DB_PORT
            )
            self.conn.autocommit = True
        except Exception as e:
            print(f"⚠️ Bağlantı Hatası: {e}")

    def create_tables(self):
        if not self.conn: return
        with self.conn.cursor() as cur:
            # --- TEMEL TABLOLAR ---
            cur.execute("""CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(50) UNIQUE, password_hash VARCHAR(255), role VARCHAR(20) DEFAULT 'admin', full_name VARCHAR(100), commission_rate INTEGER DEFAULT 0)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS patients (id SERIAL PRIMARY KEY, tc_no VARCHAR(11) UNIQUE, full_name VARCHAR(100), phone VARCHAR(20), gender VARCHAR(10), birth_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, referral_source VARCHAR(50) DEFAULT 'Bilinmiyor')""")
            cur.execute("""CREATE TABLE IF NOT EXISTS appointments (id SERIAL PRIMARY KEY, patient_id INTEGER REFERENCES patients(id), doctor_id INTEGER REFERENCES users(id), appointment_date TIMESTAMP, status VARCHAR(20), notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS transactions (id SERIAL PRIMARY KEY, trans_type VARCHAR(10), category VARCHAR(50), amount DECIMAL(10, 2), description TEXT, trans_date DATE, doctor_id INTEGER REFERENCES users(id))""")
            cur.execute("""CREATE TABLE IF NOT EXISTS system_logs (id SERIAL PRIMARY KEY, user_name VARCHAR(50), action_type VARCHAR(50), description TEXT, log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS inventory (id SERIAL PRIMARY KEY, product_name VARCHAR(100), unit VARCHAR(20), quantity INTEGER, critical_level INTEGER)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS app_settings (setting_key VARCHAR(50) PRIMARY KEY, setting_value TEXT)""")
            
            # --- MEDİKAL & GÖRÜNTÜLEME ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS medical_records (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id),
                    doctor_id INTEGER REFERENCES users(id),
                    visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    complaint TEXT, diagnosis TEXT, treatment TEXT, prescription TEXT,
                    body_map_data TEXT, photo_before TEXT, photo_after TEXT
                )
            """)

            # --- YENİ: PAKET / SEANS TAKİBİ (FİNANS) ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS service_packages (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id),
                    package_name VARCHAR(100),
                    total_sessions INTEGER,
                    used_sessions INTEGER DEFAULT 0,
                    price DECIMAL(10, 2),
                    status VARCHAR(20) DEFAULT 'Aktif', -- Aktif, Bitti, İptal
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # --- YENİ: MEDİKAL ŞABLONLAR (MAKRO) ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS medical_templates (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(100),
                    content TEXT,
                    type VARCHAR(50) -- Tani, Tedavi, Recete
                )
            """)

            # --- YENİ: HASTA DOSYALARI (FILE STORAGE) ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS patient_files (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id),
                    file_name VARCHAR(255),
                    file_path TEXT,
                    file_type VARCHAR(50), -- PDF, JPG, DICOM
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Varsayılan Kullanıcılar
            self._create_user(cur, "admin", "admin123", "admin", "Yönetici", 0)
            self._create_user(cur, "doktor1", "1234", "doktor", "Dr. Ahmet Yılmaz", 40)
            self._create_user(cur, "sekreter1", "1234", "sekreter", "Zeynep Hanım", 0)

    def _migrate_tables(self):
        """Tablo güncellemeleri"""
        if not self.conn: return
        with self.conn.cursor() as cur:
            try:
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS commission_rate INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS doctor_id INTEGER REFERENCES users(id)")
                cur.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS referral_source VARCHAR(50) DEFAULT 'Bilinmiyor'")
                cur.execute("ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS body_map_data TEXT")
                cur.execute("ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS photo_before TEXT")
                cur.execute("ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS photo_after TEXT")
            except Exception as e: print(f"Migration: {e}")

    def _init_settings(self):
        """Varsayılan Modül Ayarları"""
        defaults = {
            "module_finance": "1",
            "module_stock": "1",
            "module_sms": "0",
            "module_3d": "1",
            "license_doctor_limit": "5"
        }
        for k, v in defaults.items():
            if not self.get_setting(k):
                self.set_setting(k, v)

    def _create_user(self, cur, user, pwd, role, name, comm_rate):
        cur.execute("SELECT * FROM users WHERE username = %s", (user,))
        if not cur.fetchone():
            hashed = hashlib.sha256(pwd.encode()).hexdigest()
            cur.execute("INSERT INTO users (username, password_hash, role, full_name, commission_rate) VALUES (%s, %s, %s, %s, %s)", (user, hashed, role, name, comm_rate))

    # --- GÜVENLİK: VERİ MASKELEME ---
    def get_patient_secure(self, pid, user_role):
        """Kullanıcı rolüne göre veriyi maskeler"""
        p = self.get_patient_by_id(pid)
        if not p: return None
        
        # p: (id, tc, name, phone, gender, birth, created, referral)
        if user_role in ["sekreter", "admin"]:
            return p # Tam yetki
        else:
            # Doktor veya diğerleri maskeli görür
            p_list = list(p)
            p_list[1] = self._mask_string(p_list[1], 2, 2) # TC
            p_list[3] = self._mask_string(p_list[3], 3, 2) # Tel
            return tuple(p_list)

    def _mask_string(self, text, start_chars, end_chars):
        if not text or len(text) < (start_chars + end_chars): return text
        return text[:start_chars] + "*" * (len(text) - start_chars - end_chars) + text[-end_chars:]

    # --- AYARLAR & MODÜLLER ---
    def get_setting(self, key):
        res = self._fetch("SELECT setting_value FROM app_settings WHERE setting_key=%s", (key,), False)
        return res[0] if res else None

    def set_setting(self, key, value):
        if self.get_setting(key): return self._execute("UPDATE app_settings SET setting_value=%s WHERE setting_key=%s", (value, key))
        else: return self._execute("INSERT INTO app_settings (setting_key, setting_value) VALUES (%s, %s)", (key, value))

    def is_module_active(self, module_name):
        val = self.get_setting(module_name)
        return val == "1"

    # --- PAKET / SEANS İŞLEMLERİ (YENİ) ---
    def add_package(self, pid, name, total, price):
        return self._execute("INSERT INTO service_packages (patient_id, package_name, total_sessions, price) VALUES (%s, %s, %s, %s)", (pid, name, total, price))
    
    def get_patient_packages(self, pid):
        return self._fetch("SELECT * FROM service_packages WHERE patient_id=%s ORDER BY created_at DESC", (pid,))
    
    def use_session(self, package_id):
        # Otomatik kontrol: Bitti mi?
        pkg = self._fetch("SELECT total_sessions, used_sessions FROM service_packages WHERE id=%s", (package_id,), False)
        if pkg and pkg[1] < pkg[0]:
            self._execute("UPDATE service_packages SET used_sessions = used_sessions + 1 WHERE id=%s", (package_id,))
            # Eğer bittiyse status güncelle
            if pkg[1] + 1 == pkg[0]:
                 self._execute("UPDATE service_packages SET status='Tamamlandı' WHERE id=%s", (package_id,))
            return True
        return False

    # --- ŞABLON İŞLEMLERİ (YENİ) ---
    def get_templates(self, type_filter):
        return self._fetch("SELECT id, title, content FROM medical_templates WHERE type=%s", (type_filter,))
    
    def add_template(self, title, content, t_type):
        return self._execute("INSERT INTO medical_templates (title, content, type) VALUES (%s, %s, %s)", (title, content, t_type))

    # --- MEVCUT TEMEL FONKSİYONLAR (Aynen Koruyoruz) ---
    def check_login(self, u, p):
        h = hashlib.sha256(p.encode()).hexdigest()
        return self._fetch("SELECT id, username, full_name, role FROM users WHERE username=%s AND password_hash=%s", (u, h), False)
    def log_action(self, u, a, d): self._execute("INSERT INTO system_logs (user_name, action_type, description) VALUES (%s, %s, %s)", (u, a, d))
    def get_all_patients(self): return self._fetch("SELECT * FROM patients ORDER BY id DESC")
    def get_patient_by_id(self, pid): return self._fetch("SELECT * FROM patients WHERE id=%s", (pid,), False)
    def add_patient(self, tc, name, phone, gender, bdate, source="Bilinmiyor"): return self._execute("INSERT INTO patients (tc_no, full_name, phone, gender, birth_date, referral_source) VALUES (%s, %s, %s, %s, %s, %s)", (tc, name, phone, gender, bdate, source))
    def update_patient(self, pid, tc, name, phone, gender, bdate, source): return self._execute("UPDATE patients SET tc_no=%s, full_name=%s, phone=%s, gender=%s, birth_date=%s, referral_source=%s WHERE id=%s", (tc, name, phone, gender, bdate, source, pid))
    def delete_patient(self, pid): 
        self._execute("DELETE FROM appointments WHERE patient_id=%s", (pid,))
        return self._execute("DELETE FROM patients WHERE id=%s", (pid,))
    def add_appointment(self, pid, did, dt, notes): return self._execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, notes) VALUES (%s, %s, %s, %s)", (pid, did, dt, notes))
    def get_todays_appointments(self): 
        t = datetime.date.today().strftime('%Y-%m-%d')
        return self._fetch("SELECT a.id, p.full_name, a.appointment_date, a.status, p.id FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE DATE(a.appointment_date)=%s ORDER BY a.appointment_date", (t,))
    def set_appointment_status(self, aid, st): return self._execute("UPDATE appointments SET status=%s WHERE id=%s", (st, aid))
    def get_dashboard_stats(self): return self._fetch("SELECT status, COUNT(*) FROM appointments GROUP BY status")
    def auto_update_status(self): self._execute("UPDATE appointments SET status='Tamamlandı' WHERE appointment_date < NOW() AND status='Bekliyor'", None)
    def get_appointments_by_range(self, s, e): return self._fetch("SELECT appointment_date, status FROM appointments WHERE appointment_date BETWEEN %s AND %s", (s, e))
    def add_medical_record(self, pid, did, comp, diag, treat, presc, body_map, p_before, p_after):
        return self._execute("INSERT INTO medical_records (patient_id, doctor_id, complaint, diagnosis, treatment, prescription, body_map_data, photo_before, photo_after) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (pid, did, comp, diag, treat, presc, body_map, p_before, p_after))
    def get_patient_history(self, pid): return self._fetch("SELECT m.visit_date, u.full_name, m.complaint, m.diagnosis, m.treatment, m.prescription, m.body_map_data, m.photo_before, m.photo_after FROM medical_records m JOIN users u ON m.doctor_id=u.id WHERE m.patient_id=%s ORDER BY m.visit_date DESC", (pid,))
    def get_doctors(self): return self._fetch("SELECT id, full_name, commission_rate FROM users WHERE role='doktor'")
    def add_transaction(self, t, c, a, d, dt, did=None): return self._execute("INSERT INTO transactions (trans_type, category, amount, description, trans_date, doctor_id) VALUES (%s, %s, %s, %s, %s, %s)", (t, c, a, d, dt, did))
    def get_transactions(self): return self._fetch("SELECT t.id, t.trans_type, t.category, t.amount, t.description, t.trans_date, u.full_name FROM transactions t LEFT JOIN users u ON t.doctor_id = u.id ORDER BY t.trans_date DESC")
    def delete_transaction(self, tid): return self._execute("DELETE FROM transactions WHERE id=%s", (tid,))
    def get_finance_stats(self):
        rows = self._fetch("SELECT trans_type, SUM(amount) FROM transactions GROUP BY trans_type")
        inc, exp = 0, 0
        for r in rows:
            if r[0]=="Gelir": inc=r[1]
            elif r[0]=="Gider": exp=r[1]
        return (inc, exp, inc-exp)
    def calculate_commission(self, did, m, y):
        res = self._fetch("SELECT SUM(amount) FROM transactions WHERE doctor_id=%s AND trans_type='Gelir' AND EXTRACT(MONTH FROM trans_date)=%s AND EXTRACT(YEAR FROM trans_date)=%s", (did, m, y), False)
        tot = res[0] if res and res[0] else 0
        rate = self._fetch("SELECT commission_rate FROM users WHERE id=%s", (did,), False)[0]
        return tot, rate, tot*(rate/100)
    def add_product(self, n, u, q, c): return self._execute("INSERT INTO inventory (product_name, unit, quantity, critical_level) VALUES (%s, %s, %s, %s)", (n, u, q, c))
    def get_inventory(self): return self._fetch("SELECT * FROM inventory ORDER BY product_name ASC")
    def update_stock(self, pid, ch): return self._execute("UPDATE inventory SET quantity=quantity+%s WHERE id=%s", (ch, pid))
    def delete_product(self, pid): return self._execute("DELETE FROM inventory WHERE id=%s", (pid,))
    def get_patient_sources(self): return self._fetch("SELECT referral_source, COUNT(*) FROM patients GROUP BY referral_source")
    def get_monthly_income_stats(self): return self._fetch("SELECT TO_CHAR(trans_date, 'YYYY-MM'), SUM(amount) FROM transactions WHERE trans_type='Gelir' GROUP BY TO_CHAR(trans_date, 'YYYY-MM') ORDER BY TO_CHAR(trans_date, 'YYYY-MM') DESC LIMIT 6")
    def get_all_users(self): return self._fetch("SELECT id, username, full_name, role, commission_rate FROM users ORDER BY id ASC")
    def add_user(self, u, p, n, r, c=0):
        if self._fetch("SELECT id FROM users WHERE username=%s", (u,), False): return False
        h = hashlib.sha256(p.encode()).hexdigest()
        return self._execute("INSERT INTO users (username, password_hash, full_name, role, commission_rate) VALUES (%s, %s, %s, %s, %s)", (u, h, n, r, c))
    def delete_user(self, uid): return self._execute("DELETE FROM users WHERE id=%s", (uid,))
    def change_password(self, uid, np): return self._execute("UPDATE users SET password_hash=%s WHERE id=%s", (hashlib.sha256(np.encode()).hexdigest(), uid))

    # Helper
    def _execute(self, q, p):
        if not self.conn: return False
        try:
            with self.conn.cursor() as cur: cur.execute(q, p)
            return True
        except Exception as e: print(f"DB Err: {e}"); return False
    def _fetch(self, q, p=None, fetch_all=True):
        if not self.conn: return [] if fetch_all else None
        try:
            with self.conn.cursor() as cur:
                cur.execute(q, p)
                return cur.fetchall() if fetch_all else cur.fetchone()
        except: return [] if fetch_all else None
    def get_current_patient(self):
        """TV Ekranı için anlık 'Muayenede' olan hastayı getirir"""
        # En son 'Muayenede' statüsüne alınan randevuyu getir
        # Hem hasta adını hem doktor adını joinleyerek alıyoruz
        q = """
            SELECT p.full_name, u.full_name 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            JOIN users u ON a.doctor_id = u.id 
            WHERE a.status = 'Muayenede' 
            ORDER BY a.appointment_date DESC 
            LIMIT 1
        """
        return self._fetch(q, fetch_all=False)
    # --- YENİ: DOSYA YÖNETİMİ ---
    def add_patient_file(self, pid, fname, fpath, ftype):
        return self._execute("INSERT INTO patient_files (patient_id, file_name, file_path, file_type) VALUES (%s, %s, %s, %s)", (pid, fname, fpath, ftype))

    def get_patient_files(self, pid):
        return self._fetch("SELECT id, file_name, file_path, file_type, uploaded_at FROM patient_files WHERE patient_id=%s ORDER BY uploaded_at DESC", (pid,))

    def delete_patient_file(self, fid):
        return self._execute("DELETE FROM patient_files WHERE id=%s", (fid,))

    # --- YENİ: GDPR / UNUTULMA HAKKI ---
    def anonymize_patient(self, pid):
        """Hastayı silmez ama kimliğini tamamen yok eder (Finansal kayıtlar bozulmasın diye)"""
        anon_name = f"Anonim Hasta {pid}"
        anon_tc = "00000000000"
        anon_phone = "0000000000"
        
        # 1. Kişisel verileri anonimleştir
        self._execute("UPDATE patients SET full_name=%s, tc_no=%s, phone=%s, referral_source='Anonim' WHERE id=%s", (anon_name, anon_tc, anon_phone, pid))
        
        # 2. Medikal geçmişi sil (Hassas veri)
        self._execute("DELETE FROM medical_records WHERE patient_id=%s", (pid,))
        
        # 3. Dosyaları sil
        self._execute("DELETE FROM patient_files WHERE patient_id=%s", (pid,))
        
        return True