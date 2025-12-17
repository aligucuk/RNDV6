import flet as ft

class StatsPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db

    def view(self):
        # 1. Kaynak Analizi (Pasta Grafik)
        source_data = self.db.get_patient_sources()
        pie_sections = []
        colors = ["blue", "orange", "green", "red", "purple", "yellow"]
        
        if not source_data:
            pie_sections.append(ft.PieChartSection(100, title="Veri Yok", color="grey"))
        else:
            for i, (source, count) in enumerate(source_data):
                color = colors[i % len(colors)]
                pie_sections.append(
                    ft.PieChartSection(
                        count, 
                        title=f"{source}\n{count}", 
                        color=color, 
                        radius=100,
                        title_style=ft.TextStyle(size=12, weight="bold", color="white")
                    )
                )

        chart_source = ft.Container(
            content=ft.Column([
                ft.Text("Hasta Kaynakları (CRM)", size=16, weight="bold"),
                ft.PieChart(sections=pie_sections, sections_space=2, center_space_radius=40, expand=True)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=400, height=350, bgcolor="surface", padding=20, border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
        )

        # 2. Gelir Analizi (Bar Grafik - Basit Simülasyon)
        # Flet'in BarChart'ı biraz karmaşıktır, burada basitleştirilmiş bir liste görünümü yapacağız
        # veya basit "Progress Bar"lar ile çubuk grafik simüle edeceğiz.
        
        income_data = self.db.get_monthly_income_stats()
        bar_groups = []
        max_val = 1
        if income_data:
            max_val = max([val for date, val in income_data])
        
        bars_column = ft.Column(spacing=10)
        
        if not income_data:
            bars_column.controls.append(ft.Text("Henüz gelir verisi yok.", color="grey"))
        else:
            for date_str, amount in income_data:
                # Oran (0.0 - 1.0 arası)
                ratio = float(amount) / float(max_val) if max_val > 0 else 0
                
                bar_row = ft.Row([
                    ft.Text(date_str, width=80),
                    ft.ProgressBar(value=ratio, width=200, color="teal", bgcolor="grey200"),
                    ft.Text(f"{amount:.0f} ₺", weight="bold")
                ])
                bars_column.controls.append(bar_row)

        chart_income = ft.Container(
            content=ft.Column([
                ft.Text("Aylık Gelir Tablosu", size=16, weight="bold"),
                ft.Divider(),
                bars_column
            ]),
            width=400, height=350, bgcolor="surface", padding=20, border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
        )

        return ft.View(
            "/stats",
            [
                ft.AppBar(title=ft.Text("İstatistik & Raporlar"), bgcolor="background", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/dashboard"))),
                
                ft.Column([
                    ft.Container(height=20),
                    ft.Text("Klinik Performans Analizi", size=24, weight="bold", color="primary"),
                    ft.Container(height=20),
                    
                    ft.Row(
                        [chart_source, chart_income], 
                        alignment=ft.MainAxisAlignment.CENTER, 
                        wrap=True, spacing=20
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO, expand=True)
            ],
            bgcolor="background"
        )