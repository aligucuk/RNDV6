import flet as ft
from database.db_manager import DatabaseManager

# SAYFA IMPORTLARI
from pages.login import LoginPage
from pages.doctor_home import DoctorHomePage
from pages.patients import PatientsPage       
from pages.appointments import AppointmentsPage
from pages.medical_detail import MedicalDetailPage
from pages.finance import FinancePage
from pages.inventory import InventoryPage
from pages.settings import SettingsPage
from pages.chat_page import ChatPage
from pages.calendar_page import CalendarPage
from pages.tv_display import TVDisplayPage
from utils.notification_service import NotificationService

def main(page: ft.Page):
    page.title = "RNDV6 Klinik Yönetim Sistemi"
    
    db = DatabaseManager()
    
    # --- BİLDİRİM SERVİSİNİ BAŞLAT ---
    notif_service = NotificationService(db)
    notif_service.start()

    # --- TEMA YÜKLEME (GLOBAL ETKİ) ---
    def load_theme():
        saved_theme = db.get_setting("theme_mode")
        saved_color = db.get_setting("theme_color") or "teal"
        
        page.theme_mode = ft.ThemeMode.DARK if saved_theme == "dark" else ft.ThemeMode.LIGHT
        page.theme = ft.Theme(color_scheme_seed=saved_color)
        page.update()

    # Başlarken yükle
    load_theme()

    # --- GLOBAL CHAT OVERLAY ---
    # Bu Stack tüm sayfaların üstünde duracak
    chat_window = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([ft.Text("Sohbet", color="white"), ft.IconButton(ft.Icons.CLOSE, icon_color="white", icon_size=15, on_click=lambda e: toggle_chat(False))]), 
                bgcolor="teal", padding=5
            ),
            ft.Container(content=ft.Text("Sohbet yükleniyor..."), expand=True, bgcolor="white") # Buraya ChatPage içeriği (küçültülmüş) gelebilir
        ]),
        width=300, height=400, bgcolor="white", border_radius=10,
        shadow=ft.BoxShadow(blur_radius=20, color="black"),
        bottom=10, right=20, visible=False # Başlangıçta gizli
    )
    
    page.overlay.append(chat_window) # Sayfanın en üst katmanına ekle

    def toggle_chat(show):
        chat_window.visible = show
        chat_window.update()

    # Chat butonuna basınca sayfaya gitmek yerine popup açsın:
    # DoctorHome ve diğer sayfalardaki chat butonu aksiyonunu değiştirmelisiniz.
    # Ancak Flet'te sayfalar arası fonksiyon çağırmak için 'pubsub' kullanmak en temizidir.
    
    def on_broadcast_message(msg):
        if msg == "OPEN_CHAT_POPUP":
            toggle_chat(True)
    
    page.pubsub.subscribe(on_broadcast_message)

    def route_change(route):
        # Her sayfa değişiminde temayı zorla (Sayfalar arası geçişte renk kaybı olmasın)
        load_theme()
        
        page.views.clear()
        troute = ft.TemplateRoute(page.route)

        if page.route == "/" or troute.match("/login"):
            page.views.append(LoginPage(page, db).view())
        elif troute.match("/doctor_home"):
            page.views.append(DoctorHomePage(page, db).view())
        elif troute.match("/patient_list"):
            page.views.append(PatientsPage(page, db).view())
        elif troute.match("/appointments"):
            page.views.append(AppointmentsPage(page, db).view())
        elif troute.match("/medical/:id"):
            page.views.append(MedicalDetailPage(page, db).view())
        elif troute.match("/finance"):
            page.views.append(FinancePage(page, db).view())
        elif troute.match("/inventory"):
            page.views.append(InventoryPage(page, db).view())
        elif troute.match("/settings"):
            page.views.append(SettingsPage(page, db).view())
        elif troute.match("/chat"):
            page.views.append(ChatPage(page, db).view())
        elif troute.match("/calendar"):
            page.views.append(CalendarPage(page, db).view())
        elif troute.match("/tv"):
            page.views.append(TVDisplayPage(page, db).view())

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    page.go("/")

if __name__ == "__main__":
    ft.app(target=main)