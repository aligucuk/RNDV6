import flet as ft
import time
import threading

class WaitingRoomPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.running = True
        self.current_display = "" 

        # Ses oynatıcıyı tanımla
        self.audio_player = ft.Audio(src="assets/ding.mp3", autoplay=False)
        # Eğer sayfada yoksa ekle
        if self.audio_player not in page.overlay:
            page.overlay.append(self.audio_player)

    def start_polling(self):
        def poll():
            while self.running:
                # Eğer kullanıcı sayfadan ayrıldıysa döngüyü durdur
                if self.page.route != "/waiting_room":
                    self.running = False
                    break
                try:
                    self.check_database()
                    time.sleep(3)
                except:
                    break
        t = threading.Thread(target=poll, daemon=True)
        t.start()

    def check_database(self):
        record = self.db.get_current_patient()
        
        if record:
            p_name, dr_name = record
            parts = p_name.split()
            masked_name = ""
            # İsmi maskele (Örn: Ali -> A**)
            for p in parts:
                if len(p) > 2: masked_name += p[0] + "*" * (len(p)-1) + " "
                else: masked_name += p + " "
            
            if self.current_display == masked_name: return

            self.current_display = masked_name
            self.lbl_status.value = "İÇERİ GİRİNİZ"
            self.lbl_status.color = "green"
            self.lbl_patient.value = masked_name.strip()
            self.lbl_doctor.value = dr_name
            self.card_main.bgcolor = "#004d00"
            self.card_main.border = ft.border.all(5, "green")
            
            # Hastayı çağırma sesi
            self.audio_player.play()
            
        else:
            if self.current_display == "WAITING": return
            self.current_display = "WAITING"
            self.lbl_status.value = "BEKLEYİNİZ"
            self.lbl_status.color = "orange"
            self.lbl_patient.value = "Sıradaki Hasta..."
            self.lbl_doctor.value = "Lütfen Bekleyin"
            self.card_main.bgcolor = "#112233"
            self.card_main.border = None

        self.page.update()

    def view(self):
        self.lbl_status = ft.Text("BEKLEYİNİZ", size=40, color="orange", weight="bold")
        self.lbl_patient = ft.Text("Sıradaki Hasta...", size=70, color="white", weight="bold")
        self.lbl_doctor = ft.Text("...", size=35, color="cyan")
        
        self.card_main = ft.Container(
            content=ft.Column([
                self.lbl_status,
                ft.Divider(color="white"),
                self.lbl_patient,
                self.lbl_doctor,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#112233",
            border_radius=30,
            padding=50,
            alignment=ft.alignment.center,
            width=900, height=500,
            shadow=ft.BoxShadow(blur_radius=50, color="black"),
            
            # --- DÜZELTME BURADA YAPILDI ---
            # ft.animation.Animation yerine ft.Animation kullanıldı
            animate=ft.Animation(500, "easeOut")
        )
        
        self.start_polling()

        return ft.View(
            "/waiting_room",
            [
                ft.Column([
                    ft.Row([
                        ft.Icon("local_hospital", color="red", size=60), 
                        ft.Text("RNDV4 KLİNİK", size=40, color="white")
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(expand=True),
                    ft.Row([self.card_main], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(expand=True),
                    ft.Text("Lütfen randevu saatinizden 15 dk önce geliniz.", color="grey", size=20)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            ],
            bgcolor="black", padding=40
        )