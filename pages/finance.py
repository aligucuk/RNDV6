import flet as ft
from datetime import datetime

class FinancePage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Tarih")), ft.DataColumn(ft.Text("Tür")), 
                ft.DataColumn(ft.Text("Kategori")), ft.DataColumn(ft.Text("Tutar")), 
                ft.DataColumn(ft.Text("Açıklama")), ft.DataColumn(ft.Text("İşlem"))
            ],
            border=ft.border.all(1, "grey"), vertical_lines=ft.border.BorderSide(1, "grey"),
        )

    def view(self):
        self.dd_type = ft.Dropdown(label="Tür", width=100, options=[ft.dropdown.Option("Gelir"), ft.dropdown.Option("Gider")])
        self.txt_cat = ft.TextField(label="Kategori", width=150)
        self.txt_amount = ft.TextField(label="Tutar", width=100, input_filter=ft.NumbersOnlyInputFilter())
        self.txt_desc = ft.TextField(label="Açıklama", expand=True)
        btn_add = ft.ElevatedButton("Ekle", bgcolor="teal", color="white", on_click=self.add_transaction)

        self.load_transactions()

        docs = self.db.get_doctors()
        opts = [ft.dropdown.Option(str(u[0]), u[1]) for u in docs] if docs else []
        self.dd_doctor = ft.Dropdown(label="Doktor", options=opts)
        self.dd_month = ft.Dropdown(label="Ay", width=80, options=[ft.dropdown.Option(str(i), str(i)) for i in range(1, 13)])
        self.dd_year = ft.Dropdown(label="Yıl", width=100, options=[ft.dropdown.Option(str(y), str(y)) for y in range(2024, 2030)])
        self.lbl_result = ft.Text("Sonuç: -", size=16)
        btn_calc = ft.ElevatedButton("Hesapla", bgcolor="orange", color="white", on_click=self.calc_commission)

        tabs = ft.Tabs(tabs=[
            ft.Tab(text="Genel Kasa", icon="wallet", content=ft.Column([ft.Row([self.dd_type, self.txt_cat, self.txt_amount, self.txt_desc, btn_add]), ft.Divider(), ft.ListView(controls=[self.data_table], expand=True)])),
            ft.Tab(text="Hakediş", icon="calculate", content=ft.Column([ft.Row([self.dd_doctor, self.dd_month, self.dd_year, btn_calc]), ft.Divider(), ft.Container(content=self.lbl_result, padding=20, bgcolor="#fff3e0")])),
        ])

        return ft.View("/finance", [ft.AppBar(title=ft.Text("Finans Merkezi"), bgcolor="teal", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/doctor_home"))), ft.Container(content=tabs, padding=20, expand=True)])

    def add_transaction(self, e):
        if self.dd_type.value and self.txt_amount.value:
            self.db.add_transaction(self.dd_type.value, self.txt_cat.value, float(self.txt_amount.value), self.txt_desc.value, datetime.now())
            self.page.open(ft.SnackBar(ft.Text("Kaydedildi"), bgcolor="green"))
            self.load_transactions()

    def load_transactions(self):
        self.data_table.rows.clear()
        for t in self.db.get_transactions():
            self.data_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(t[5]))),
                ft.DataCell(ft.Text(t[1], color="green" if t[1]=="Gelir" else "red")),
                ft.DataCell(ft.Text(t[2])),
                ft.DataCell(ft.Text(f"{t[3]} ₺", weight="bold")),
                ft.DataCell(ft.Text(t[4])),
                ft.DataCell(ft.IconButton("delete", icon_color="red", on_click=lambda _, tid=t[0]: self.delete_trans(tid))),
            ]))
        
        if self.data_table.page:
            self.data_table.update()

    def delete_trans(self, tid):
        self.db.delete_transaction(tid)
        self.load_transactions()

    def calc_commission(self, e):
        if self.dd_doctor.value and self.dd_month.value:
            t, r, c = self.db.calculate_commission(int(self.dd_doctor.value), int(self.dd_month.value), int(self.dd_year.value))
            self.lbl_result.value = f"Ciro: {t} TL\nOran: %{r}\nHakediş: {c} TL"
            self.lbl_result.update()