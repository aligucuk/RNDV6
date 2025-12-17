import flet as ft

class InventoryPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

    def view(self):
        # --- Ürün Ekleme Formu ---
        self.txt_name = ft.TextField(label="Ürün Adı (Örn: Botox)", width=200, border_radius=10)
        self.dd_unit = ft.Dropdown(
            label="Birim", width=100, 
            options=[ft.dropdown.Option("Adet"), ft.dropdown.Option("Kutu"), ft.dropdown.Option("ML")],
            border_radius=10, value="Adet"
        )
        self.txt_qty = ft.TextField(label="Mevcut Stok", width=100, value="0", keyboard_type="number", border_radius=10)
        self.txt_crit = ft.TextField(label="Kritik Sınır", width=100, value="10", keyboard_type="number", border_radius=10)
        
        btn_add = ft.ElevatedButton("Ürün Ekle", icon="add", bgcolor="green", color="white", on_click=self.add_product_click)

        # --- Stok Listesi ---
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Ürün Adı")),
                ft.DataColumn(ft.Text("Stok Durumu")),
                ft.DataColumn(ft.Text("Birim")),
                ft.DataColumn(ft.Text("Hızlı İşlem")),
                ft.DataColumn(ft.Text("Sil")),
            ],
            width=800,
            heading_row_color="surfaceVariant",
        )
        
        self.refresh_table()

        return ft.View(
            "/inventory",
            [
                ft.AppBar(title=ft.Text("Stok & Envanter Takibi"), bgcolor="background", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/dashboard"))),
                
                ft.Column(
                    controls=[
                        # Ekleme Paneli
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Yeni Malzeme Girişi", size=18, weight="bold", color="primary"),
                                ft.Row([self.txt_name, self.dd_unit, self.txt_qty, self.txt_crit, btn_add], alignment=ft.MainAxisAlignment.CENTER)
                            ]),
                            padding=20, bgcolor="surfaceVariant", border_radius=15
                        ),
                        
                        ft.Divider(),
                        
                        # Liste
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Mevcut Envanter", size=20, weight="bold"),
                                ft.Text("* Kırmızı: Kritik seviyenin altında!", size=12, color="red"),
                                self.data_table
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=20
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            ], bgcolor="background"
        )

    def refresh_table(self):
        self.data_table.rows.clear()
        products = self.db.get_inventory()
        
        if not products:
            self.data_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text("Henüz ürün yok.")) for _ in range(5)]))
        
        for p in products:
            pid, name, unit, qty, crit = p
            
            # Kritik Seviye Kontrolü
            is_critical = qty <= crit
            text_color = "red" if is_critical else "green"
            status_text = f"{qty} (KRİTİK!)" if is_critical else str(qty)
            
            self.data_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(name, weight="bold")),
                ft.DataCell(ft.Text(status_text, color=text_color, weight="bold", size=16)),
                ft.DataCell(ft.Text(unit)),
                ft.DataCell(ft.Row([
                    ft.IconButton("remove_circle", icon_color="red", tooltip="-1 Düş", on_click=lambda e, x=pid: self.update_stock(x, -1)),
                    ft.IconButton("add_circle", icon_color="green", tooltip="+1 Ekle", on_click=lambda e, x=pid: self.update_stock(x, 1)),
                ])),
                ft.DataCell(ft.IconButton("delete", icon_color="grey", on_click=lambda e, x=pid: self.delete_product(x)))
            ]))
        self.page.update()

    def add_product_click(self, e):
        if not self.txt_name.value: return
        try:
            qty = int(self.txt_qty.value)
            crit = int(self.txt_crit.value)
            if self.db.add_product(self.txt_name.value, self.dd_unit.value, qty, crit):
                self.page.open(ft.SnackBar(ft.Text("Ürün Eklendi"), bgcolor="green"))
                self.txt_name.value = ""
                self.refresh_table()
            else:
                self.page.open(ft.SnackBar(ft.Text("Hata!"), bgcolor="red"))
        except:
             self.page.open(ft.SnackBar(ft.Text("Sayısal değer giriniz!"), bgcolor="red"))

    def update_stock(self, pid, change):
        self.db.update_stock(pid, change)
        self.refresh_table()

    def delete_product(self, pid):
        self.db.delete_product(pid)
        self.refresh_table()