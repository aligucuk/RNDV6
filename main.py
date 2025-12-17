import flet as ft
from database.db_manager import DatabaseManager
from utils.locales import TR
# Sayfalar
from pages.login import LoginPage
from pages.dashboard import DashboardPage
from pages.patients import PatientsPage
from pages.patient_list import PatientListPage
from pages.appointments import AppointmentsPage
from pages.all_appointments import AllAppointmentsPage
from pages.finance import FinancePage
from pages.calendar import CalendarPage
from pages.settings import SettingsPage
from pages.inventory import InventoryPage
from pages.stats import StatsPage
from pages.medical_detail import MedicalDetailPage
from pages.waiting_room import WaitingRoomPage
from pages.doctor_home import DoctorHomePage
from utils.license_manager import LicenseManager
from pages.activation import ActivationPage

def main(page: ft.Page):
    
    page.window_prevent_close = True  

    def window_event(e):
        if e.data == "close":
            
           page.window_destroy()
    page.on_window_event = window_event
    page.title = "RNDV4 Doktor Paneli"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    
    # ... Veritabanını Başlat ...
    db = DatabaseManager()
    
    # --- LİSANS KONTROLÜ (YENİ) ---
    lm = LicenseManager(db)
    is_licensed, license_msg = lm.check_license()
    
    # Başlangıç Rotasını Belirle
    initial_route = "/login" if is_licensed else "/activation"
    
    def route_change(e):
        # Rota Kontrolü (Router)
        troute = ft.TemplateRoute(page.route)

        # 1. Login
        if troute.match("/login"):
            page.views.append(LoginPage(page, db).view())
        
        # 2. Dashboard
        elif troute.match("/dashboard"):
            page.views.append(DashboardPage(page, db).view())

        # 3. Hastalar
        elif troute.match("/patient_list"):
            page.views.append(PatientListPage(page, db).view())
        elif troute.match("/patients/:id"):
            page.views.append(PatientsPage(page, db, int(troute.id)).view())
        elif troute.match("/patients"):
            page.views.append(PatientsPage(page, db).view())

        # 4. Randevular
        elif troute.match("/appointments"):
            page.views.append(AppointmentsPage(page, db).view())
        elif troute.match("/all_appointments"):
            page.views.append(AllAppointmentsPage(page, db).view())
            
        # 5. Diğer Modüller
        elif troute.match("/finance"):
            page.views.append(FinancePage(page, db).view())
        elif troute.match("/calendar"):
            page.views.append(CalendarPage(page, db).view())
        elif troute.match("/settings"):
            page.views.append(SettingsPage(page, db).view())
        elif troute.match("/inventory"):
            page.views.append(InventoryPage(page, db).view())
        elif troute.match("/stats"):
            page.views.append(StatsPage(page, db).view())
        # ... 
        elif troute.match("/activation"):
            page.views.append(ActivationPage(page, db).view())
        # ...
        # 6. Medikal Detay (3D Atlaslı)
        elif troute.match("/medical/:id"):
            page.views.append(MedicalDetailPage(page, db).view())

        # 7. YENİ: DOKTOR & TV EKRANLARI
        elif troute.match("/doctor_home"):
            page.views.append(DoctorHomePage(page, db).view())
        elif troute.match("/waiting_room"):
            page.views.append(WaitingRoomPage(page, db).view())
            
        # Varsayılan: Login
        else:
            page.go(initial_route)
            
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Başlangıç Rotası
    page.go(initial_route)

ft.app(target=main, assets_dir="assets")
