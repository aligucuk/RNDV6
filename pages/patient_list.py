import flet as ft

class PatientListPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        # Kullanıcı rolünü alıyoruz (Yetki kontrolü için)
        self.user_role = page.session.get("user_role")

    def view(self):
        patients = self.db.get_all_patients()
        rows = []
        for p in patients:
            # Veritabanından gelen veriyi ayrıştır
            # Sıra: id, tc, ad, tel, cinsiyet, d.tarihi, ...
            pid = p[0]
            tc = p[1]
            name = p[2]
            phone = p[3]
            bdate = p[5]
            
            bdate_str = bdate.strftime('%d-%m-%Y') if bdate else "-"
            
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(tc, color="onSurface")),
                ft.DataCell(ft.Text(name, weight="bold", color="onSurface")),
                ft.DataCell(ft.Text(phone, color="onSurface")),
                ft.DataCell(ft.Text(bdate_str, color="onSurfaceVariant")),
                # Düzenle butonu
                ft.DataCell(ft.IconButton(
                    icon="edit_square", 
                    icon_color="primary", 
                    tooltip="Detay/Düzenle", 
                    on_click=lambda e, x=pid: self.page.go(f"/patients/{x}")
                ))
            ]))

        # --- YETKİ KONTROLÜ ---
        # Eğer kullanıcı doktor ise "Yeni Hasta Ekle" (+) butonunu görmesin
        fab = None
        if self.user_role != "doktor":
            fab = ft.FloatingActionButton(
                icon="add", bgcolor="primary", 
                tooltip="Yeni Hasta Ekle",
                on_click=lambda _: self.page.go("/patients")
            )

        # Geri butonu nereye gidecek?
        # Doktor ise "Doktor Home"a, Yönetici/Sekreter ise "Dashboard"a dönsün
        back_route = "/doctor_home" if self.user_role == "doktor" else "/dashboard"

        return ft.View(
            "/patient_list",
            [
                ft.AppBar(
                    title=ft.Text("Hasta Listesi"), 
                    bgcolor="background", color="primary", 
                    leading=ft.IconButton("arrow_back", icon_color="primary", on_click=lambda _: self.page.go(back_route))
                ),
                
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon("people", size=30, color="primary"),
                                    ft.Text("Kayıtlı Hastalar", size=24, weight="bold", color="primary")
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                
                                ft.Container(height=10),
                                # Arama Çubuğu
                                ft.TextField(
                                    label="Hasta Ara (Ad veya TC)...", prefix_icon="search", 
                                    height=40, content_padding=10, border_radius=10, width=400
                                ),
                                ft.Divider(),
                                
                                # Tablo
                                ft.Container(
                                    content=ft.DataTable(
                                        columns=[
                                            ft.DataColumn(ft.Text("TC Kimlik", color="primary")),
                                            ft.DataColumn(ft.Text("Ad Soyad", color="primary")),
                                            ft.DataColumn(ft.Text("Telefon", color="primary")),
                                            ft.DataColumn(ft.Text("D. Tarihi", color="primary")),
                                            ft.DataColumn(ft.Text("İşlem", color="primary")),
                                        ],
                                        rows=rows, heading_row_color="surfaceVariant", data_row_min_height=50,
                                    ),
                                    bgcolor="surface", border_radius=10, padding=10, shadow=ft.BoxShadow(blur_radius=10, color="#1A000000"),
                                    alignment=ft.alignment.center
                                )
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=20, alignment=ft.alignment.center
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            ],
            floating_action_button=fab, # Rol'e göre buton
            bgcolor="background"
        )