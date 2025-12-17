import flet as ft
import os

class SettingsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.user_role = page.session.get("user_role")
        self.user_id = page.session.get("user_id")

        self.folder_picker = ft.FilePicker(on_result=self.on_folder_picked)
        if self.folder_picker not in page.overlay:
            page.overlay.append(self.folder_picker)

    def on_folder_picked(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.db.set_setting("backup_path", e.path)
            self.lbl_backup_path.value = f"Klasör: {e.path}"
            self.page.update()

    def view(self):
        # --- TAB 1: PROFİL ---
        self.txt_new_pass = ft.TextField(label="Yeni Şifre", password=True, can_reveal_password=True)
        btn_change_pass = ft.ElevatedButton("Şifremi Güncelle", on_click=self.change_pass_click)
        tab_profile = ft.Container(content=ft.Column([ft.Text("Güvenlik", size=20, weight="bold"), ft.Divider(), self.txt_new_pass, btn_change_pass], width=400), padding=30)
        
        tabs = [ft.Tab(text="Profilim", content=tab_profile)]

        # --- TAB 2: YEDEKLEME ---
        current_path = self.db.get_setting("backup_path")
        self.lbl_backup_path = ft.Text(f"Klasör: {current_path if current_path else 'Seçilmedi'}")
        tab_backup = ft.Container(content=ft.Column([
            ft.Text("Yedekleme", size=20, weight="bold"),
            self.lbl_backup_path,
            ft.ElevatedButton("Klasör Seç", on_click=lambda _: self.folder_picker.get_directory_path())
        ], width=400), padding=30)
        tabs.append(ft.Tab(text="Yedekleme", content=tab_backup))

    def view(self):
        # ... (Profil ve Yedekleme sekmeleri aynı kalıyor) ...
        # (Burayı eski kodundan koru, sadece aşağıdaki Şablon kısmını ekle)
        
        self.txt_new_pass = ft.TextField(label="Yeni Şifre", password=True, can_reveal_password=True)
        btn_change_pass = ft.ElevatedButton("Şifremi Güncelle", on_click=self.change_pass_click)
        tab_profile = ft.Container(content=ft.Column([ft.Text("Güvenlik", size=20, weight="bold"), ft.Divider(), self.txt_new_pass, btn_change_pass], width=400), padding=30)
        tabs = [ft.Tab(text="Profilim", content=tab_profile)]

        current_path = self.db.get_setting("backup_path")
        self.lbl_backup_path = ft.Text(f"Klasör: {current_path if current_path else 'Seçilmedi'}")
        tab_backup = ft.Container(content=ft.Column([
            ft.Text("Yedekleme", size=20, weight="bold"),
            self.lbl_backup_path,
            ft.ElevatedButton("Klasör Seç", on_click=lambda _: self.folder_picker.get_directory_path())
        ], width=400), padding=30)
        tabs.append(ft.Tab(text="Yedekleme", content=tab_backup))

        # --- YENİ SEKME: ŞABLONLAR (Doktorlar da görebilir) ---
        self.txt_tpl_title = ft.TextField(label="Şablon Adı (Örn: Bel Fıtığı)", width=200)
        self.dd_tpl_type = ft.Dropdown(label="Tür", width=150, options=[ft.dropdown.Option("Tani"), ft.dropdown.Option("Tedavi"), ft.dropdown.Option("Recete")])
        self.txt_tpl_content = ft.TextField(label="İçerik (Uzun Metin)", multiline=True, min_lines=3, width=400)
        
        tab_templates = ft.Container(content=ft.Column([
            ft.Text("Hızlı Yazı Şablonları (Makro)", size=20, weight="bold"),
            ft.Row([self.txt_tpl_title, self.dd_tpl_type]),
            self.txt_tpl_content,
            ft.ElevatedButton("Şablonu Kaydet", icon="save", on_click=self.add_template_click)
        ]), padding=30)
        tabs.append(ft.Tab(text="Şablonlar", content=tab_templates))

        # --- ADMIN SEKME ---
        if self.user_role == "admin":
             # ... (Eski Admin kodlarını buraya yapıştır - Modüller ve Personel) ...
             # (Önceki mesajdaki kodların aynısı)
             pass 
        
        # --- GDPR: UNUTULMA HAKKI ---
        self.txt_anon_tc = ft.TextField(label="Hasta TC No", width=200)
            
        tab_gdpr = ft.Container(content=ft.Column([
                ft.Text("GDPR / Unutulma Hakkı", size=20, weight="bold", color="red"),
                ft.Text("DİKKAT: Bu işlem hastanın kimlik bilgilerini ve medikal geçmişini kalıcı olarak siler, ancak finansal kayıtları 'Anonim' olarak saklar.", size=12),
                ft.Row([self.txt_anon_tc, ft.ElevatedButton("HASTAYI ANONİMLEŞTİR", bgcolor="red", color="white", on_click=self.anonymize_click)])
            ]), padding=30)
            
        tabs.append(ft.Tab(text="GDPR", content=tab_gdpr))

        return ft.View("/settings", [ft.AppBar(title=ft.Text("Ayarlar"), bgcolor="background", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/dashboard"))), ft.Tabs(tabs=tabs, expand=True)], bgcolor="background")

    def change_pass_click(self, e):
        if self.db.change_password(self.user_id, self.txt_new_pass.value): self.page.open(ft.SnackBar(ft.Text("Güncellendi"), bgcolor="green"))
    
    def toggle_module(self, key, e):
        val = "1" if e.control.value else "0"
        self.db.set_setting(key, val)
        self.page.open(ft.SnackBar(ft.Text("Ayarlar kaydedildi. Etki etmesi için programı yeniden başlatın."), bgcolor="orange"))

    def add_user_click(self, e):
        # LİSANS KONTROLÜ (Basit Örnek)
        users = self.db.get_all_users()
        doctors = [u for u in users if u[3] == "doktor"]
        limit = int(self.db.get_setting("license_doctor_limit") or 5)
        
        if self.dd_u_role.value == "doktor" and len(doctors) >= limit:
            self.page.open(ft.SnackBar(ft.Text(f"Paket Limitiniz Dolu! ({limit} Doktor)"), bgcolor="red"))
            return

        if self.db.add_user(self.txt_u_user.value, self.txt_u_pass.value, self.txt_u_name.value, self.dd_u_role.value, int(self.txt_u_rate.value)):
            self.page.open(ft.SnackBar(ft.Text("Eklendi"), bgcolor="green")); self.refresh_user_list()
        else: self.page.open(ft.SnackBar(ft.Text("Hata!"), bgcolor="red"))

    def refresh_user_list(self):
        self.user_list.controls.clear()
        for u in self.db.get_all_users():
            uid, uname, fname, role, rate = u
            btn = ft.IconButton("delete", icon_color="red", on_click=lambda e, x=uid: self.delete_user_click(x))
            if uid == self.user_id: btn.visible = False
            self.user_list.controls.append(ft.Card(content=ft.ListTile(leading=ft.Icon("person"), title=ft.Text(f"{fname} ({uname})"), subtitle=ft.Text(f"{role} | %{rate}"), trailing=btn)))
        self.page.update()

    def delete_user_click(self, uid): self.db.delete_user(uid); self.refresh_user_list()
    def add_template_click(self, e):
        if not self.txt_tpl_title.value or not self.txt_tpl_content.value: return
        self.db.add_template(self.txt_tpl_title.value, self.txt_tpl_content.value, self.dd_tpl_type.value)
        self.page.open(ft.SnackBar(ft.Text("Şablon Eklendi!"), bgcolor="green"))
        self.txt_tpl_content.value = ""
        self.page.update()
    def anonymize_click(self, e):
        # TC'den ID bulmamız lazım. Basitlik için tüm hastaları çekip bulalım (veya SQL yazılabilir)
        patients = self.db.get_all_patients()
        pid = None
        for p in patients:
            if p[1] == self.txt_anon_tc.value:
                pid = p[0]
                break
        
        if pid:
            self.db.anonymize_patient(pid)
            self.page.open(ft.SnackBar(ft.Text("Hasta Başarıyla Anonimleştirildi."), bgcolor="green"))
            self.txt_anon_tc.value = ""
            self.page.update()
        else:
            self.page.open(ft.SnackBar(ft.Text("Hasta Bulunamadı!"), bgcolor="red"))