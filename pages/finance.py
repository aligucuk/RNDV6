import flet as ft
import datetime

class FinancePage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.date_picker = ft.DatePicker(
            on_change=self.handle_date_change,
            first_date=datetime.datetime(2020, 1, 1),
            last_date=datetime.datetime(2030, 12, 31)
        )

    def handle_date_change(self, e):
        if e.control.value:
            self.txt_date.value = e.control.value.strftime("%d.%m.%Y")
            self.page.update()

    def view(self):
        # --- TAB 1: GENEL KASA ---
        inc, exp, net = self.db.get_finance_stats()
        
        def card(t, v, c, i):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(i, color="white"), ft.Text(t, color="white"), ft.Text(f"{v:.2f} ₺", size=20, weight="bold", color="white")
                ]), bgcolor=c, padding=15, border_radius=10, width=180, height=100
            )

        self.dd_type = ft.Dropdown(label="Tür", width=120, options=[ft.dropdown.Option("Gelir"), ft.dropdown.Option("Gider")], border_radius=10)
        self.txt_cat = ft.TextField(label="Kategori", width=180, border_radius=10)
        self.txt_amount = ft.TextField(label="Tutar", width=120, suffix_text="₺", keyboard_type="number", border_radius=10)
        self.txt_date = ft.TextField(label="Tarih", width=120, value=datetime.date.today().strftime("%d.%m.%Y"), read_only=True, border_radius=10)
        
        doctors = self.db.get_doctors()
        doc_options = [ft.dropdown.Option(key=str(d[0]), text=d[1]) for d in doctors]
        self.dd_doctor = ft.Dropdown(label="İlgili Doktor", width=250, options=doc_options, border_radius=10)

        rows = []
        for t in self.db.get_transactions():
            tid, ttype, cat, amt, desc, date, dname = t
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(date.strftime("%d.%m"))),
                ft.DataCell(ft.Text(ttype, color="green" if ttype=="Gelir" else "red")),
                ft.DataCell(ft.Text(cat)),
                ft.DataCell(ft.Text(f"{amt} ₺")),
                ft.DataCell(ft.Text(dname if dname else "-")),
                ft.DataCell(ft.IconButton("delete", icon_color="red", on_click=lambda e, x=tid: self.delete_clicked(x)))
            ]))

        tab_kasa = ft.Column([
            ft.Row([card("Gelir", inc, "green", "trending_up"), card("Gider", exp, "red", "trending_down"), card("Net", net, "blue", "account_balance")], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Row([self.dd_type, self.txt_cat, self.txt_amount, self.txt_date, ft.IconButton("event", on_click=lambda _: self.page.open(self.date_picker))], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.dd_doctor, ft.ElevatedButton("EKLE", on_click=self.add_clicked, bgcolor="primary", color="white")], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.DataTable(columns=[ft.DataColumn(ft.Text("Tarih")), ft.DataColumn(ft.Text("Tür")), ft.DataColumn(ft.Text("Kategori")), ft.DataColumn(ft.Text("Tutar")), ft.DataColumn(ft.Text("Doktor")), ft.DataColumn(ft.Text("Sil"))], rows=rows)
        ], scroll=ft.ScrollMode.AUTO)

        # --- TAB 2: HAKEDİŞ ---
        self.dd_comm_doctor = ft.Dropdown(label="Doktor Seçiniz", width=300, options=doc_options)
        self.dd_month = ft.Dropdown(label="Ay", width=100, options=[ft.dropdown.Option(str(i), str(i)) for i in range(1, 13)], value=str(datetime.date.today().month))
        self.dd_year = ft.Dropdown(label="Yıl", width=100, options=[ft.dropdown.Option(str(i), str(i)) for i in range(2024, 2030)], value=str(datetime.date.today().year))
        self.lbl_result = ft.Text("Hesaplama bekleniyor...", size=16)
        
        tab_hakedis = ft.Container(content=ft.Column([
            ft.Text("Doktor Prim Hesaplama", size=20, weight="bold", color="primary"),
            ft.Divider(),
            ft.Row([self.dd_comm_doctor, self.dd_month, self.dd_year], alignment=ft.MainAxisAlignment.CENTER),
            ft.ElevatedButton("HESAPLA", on_click=self.calc_commission, bgcolor="orange", color="white", width=200),
            ft.Divider(),
            ft.Container(content=self.lbl_result, bgcolor="surfaceVariant", padding=20, border_radius=10)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=40)

        # --- TAB 3: PAKET SATIŞI (YENİ) ---
        patients = self.db.get_all_patients()
        p_options = [ft.dropdown.Option(key=str(p[0]), text=f"{p[2]} ({p[1]})") for p in patients]
        
        self.dd_pkg_patient = ft.Dropdown(label="Hasta Seç", width=300, options=p_options)
        self.txt_pkg_name = ft.TextField(label="Paket Adı (Örn: 10 Seans Lazer)", width=300)
        self.txt_pkg_count = ft.TextField(label="Seans Sayısı", width=140, keyboard_type="number")
        self.txt_pkg_price = ft.TextField(label="Fiyat", width=140, keyboard_type="number", suffix_text="₺")
        
        tab_package = ft.Container(content=ft.Column([
            ft.Text("Hizmet Paketi Satışı", size=20, weight="bold", color="teal"),
            ft.Text("Hastaya toplu seans tanımlar ve borçlandırır.", size=12, color="grey"),
            ft.Divider(),
            self.dd_pkg_patient,
            self.txt_pkg_name,
            ft.Row([self.txt_pkg_count, self.txt_pkg_price], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.ElevatedButton("PAKETİ TANIMLA", icon="add_task", bgcolor="teal", color="white", on_click=self.add_package_click)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=30)

        # --- ANA GÖRÜNÜM ---
        return ft.View(
            "/finance",
            [
                ft.AppBar(title=ft.Text("Finans Merkezi"), bgcolor="background", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/dashboard"))),
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    tabs=[
                        ft.Tab(text="Genel Kasa", content=ft.Container(content=tab_kasa, padding=20)),
                        ft.Tab(text="Hakediş Hesapla", content=tab_hakedis),
                        ft.Tab(text="Paket Satışı", content=tab_package), # YENİ
                    ],
                    expand=True
                )
            ], bgcolor="background"
        )

    # ... (Eski fonksiyonlar: add_clicked, delete_clicked, calc_commission aynen kalıyor) ...
    def add_clicked(self, e):
        if not self.dd_type.value or not self.txt_amount.value: return
        try:
            amt = float(self.txt_amount.value)
            d_obj = datetime.datetime.strptime(self.txt_date.value, "%d.%m.%Y").date()
            doc_id = int(self.dd_doctor.value) if self.dd_doctor.value else None
            self.db.add_transaction(self.dd_type.value, self.txt_cat.value, amt, "", d_obj, doc_id)
            self.page.go("/finance")
        except: self.page.open(ft.SnackBar(ft.Text("Hata!"), bgcolor="red"))

    def delete_clicked(self, tid):
        self.db.delete_transaction(tid); self.page.go("/finance")

    def calc_commission(self, e):
        if not self.dd_comm_doctor.value: return
        doc_id = int(self.dd_comm_doctor.value)
        total, rate, comm = self.db.calculate_commission(doc_id, int(self.dd_month.value), int(self.dd_year.value))
        self.lbl_result.value = f"TOPLAM CİRO: {total:.2f} ₺\nPRİM ORANI: %{rate}\nÖDENECEK: {comm:.2f} ₺"
        self.page.update()

    # --- YENİ FONKSİYON: PAKET EKLEME ---
    def add_package_click(self, e):
        if not self.dd_pkg_patient.value or not self.txt_pkg_name.value:
            self.page.open(ft.SnackBar(ft.Text("Eksik bilgi!"), bgcolor="red")); return
        
        try:
            pid = int(self.dd_pkg_patient.value)
            total = int(self.txt_pkg_count.value)
            price = float(self.txt_pkg_price.value)
            
            # 1. Paketi Tanımla
            self.db.add_package(pid, self.txt_pkg_name.value, total, price)
            
            # 2. Gelir Olarak Kasaya İşle
            self.db.add_transaction("Gelir", "Paket Satışı", price, f"{self.txt_pkg_name.value}", datetime.date.today())
            
            self.page.open(ft.SnackBar(ft.Text("Paket Tanımlandı ve Kasaya İşlendi!"), bgcolor="green"))
            self.txt_pkg_name.value = ""; self.txt_pkg_count.value = ""; self.txt_pkg_price.value = ""
            self.page.update()
        except Exception as ex:
            self.page.open(ft.SnackBar(ft.Text(f"Hata: {ex}"), bgcolor="red"))