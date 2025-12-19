import flet as ft
import base64
import threading
import http.server
import socketserver
import os
import shutil
from utils.pdf_maker import create_prescription_pdf

# --- SUNUCU ---
PORT = 8000
SERVER_STARTED = False

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads = True
class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    def log_message(self, format, *args): pass 

def start_server():
    global SERVER_STARTED
    if not SERVER_STARTED:
        try:
            server = ThreadedHTTPServer(("", PORT), CORSRequestHandler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            SERVER_STARTED = True
        except: pass
start_server()

class MedicalDetailPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        try: self.patient_id = int(page.route.split("/")[-1])
        except: self.patient_id = 0
        self.doctor_id = page.session.get("user_id")
        self.doctor_name = page.session.get("user_name")
        
        self.mode = "body"
        self.gender = "male"
        self.muscle = False
        
        self.file_picker = ft.FilePicker(on_result=self.upload_file)
        self.page.overlay.append(self.file_picker)

        html = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script><style>body{margin:0;overflow:hidden;background:#222}model-viewer{width:100%;height:100vh;outline:none;--poster-color:transparent}</style></head><body><model-viewer id="viewer" src="" camera-controls auto-rotate shadow-intensity="1.5" ar></model-viewer><script>const v=document.querySelector("#viewer");window.changeModel=(u)=>{v.src=u;}</script></body></html>"""
        self.wv = ft.WebView(url=f"data:text/html;base64,{base64.b64encode(html.encode()).decode()}", expand=True, on_page_ended=lambda _: self.update_model())

    def update_model(self, e=None):
        is_body = (self.mode == "body")
        self.switch_gender.visible = is_body
        self.switch_muscle.visible = is_body
        self.switch_gender.update()
        self.switch_muscle.update()

        filename = ""
        if self.mode == "skeleton": filename = "skeleton.glb"
        elif self.mode == "teeth": filename = "teeth.glb"
        else:
            t = "muscle" if self.switch_muscle.value else "body"
            g = "female" if self.switch_gender.value else "male"
            filename = f"{t}_{g}.glb"
        
        self.wv.run_javascript(f"changeModel('http://localhost:{PORT}/assets/{filename}')")

    def upload_file(self, e: ft.FilePickerResultEvent):
        if e.files:
            f = e.files[0]
            dest = f"assets/uploads/{f.name}"
            os.makedirs("assets/uploads", exist_ok=True)
            shutil.copy(f.path, dest)
            self.db.add_patient_file(self.patient_id, f.name, dest, "MR/Röntgen")
            self.page.open(ft.SnackBar(ft.Text("Dosya Yüklendi"), bgcolor="green"))
            self.refresh_files()

    def refresh_files(self):
        self.files_list.controls.clear()
        files = self.db.get_patient_files(self.patient_id)
        for fi in files:
            self.files_list.controls.append(ft.ListTile(leading=ft.Icon("image"), title=ft.Text(fi[1]), subtitle=ft.Text(str(fi[4]))))
        self.files_list.update()

    def view(self):
        p = self.db.get_patient_by_id(self.patient_id)
        p_name = p[2] if p else "Bilinmiyor"

        # SEKME 1: MUAYENE
        self.txt_anamnez = ft.TextField(label="Anamnez (Hikaye)", multiline=True, min_lines=3)
        self.txt_diagnosis = ft.TextField(label="Tanı")
        self.txt_treatment = ft.TextField(label="Tedavi", multiline=True)
        self.txt_presc = ft.TextField(label="Reçete", icon="medication", multiline=True)
        btn_save = ft.ElevatedButton("Kaydet", icon="save", bgcolor="green", color="white", on_click=self.save_record)
        btn_pdf = ft.ElevatedButton("PDF", icon="print", bgcolor="blue", color="white", on_click=self.print_pdf)

        tab_exam = ft.Container(content=ft.Column([
            ft.Text("Muayene Formu", size=20, weight="bold"),
            self.txt_anamnez, self.txt_diagnosis, self.txt_treatment, self.txt_presc,
            ft.Row([btn_save, btn_pdf])
        ], scroll=ft.ScrollMode.AUTO), padding=20)

        # SEKME 2: 3D ATLAS
        self.switch_gender = ft.Switch(label="Kadın", active_color="pink", on_change=self.update_model)
        self.switch_muscle = ft.Switch(label="Kas", active_color="red", on_change=self.update_model)
        
        ctrl_row = ft.Row([
            ft.ElevatedButton("Vücut", on_click=lambda _: setattr(self, 'mode', 'body') or self.update_model()),
            ft.ElevatedButton("İskelet", on_click=lambda _: setattr(self, 'mode', 'skeleton') or self.update_model()),
            ft.ElevatedButton("Diş", on_click=lambda _: setattr(self, 'mode', 'teeth') or self.update_model()),
            self.switch_gender, self.switch_muscle
        ], alignment=ft.MainAxisAlignment.CENTER)

        tab_atlas = ft.Column([
            ft.Container(content=ctrl_row, padding=10, bgcolor="surfaceVariant"),
            ft.Container(content=self.wv, expand=True)
        ])

        # SEKME 3: GEÇMİŞ
        self.files_list = ft.Column()
        history_col = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO) # Scroll burada
        hist = self.db.get_patient_history(self.patient_id)
        if hist:
            for h in hist:
                history_col.controls.append(ft.Container(content=ft.Column([ft.Text(f"{h[0].strftime('%d.%m.%Y')} - {h[3]}", weight="bold"), ft.Text(h[5], italic=True)]), padding=10, bgcolor="white", border_radius=5))
        
        tab_history = ft.Column([
            ft.Text("Geçmiş Muayeneler", weight="bold"),
            # HATA DÜZELTME: overflow kaldırıldı
            ft.Container(content=history_col, height=200, border=ft.border.all(1, "grey")),
            ft.Divider(),
            ft.Text("Dosyalar (MR / Röntgen)", weight="bold"),
            ft.ElevatedButton("Dosya Yükle", icon="upload", on_click=lambda _: self.file_picker.pick_files()),
            self.files_list
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Muayene", icon="edit_document", content=tab_exam),
                ft.Tab(text="3D Atlas", icon="accessibility_new", content=tab_atlas),
                ft.Tab(text="Geçmiş & Dosyalar", icon="folder_open", content=tab_history),
            ],
            expand=True
        )

        return ft.View(
            f"/medical/{self.patient_id}",
            [
                ft.AppBar(title=ft.Text(f"Dosya: {p_name}"), bgcolor="teal", leading=ft.IconButton("arrow_back", on_click=lambda _: self.page.go("/doctor_home"))),
                tabs
            ]
        )

    def save_record(self, e):
        if not self.txt_diagnosis.value: return
        self.db.add_medical_record(self.patient_id, self.doctor_id, self.txt_anamnez.value, self.txt_diagnosis.value, self.txt_treatment.value, self.txt_presc.value, None, None, None)
        self.page.open(ft.SnackBar(ft.Text("Kaydedildi"), bgcolor="green"))

    def print_pdf(self, e):
        pass