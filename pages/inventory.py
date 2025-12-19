import flet as ft

class InventoryPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.stock_list = ft.ListView(expand=True, spacing=10)
        self.log_list = ft.ListView(expand=True, spacing=10)

    def view(self):
        self.txt_name = ft.TextField(label="Ürün Adı", width=200)
        self.txt_qty = ft.TextField(label="Adet", width=100, input_filter=ft.NumbersOnlyInputFilter())
        self.txt_unit = ft.TextField(label="Birim", width=100)
        btn_add = ft.ElevatedButton("Ekle", bgcolor="teal", color="white", on_click=self.add_stock)
        self.load_stock()
        self.load_logs()

        tabs = ft.Tabs(tabs=[
            ft.Tab(text="Stok", icon="inventory", content=ft.Column([ft.Row([self.txt_name, self.txt_qty, self.txt_unit, btn_add]), ft.Divider(), self.stock_list])),
            ft.Tab(text="Geçmiş", icon="history", content=ft.Column([ft.Text("Kullanım Logları", size=18, weight="bold"), ft.Divider(), self.log_list])),
        ])

        return ft.View("/inventory", [ft.AppBar(title=ft.Text("Stok Yönetimi"), bgcolor="teal", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/doctor_home"))), ft.Container(content=tabs, padding=20, expand=True)])

    def add_stock(self, e):
        if self.txt_name.value and self.txt_qty.value:
            self.db.add_product(self.txt_name.value, self.txt_unit.value, int(self.txt_qty.value), 10)
            self.load_stock()

    def load_stock(self):
        self.stock_list.controls.clear()
        for i in self.db.get_inventory():
            self.stock_list.controls.append(ft.Container(
                content=ft.Row([
                    ft.Column([ft.Text(i[1], weight="bold"), ft.Text(f"{i[3]} {i[2]}")], width=200),
                    ft.Row([
                        ft.IconButton("remove", on_click=lambda _, pid=i[0], n=i[1]: self.use_stock(pid, n)),
                        ft.IconButton("add", on_click=lambda _, pid=i[0]: self.add_qty(pid, 1)),
                        ft.IconButton("delete", icon_color="red", on_click=lambda _, pid=i[0]: self.del_stock(pid))
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=10, bgcolor="white", border_radius=10, border=ft.border.all(1, "#eee")
            ))
        
        if self.stock_list.page:
            self.stock_list.update()

    def use_stock(self, pid, pname):
        txt_q = ft.TextField(label="Adet", value="1")
        txt_p = ft.TextField(label="Hasta ID (Opsiyonel)")
        def save(e):
            pat_id = int(txt_p.value) if txt_p.value else None
            self.db.log_inventory_usage(pid, self.page.session.get("user_id"), pat_id, int(txt_q.value))
            self.page.close(dlg); self.load_stock(); self.load_logs()
        dlg = ft.AlertDialog(title=ft.Text(f"{pname} Kullan"), content=ft.Column([txt_q, txt_p], height=100), actions=[ft.TextButton("Kullan", on_click=save)])
        self.page.open(dlg)

    def add_qty(self, pid, n): self.db.update_stock(pid, n); self.load_stock()
    def del_stock(self, pid): self.db.delete_product(pid); self.load_stock()

    def load_logs(self):
        self.log_list.controls.clear()
        for l in self.db.get_inventory_logs():
            p_info = f" -> Hasta: {l[3]}" if l[3] else ""
            self.log_list.controls.append(ft.ListTile(title=ft.Text(f"{l[1]} ({l[4]})"), subtitle=ft.Text(f"{l[0]} | {l[2]}{p_info}"), leading=ft.Icon("history")))
        
        if self.log_list.page:
            self.log_list.update()