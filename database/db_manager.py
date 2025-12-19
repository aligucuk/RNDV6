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
        self._init_settings()

    def connect(self):
        try:
            self.conn = psycopg2.connect(database=self.DB_NAME, user=self.DB_USER, password=self.DB_PASS, host=self.DB_HOST, port=self.DB_PORT)
            self.conn.autocommit = True
        except Exception as e: print(f"⚠️ Bağlantı Hatası: {e}")

    def create_tables(self):
        if not self.conn: return
        with self.conn.cursor() as cur:
            # Tablo tanımları...
            cur.execute("""CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(50) UNIQUE, password_hash VARCHAR(255), role VARCHAR(20) DEFAULT 'admin', full_name VARCHAR(100), commission_rate INTEGER DEFAULT 0, dashboard_config TEXT)""")
            # HASTA TABLOSUNA EMAIL EKLENECEK (Migrate ile)
            cur.execute("""CREATE TABLE IF NOT EXISTS patients (id SERIAL PRIMARY KEY, tc_no VARCHAR(11) UNIQUE, full_name VARCHAR(100), phone VARCHAR(20), gender VARCHAR(10), birth_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, referral_source VARCHAR(50) DEFAULT 'Bilinmiyor', crm_status VARCHAR(50) DEFAULT 'Yeni', email VARCHAR(100))""")
            
            cur.execute("""CREATE TABLE IF NOT EXISTS appointments (id SERIAL PRIMARY KEY, patient_id INTEGER REFERENCES patients(id), doctor_id INTEGER REFERENCES users(id), appointment_date TIMESTAMP, status VARCHAR(20), notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reminder_sent BOOLEAN DEFAULT FALSE)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS transactions (id SERIAL PRIMARY KEY, trans_type VARCHAR(10), category VARCHAR(50), amount DECIMAL(10, 2), description TEXT, trans_date DATE, doctor_id INTEGER REFERENCES users(id))""")
            cur.execute("""CREATE TABLE IF NOT EXISTS system_logs (id SERIAL PRIMARY KEY, user_name VARCHAR(50), action_type VARCHAR(50), description TEXT, log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS app_settings (setting_key VARCHAR(50) PRIMARY KEY, setting_value TEXT)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS inventory (id SERIAL PRIMARY KEY, product_name VARCHAR(100), unit VARCHAR(20), quantity INTEGER, critical_level INTEGER)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS inventory_logs (id SERIAL PRIMARY KEY, product_id INTEGER REFERENCES inventory(id), doctor_id INTEGER REFERENCES users(id), patient_id INTEGER REFERENCES patients(id), quantity INTEGER, usage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS medical_records (id SERIAL PRIMARY KEY, patient_id INTEGER REFERENCES patients(id), doctor_id INTEGER REFERENCES users(id), visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, complaint TEXT, diagnosis TEXT, treatment TEXT, prescription TEXT, body_map_data TEXT, photo_before TEXT, photo_after TEXT)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS patient_files (id SERIAL PRIMARY KEY, patient_id INTEGER REFERENCES patients(id), file_name VARCHAR(255), file_path TEXT, file_type VARCHAR(50), uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS doctor_notes (id SERIAL PRIMARY KEY, doctor_id INTEGER, note_date TEXT, note_text TEXT, is_shared BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, sender_id INTEGER, receiver_id INTEGER, message_text TEXT, is_read BOOLEAN DEFAULT FALSE, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            
            # Bildirim Ayarları
            cur.execute("""CREATE TABLE IF NOT EXISTS notification_settings (id SERIAL PRIMARY KEY, channel VARCHAR(20), api_key TEXT, api_secret TEXT, sender_id VARCHAR(50), is_active BOOLEAN DEFAULT FALSE, template_text TEXT)""")
            
            # Varsayılanlar
            self._create_user(cur, "admin", "admin123", "admin", "Yönetici", 0)
            self._create_user(cur, "doktor1", "1234", "doktor", "Dr. Ahmet Yılmaz", 40)
            self._create_user(cur, "sekreter", "1234", "sekreter", "Zeynep Hanım", 0)
            self._init_notification_settings(cur)

    # ... (Buraya kadar olan kodlar aynı kalsın) ...

    def _migrate_tables(self):
        if not self.conn: return
        with self.conn.cursor() as cur:
            try:
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS commission_rate INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS dashboard_config TEXT")
                cur.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS email VARCHAR(100)")
                cur.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS crm_status VARCHAR(50) DEFAULT 'Yeni'")
                cur.execute("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS reminder_sent BOOLEAN DEFAULT FALSE")
                
                # YENİLER
                cur.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS patient_id INTEGER REFERENCES patients(id)")
                cur.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS is_debt_payment BOOLEAN DEFAULT FALSE")
                cur.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS current_debt DECIMAL(10, 2) DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS can_create_app BOOLEAN DEFAULT FALSE")
                cur.execute("ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS target_user_id INTEGER")
                cur.execute("ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS sender_name VARCHAR(100)")
            except Exception as e: 
                print(f"Migration Log: {e}")

    # --- DİKKAT: BU FONKSİYONLAR _migrate_tables İLE AYNI HİZADA OLMALI (SOLA YASLI) ---
    
    def add_transaction_linked(self, t_type, cat, amount, desc, date, doc_id, pat_id=None, is_debt=False):
        """Hastaya bağlı işlem ekler ve borcu günceller"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO transactions (trans_type, category, amount, description, trans_date, doctor_id, patient_id, is_debt_payment) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (t_type, cat, amount, desc, date, doc_id, pat_id, is_debt))
            
            if pat_id:
                if t_type == "Gelir" and is_debt: # Borç tahsilatı
                    cur.execute("UPDATE patients SET current_debt = current_debt - %s WHERE id=%s", (amount, pat_id))
                elif t_type == "Borç": # Yeni borç
                    cur.execute("UPDATE patients SET current_debt = current_debt + %s WHERE id=%s", (amount, pat_id))
            return True

    def get_patient_debt(self, pid):
        res = self._fetch("SELECT current_debt FROM patients WHERE id=%s", (pid,), False)
        return res[0] if res else 0.0

    def set_user_permission(self, uid, can_create):
        return self._execute("UPDATE users SET can_create_app=%s WHERE id=%s", (can_create, uid))
        
    def get_user_permission(self, uid):
        res = self._fetch("SELECT can_create_app FROM users WHERE id=%s", (uid,), False)
        return res[0] if res else False

    def add_shared_note(self, sender_name, target_uid, date, text):
        return self._execute("INSERT INTO doctor_notes (doctor_id, note_date, note_text, is_shared, target_user_id, sender_name) VALUES (%s, %s, %s, TRUE, %s, %s)", (target_uid, date, text, target_uid, sender_name))
        
    def _init_settings(self):
        defaults = {"module_finance": "1", "module_stock": "1", "module_sms": "0", "module_3d": "1", "theme_mode": "light", "theme_color": "teal"}
        for k, v in defaults.items():
            if not self.get_setting(k): self.set_setting(k, v)

    def _init_notification_settings(self, cur):
        channels = [
            ("sms", "Sayın {hasta}, {tarih} {saat} tarihindeki randevunuzu hatırlatırız."),
            ("email", "Sayın {hasta}, Randevu Hatırlatması: {tarih} {saat}."),
            ("whatsapp", "Merhaba {hasta}, {tarih} {saat} randevunuz mevcuttur.")
        ]
        for ch, tmpl in channels:
            cur.execute("SELECT id FROM notification_settings WHERE channel=%s", (ch,))
            if not cur.fetchone():
                cur.execute("INSERT INTO notification_settings (channel, template_text, is_active) VALUES (%s, %s, FALSE)", (ch, tmpl))

    def _create_user(self, cur, user, pwd, role, name, comm_rate):
        cur.execute("SELECT id FROM users WHERE username = %s", (user,))
        if not cur.fetchone():
            hashed = hashlib.sha256(pwd.encode()).hexdigest()
            cur.execute("INSERT INTO users (username, password_hash, role, full_name, commission_rate) VALUES (%s, %s, %s, %s, %s)", (user, hashed, role, name, comm_rate))

    # --- HELPER ---
    def _execute(self, q, p=None):
        if not self.conn: return False
        try:
            with self.conn.cursor() as cur: cur.execute(q, p); return True
        except Exception as e: print(f"DB Err: {e}"); return False
    def _fetch(self, q, p=None, fetch_all=True):
        if not self.conn: return [] if fetch_all else None
        try:
            with self.conn.cursor() as cur: cur.execute(q, p); return cur.fetchall() if fetch_all else cur.fetchone()
        except: return [] if fetch_all else None

    # --- HASTA FONKSİYONLARI (GÜNCELLENDİ) ---
    def add_patient(self, tc, name, phone, gender, bdate, source="Bilinmiyor", email=""):
        # Email parametresi eklendi
        return self._execute("INSERT INTO patients (tc_no, full_name, phone, gender, birth_date, referral_source, crm_status, email) VALUES (%s, %s, %s, %s, %s, %s, 'Yeni', %s)", (tc, name, phone, gender, bdate, source, email))
    
    def get_all_patients(self): return self._fetch("SELECT * FROM patients ORDER BY id DESC")
    def get_patient_by_id(self, pid): return self._fetch("SELECT * FROM patients WHERE id=%s", (pid,), False)
    def search_patients(self, term): return self._fetch("SELECT * FROM patients WHERE full_name ILIKE %s OR tc_no ILIKE %s", (f"%{term}%", f"%{term}%"))
    def get_patient_sources(self): return self._fetch("SELECT referral_source, COUNT(*) FROM patients GROUP BY referral_source")
    def get_patients_by_status(self): return self._fetch("SELECT id, full_name, phone, crm_status, referral_source FROM patients ORDER BY created_at DESC")
    def update_patient_status(self, pid, new_status): return self._execute("UPDATE patients SET crm_status=%s WHERE id=%s", (new_status, pid))

    # --- BİLDİRİM FONKSİYONLARI (GÜNCELLENDİ) ---
    def get_notification_settings(self): return self._fetch("SELECT channel, api_key, api_secret, sender_id, is_active, template_text FROM notification_settings")
    def update_notification_setting(self, channel, key, secret, sender, active, template): return self._execute("UPDATE notification_settings SET api_key=%s, api_secret=%s, sender_id=%s, is_active=%s, template_text=%s WHERE channel=%s", (key, secret, sender, active, template, channel))
    
    def get_pending_reminders(self):
        # *** GÜNCELLEME: Email'i de çekiyoruz ***
        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(hours=24)
        query = """
            SELECT a.id, p.full_name, p.phone, p.email, a.appointment_date 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            WHERE a.appointment_date BETWEEN %s AND %s 
            AND a.status = 'Bekliyor' 
            AND a.reminder_sent = FALSE
        """
        return self._fetch(query, (now, tomorrow))

    def mark_reminder_sent(self, app_id): self._execute("UPDATE appointments SET reminder_sent = TRUE WHERE id=%s", (app_id,))

    # --- DİĞER MODÜLLER ---
    def log_action(self, u, a, d): self._execute("INSERT INTO system_logs (user_name, action_type, description) VALUES (%s, %s, %s)", (u, a, d))
    def check_login(self, u, p): h = hashlib.sha256(p.encode()).hexdigest(); return self._fetch("SELECT id, username, full_name, role FROM users WHERE username=%s AND password_hash=%s", (u, h), False)
    def get_users_except(self, uid): return self._fetch("SELECT id, username, role, full_name FROM users WHERE id != %s", (uid,))
    def get_all_users(self): return self._fetch("SELECT id, username, full_name, role, commission_rate FROM users ORDER BY id ASC")
    def get_doctors(self): return self._fetch("SELECT id, full_name FROM users WHERE role='doktor'")
    def add_user(self, u, p, n, r, c=0):
        if self._fetch("SELECT id FROM users WHERE username=%s", (u,), False): return False
        h = hashlib.sha256(p.encode()).hexdigest()
        return self._execute("INSERT INTO users (username, password_hash, full_name, role, commission_rate) VALUES (%s, %s, %s, %s, %s)", (u, h, n, r, c))
    def delete_user(self, uid): return self._execute("DELETE FROM users WHERE id=%s", (uid,))
    def send_message(self, sid, rid, txt): return self._execute("INSERT INTO messages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)", (sid, rid, txt))
    def get_chat_history(self, u1, u2): return self._fetch("SELECT sender_id, message_text, timestamp FROM messages WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s) ORDER BY timestamp ASC", (u1, u2, u2, u1))
    def delete_patient(self, pid):
        self._execute("DELETE FROM appointments WHERE patient_id=%s", (pid,))
        self._execute("DELETE FROM medical_records WHERE patient_id=%s", (pid,))
        self._execute("DELETE FROM patient_files WHERE patient_id=%s", (pid,))
        return self._execute("DELETE FROM patients WHERE id=%s", (pid,))
    def auto_update_status(self): self._execute("UPDATE appointments SET status='Tamamlandı' WHERE appointment_date < CURRENT_TIMESTAMP AND status='Bekliyor'", None)
    def add_appointment(self, pid, did, dt, notes): return self._execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, notes, status) VALUES (%s, %s, %s, %s, 'Bekliyor')", (pid, did, dt, notes))
    def get_appointments_by_doctor(self, did): return self._fetch("SELECT a.id, p.full_name, a.appointment_date, a.status, a.notes, p.id FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.doctor_id=%s ORDER BY a.appointment_date ASC", (did,))
    def get_todays_appointments(self): t = datetime.date.today().strftime('%Y-%m-%d'); return self._fetch("SELECT a.id, p.full_name, a.appointment_date, a.status, p.id FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE DATE(a.appointment_date)=%s ORDER BY a.appointment_date", (t,))
    def set_appointment_status(self, aid, st): return self._execute("UPDATE appointments SET status=%s WHERE id=%s", (st, aid))
    def add_medical_record(self, pid, did, comp, diag, treat, presc, body_map, p_before, p_after): return self._execute("INSERT INTO medical_records (patient_id, doctor_id, complaint, diagnosis, treatment, prescription, body_map_data, photo_before, photo_after) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (pid, did, comp, diag, treat, presc, body_map, p_before, p_after))
    def get_patient_history(self, pid): return self._fetch("SELECT m.visit_date, u.full_name, m.complaint, m.diagnosis, m.treatment, m.prescription, m.body_map_data, m.photo_before, m.photo_after FROM medical_records m JOIN users u ON m.doctor_id=u.id WHERE m.patient_id=%s ORDER BY m.visit_date DESC", (pid,))
    def add_patient_file(self, pid, fname, fpath, ftype): return self._execute("INSERT INTO patient_files (patient_id, file_name, file_path, file_type) VALUES (%s, %s, %s, %s)", (pid, fname, fpath, ftype))
    def get_patient_files(self, pid): return self._fetch("SELECT * FROM patient_files WHERE patient_id=%s ORDER BY uploaded_at DESC", (pid,))
    def calculate_commission(self, did, m, y): res = self._fetch("SELECT SUM(amount) FROM transactions WHERE doctor_id=%s AND trans_type='Gelir' AND EXTRACT(MONTH FROM trans_date)=%s AND EXTRACT(YEAR FROM trans_date)=%s", (did, m, y), False); tot = float(res[0]) if res and res[0] else 0.0; ud = self._fetch("SELECT commission_rate FROM users WHERE id=%s", (did,), False); rate = ud[0] if ud else 0; return tot, rate, tot * (rate / 100.0)
    def add_transaction(self, t, c, a, d, dt, did=None): return self._execute("INSERT INTO transactions (trans_type, category, amount, description, trans_date, doctor_id) VALUES (%s, %s, %s, %s, %s, %s)", (t, c, a, d, dt, did))
    def get_transactions(self): return self._fetch("SELECT t.id, t.trans_type, t.category, t.amount, t.description, t.trans_date, u.full_name FROM transactions t LEFT JOIN users u ON t.doctor_id = u.id ORDER BY t.trans_date DESC")
    def delete_transaction(self, tid): return self._execute("DELETE FROM transactions WHERE id=%s", (tid,))
    def add_product(self, n, u, q, c): return self._execute("INSERT INTO inventory (product_name, unit, quantity, critical_level) VALUES (%s, %s, %s, %s)", (n, u, q, c))
    def get_inventory(self): return self._fetch("SELECT * FROM inventory ORDER BY product_name ASC")
    def update_stock(self, pid, ch): return self._execute("UPDATE inventory SET quantity=quantity+%s WHERE id=%s", (ch, pid))
    def delete_product(self, pid): return self._execute("DELETE FROM inventory WHERE id=%s", (pid,))
    def log_inventory_usage(self, prod_id, doc_id, pat_id, qty): self.update_stock(prod_id, -qty); return self._execute("INSERT INTO inventory_logs (product_id, doctor_id, patient_id, quantity) VALUES (%s, %s, %s, %s)", (prod_id, doc_id, pat_id, qty))
    def get_inventory_logs(self): return self._fetch("SELECT l.usage_date, i.product_name, u.full_name, p.full_name, l.quantity FROM inventory_logs l JOIN inventory i ON l.product_id = i.id JOIN users u ON l.doctor_id = u.id LEFT JOIN patients p ON l.patient_id = p.id ORDER BY l.usage_date DESC")
    def is_module_active(self, module_name): val = self.get_setting(module_name); return val == "1"
    def get_setting(self, key): res = self._fetch("SELECT setting_value FROM app_settings WHERE setting_key=%s", (key,), False); return res[0] if res else None
    def set_setting(self, key, value):
        if self.get_setting(key): return self._execute("UPDATE app_settings SET setting_value=%s WHERE setting_key=%s", (value, key))
        else: return self._execute("INSERT INTO app_settings (setting_key, setting_value) VALUES (%s, %s)", (key, value))
    def save_dashboard_config(self, uid, config_json): return self._execute("UPDATE users SET dashboard_config=%s WHERE id=%s", (config_json, uid))
    def get_dashboard_config(self, uid): res = self._fetch("SELECT dashboard_config FROM users WHERE id=%s", (uid,), False); return res[0] if res else None
    def factory_reset(self):
        try:
            with self.conn.cursor() as cur:
                for t in ["appointments", "medical_records", "transactions", "inventory_logs", "patient_files", "system_logs", "messages", "doctor_notes", "patients", "inventory"]: cur.execute(f"TRUNCATE TABLE {t} CASCADE")
            return True
        except: return False
    def add_note(self, did, d_date, text, share): return self._execute("INSERT INTO doctor_notes (doctor_id, note_date, note_text, is_shared) VALUES (%s, %s, %s, %s)", (did, d_date, text, share))
    
    def get_notes_by_date(self, did, d_date):
       
        return self._fetch("SELECT note_text, is_shared, sender_name FROM doctor_notes WHERE doctor_id=%s AND note_date=%s", (did, d_date))