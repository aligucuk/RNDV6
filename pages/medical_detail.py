import flet as ft
import base64
import os
import threading
import http.server
import socketserver
from utils.pdf_maker import create_prescription_pdf

# --- ARKA PLAN SUNUCUSU (Büyük Dosyalar İçin - DEĞİŞTİRMEYİN) ---
PORT = 8000
SERVER_STARTED = False

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    def log_message(self, format, *args): pass 
    def handle(self):
        try: super().handle()
        except: pass

def start_background_server():
    global SERVER_STARTED
    if SERVER_STARTED: return
    def serve():
        try:
            server = ThreadedHTTPServer(("", PORT), CORSRequestHandler)
            server.serve_forever()
        except OSError: pass
    t = threading.Thread(target=serve, daemon=True)
    t.start()
    SERVER_STARTED = True

start_background_server()

class MedicalDetailPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.patient_id = int(page.route.split("/")[-1])
        self.doctor_id = page.session.get("user_id")
        self.doctor_name = page.session.get("user_name")
        self.p_name = "" 

        self.current_mode = "body"
        self.gender = "male"
        self.show_muscles = False

        # --- HTML KODU ---
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>3D Atlas</title>
            <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
            <style>
                body { margin: 0; padding: 0; background-color: #ffffff; overflow: hidden; font-family: sans-serif; }
                model-viewer { width: 100vw; height: 100vh; outline: none; --poster-color: transparent; }
                #loading-bar {
                    position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
                    background: rgba(0,0,0,0.8); color: white; padding: 12px 24px; border-radius: 30px;
                    display: none; font-size: 14px; font-weight: bold; pointer-events: none;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: opacity 0.3s;
                }
            </style>
        </head>
        <body>
            <div id="loading-bar">Yükleniyor...</div>
            <model-viewer id="viewer" src="" camera-controls auto-rotate shadow-intensity="0" exposure="1" min-camera-orbit="auto auto 5%" max-camera-orbit="auto auto 100%"></model-viewer>
            <script>
                const viewer = document.querySelector("#viewer");
                const loading = document.querySelector("#loading-bar");
                window.changeModel = (modelUrl) => { 
                    loading.style.display = "block"; loading.innerText = "Yükleniyor..."; viewer.src = modelUrl; 
                };
                viewer.addEventListener('load', () => { loading.style.display = "none"; });
                viewer.addEventListener('progress', (e) => {
                    const progress = parseInt(e.detail.totalProgress * 100);
                    loading.innerText = "Yükleniyor: %" + progress;
                    if(progress >= 100) { setTimeout(() => { loading.style.display = "none"; }, 500); }
                });
                viewer.addEventListener('error', (e) => { loading.innerText = "HATA"; loading.style.backgroundColor = "#ff4444"; });
            </script>
        </body>
        </html>
        """
        b64_html = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        self.webview = ft.WebView(url=f"data:text/html;base64,{b64_html}", enable_javascript=True, expand=True, on_page_ended=lambda _: self.load_default_model())

        # --- BUTONLAR ---
        self.btn_body = ft.ElevatedButton("Tüm Vücut", icon="person", on_click=lambda _: self.set_mode("body"), bgcolor="teal", color="white")
        self.btn_skeleton = ft.ElevatedButton("İskelet", icon="grid_on", on_click=lambda _: self.set_mode("skeleton"))
        self.btn_teeth = ft.ElevatedButton("Diş", icon="sentiment_satisfied_alt", on_click=lambda _: self.set_mode("teeth"))

        self.sw_gender = ft.Switch(label="Kadın / Erkek", value=False, active_color="pink", inactive_thumb_color="blue", thumb_icon="male", on_change=self.update_state)
        self.sw_muscle = ft.Switch(label="Kas Sistemi", value=False, active_color="red", on_change=self.update_state)
        self.control_row = ft.Row([self.sw_gender, ft.VerticalDivider(width=10), self.sw_muscle], visible=True)

    # --- YARDIMCI TASARIM FONKSİYONU: GİRİŞ KARTI ---
    def create_input_card(self, label, icon_name, control, color="blue"):
        """Giriş alanlarını şık bir kart içine alır"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon_name, color=color),
                    ft.Text(label, weight="bold", color="grey", size=14)
                ]),
                ft.Container(height=5), # Boşluk
                control
            ]),
            padding=15,
            bgcolor="white",
            border_radius=10,
            border=ft.border.only(left=ft.BorderSide(5, color)), # Sol tarafa renkli çizgi
            shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.with_opacity(0.1, "black"))
        )

    def load_default_model(self): self.update_state()

    def update_state(self, e=None):
        self.gender = "female" if self.sw_gender.value else "male"
        self.show_muscles = self.sw_muscle.value
        self.sw_gender.thumb_icon = "female" if self.sw_gender.value else "male"
        self.sw_gender.update()

        filename = ""
        if self.current_mode == "skeleton":
            filename = "skeleton.glb"
            self.control_row.visible = False
            self.update_buttons(self.btn_skeleton)
        elif self.current_mode == "teeth":
            filename = "teeth.glb"
            self.control_row.visible = False
            self.update_buttons(self.btn_teeth)
        else:
            self.control_row.visible = True
            prefix = "muscle" if self.show_muscles else "body"
            filename = f"{prefix}_{self.gender}.glb"
            self.update_buttons(self.btn_body)

        self.control_row.update()
        self.load_model_file(filename)

    def update_buttons(self, active_btn):
        for btn in [self.btn_body, self.btn_skeleton, self.btn_teeth]: btn.bgcolor, btn.color = None, None
        active_btn.bgcolor, active_btn.color = "teal", "white"
        self.btn_body.update(); self.btn_skeleton.update(); self.btn_teeth.update()

    def set_mode(self, mode): self.current_mode = mode; self.update_state()

    def load_model_file(self, model_file):
        server_url = f"http://localhost:8000/assets/{model_file}"
        self.webview.run_javascript(f"changeModel('{server_url}')")

    def view(self):
        patient = self.db.get_patient_by_id(self.patient_id)
        if not patient: return ft.View("/dashboard", [ft.Text("Hasta Bulunamadı!")])
        self.p_name = patient[2] 

        # --- GİRİŞ ALANLARI (MODERN TASARIM) ---
        self.txt_complaint = ft.TextField(hint_text="Hastanın şikayetini buraya yazın...", multiline=True, min_lines=3, border=ft.InputBorder.NONE, text_size=14)
        self.txt_diagnosis = ft.TextField(hint_text="Konulan tanı...", border=ft.InputBorder.NONE, text_size=15, weight="bold", color="teal")
        self.txt_treatment = ft.TextField(hint_text="Uygulanan tedavi yöntemleri...", multiline=True, min_lines=2, border=ft.InputBorder.NONE, text_size=14)
        self.txt_presc = ft.TextField(hint_text="İlaç isimleri ve kullanım şekli...", multiline=True, min_lines=2, border=ft.InputBorder.NONE, text_size=14)
        
        # Kartları Oluştur
        card_complaint = self.create_input_card("Şikayet / Hikaye", "history", self.txt_complaint, "orange")
        card_diagnosis = self.create_input_card("Tanı (Teşhis)", "medical_services", self.txt_diagnosis, "red")
        card_treatment = self.create_input_card("Uygulanan Tedavi", "healing", self.txt_treatment, "blue")
        card_presc = self.create_input_card("Reçete / İlaçlar", "medication", self.txt_presc, "green")

        btn_save = ft.ElevatedButton("Muayeneyi Kaydet", icon="save", bgcolor="#2e7d32", color="white", height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), on_click=self.save_record)
        
        # Form Düzeni
        tab_form = ft.Column([
            ft.Text("Yeni Muayene Kaydı", size=22, weight="bold", color="#37474f"),
            ft.Divider(color="transparent", height=10),
            card_complaint,
            ft.Container(height=10),
            card_diagnosis,
            ft.Container(height=10),
            ft.Row([
                ft.Expanded(card_treatment),
                ft.Container(width=10),
                ft.Expanded(card_presc)
            ]),
            ft.Container(height=20),
            ft.Row([btn_save], alignment=ft.MainAxisAlignment.END)
        ], scroll=ft.ScrollMode.HIDDEN, expand=True)

        # Atlas Düzeni
        tab_atlas = ft.Column([
            ft.Container(
                content=ft.Row([
                    self.btn_body, self.btn_skeleton, self.btn_teeth,
                    ft.VerticalDivider(width=20),
                    self.control_row
                ], scroll=ft.ScrollMode.AUTO),
                padding=10, bgcolor="white", border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black"))
            ),
            ft.Container(content=self.webview, expand=True, border_radius=10, clip_behavior=ft.ClipBehavior.HARD_EDGE)
        ], expand=True)

        return ft.View(
            f"/medical/{self.patient_id}",
            [
                ft.AppBar(title=ft.Text(f"Dosya: {self.p_name}", weight="bold"), center_title=False, bgcolor="teal", color="white", leading=ft.IconButton("arrow_back", icon_color="white", on_click=lambda _: self.page.go("/doctor_home"))),
                ft.Container(
                    content=ft.Row([
                        # SOL PANEL: Form ve Atlas
                        ft.Container(
                            content=ft.Tabs(
                                selected_index=0,
                                animation_duration=300,
                                indicator_color="teal",
                                label_color="teal",
                                unselected_label_color="grey",
                                tabs=[
                                    ft.Tab(text="Muayene Formu", icon="edit_document", content=ft.Container(content=tab_form, padding=30, bgcolor="#f5f7f8")),
                                    ft.Tab(text="3D Atlas", icon="3d_rotation", content=ft.Container(content=tab_atlas, padding=20, bgcolor="#f5f7f8")),
                                ], expand=True
                            ),
                            expand=7, bgcolor="white", border_radius=0
                        ),
                        # SAĞ PANEL: Geçmiş (Koyu Tema)
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon("history", color="white"), ft.Text("Hasta Geçmişi", size=18, weight="bold", color="white")], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Divider(color="white54"),
                                self.build_history_list()
                            ], scroll=ft.ScrollMode.AUTO),
                            expand=3, padding=20, bgcolor="#263238"
                        )
                    ], spacing=0, expand=True),
                    expand=True
                )
            ],
            padding=0, # Sayfa kenar boşluklarını sıfırladık
            bgcolor="#f5f7f8"
        )

    def build_history_list(self):
        col = ft.Column(spacing=15)
        h_data = self.db.get_patient_history(self.patient_id)
        if h_data:
            for r in h_data:
                # Geçmiş verilerini şık kartlara çevirdik
                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(r[0].strftime("%d.%m.%Y"), weight="bold", color="teal", size=14),
                            ft.Icon("check_circle", size=16, color="green")
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10, color="grey"),
                        ft.Text(f"Tanı: {r[3]}", size=13, weight="w500"),
                        ft.Text(f"Tedavi: {r[4][:50]}..." if len(r[4])>50 else r[4], size=12, color="grey", italic=True)
                    ]),
                    padding=15, bgcolor="white", border_radius=10,
                    shadow=ft.BoxShadow(blur_radius=5, color="black")
                )
                col.controls.append(card)
        else:
            col.controls.append(ft.Container(content=ft.Text("Henüz geçmiş kayıt bulunmamaktadır.", color="white70", italic=True), alignment=ft.alignment.center, padding=20))
        return col

    def save_record(self, e):
        if self.db.add_medical_record(self.patient_id, self.doctor_id, self.txt_complaint.value, self.txt_diagnosis.value, self.txt_treatment.value, self.txt_presc.value):
            self.page.open(ft.SnackBar(ft.Text("Kayıt Başarılı!"), bgcolor="green"))
            self.page.go(f"/medical/{self.patient_id}")
        else: self.page.open(ft.SnackBar(ft.Text("Kayıt Sırasında Hata Oluştu"), bgcolor="red"))

    def print_pdf(self, e): pass