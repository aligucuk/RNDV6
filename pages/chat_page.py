import flet as ft
import threading
import time

class ChatPage:
    def __init__(self, page: ft.Page, db):
        self.page = page
        self.db = db
        self.current_user_id = page.session.get("user_id")
        self.receiver_id = None
        self.receiver_name = ""
        self.is_active = True # Döngü aktif mi?
        
        # UI Elemanları
        self.user_list = ft.ListView(expand=True, spacing=5)
        self.chat_area = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)
        self.txt_message = ft.TextField(hint_text="Mesaj yazın...", expand=True, on_submit=self.send_message, border_radius=20)
        self.btn_send = ft.IconButton(icon=ft.Icons.SEND, icon_color="teal", on_click=self.send_message)
        self.chat_header = ft.Text("Sohbet Başlatmak için Kişi Seçin", size=16, weight="bold")

    def view(self):
        # Sayfa yüklenince listeyi getir
        self.load_users(initial=True)

        left_panel = ft.Container(
            content=ft.Column([
                ft.Text("Kişiler", size=18, weight="bold", color="teal"),
                ft.Divider(),
                self.user_list
            ]),
            width=250, bgcolor="white", padding=10, 
            border=ft.border.only(right=ft.BorderSide(1, "#eeeeee"))
        )

        right_panel = ft.Container(
            content=ft.Column([
                ft.Container(content=self.chat_header, padding=10, bgcolor="#f5f7f8", border_radius=10),
                ft.Container(content=self.chat_area, expand=True, padding=10),
                ft.Container(
                    content=ft.Row([self.txt_message, self.btn_send]),
                    padding=10, bgcolor="white", border=ft.border.only(top=ft.BorderSide(1, "#eeeeee"))
                )
            ]),
            expand=True, bgcolor="#f5f7f8"
        )

        # Arka plan dinleyicisini başlat
        threading.Thread(target=self.chat_listener, daemon=True).start()

        return ft.View(
            "/chat",
            [
                ft.AppBar(title=ft.Text("Ekip İletişimi"), bgcolor="teal", leading=ft.IconButton("arrow_back", on_click=self.go_back)),
                ft.Row([left_panel, right_panel], expand=True, spacing=0)
            ],
            padding=0
        )

    def go_back(self, e):
        self.is_active = False # Döngüyü durdur
        self.page.go("/doctor_home")

    def load_users(self, initial=False):
        users = self.db.get_users_except(self.current_user_id)
        self.user_list.controls.clear()
        
        if not users:
            self.user_list.controls.append(ft.Text("Kullanıcı yok.", color="grey"))
        
        for u in users:
            bg = "#e0f2f1" if self.receiver_id == u[0] else "white"
            self.user_list.controls.append(
                ft.ListTile(
                    leading=ft.CircleAvatar(content=ft.Text(u[3][0].upper()), bgcolor="orange" if u[2]=="doktor" else "blue"),
                    title=ft.Text(u[3], weight="bold"),
                    subtitle=ft.Text(u[2]),
                    on_click=lambda _, uid=u[0], uname=u[3]: self.select_user(uid, uname),
                    bgcolor=bg
                )
            )
        if not initial and self.user_list.page: self.user_list.update()

    def select_user(self, uid, uname):
        self.receiver_id = uid
        self.receiver_name = uname
        self.chat_header.value = f"Sohbet: {uname}"
        self.chat_header.update()
        self.load_users() # Seçim rengini güncelle
        self.load_messages() # Mesajları getir

    def load_messages(self):
        if not self.receiver_id: return
        
        # DB'den çek
        messages = self.db.get_chat_history(self.current_user_id, self.receiver_id)
        self.chat_area.controls.clear()
        
        if not messages:
            self.chat_area.controls.append(ft.Text("Henüz mesaj yok.", italic=True, color="grey", text_align="center"))
        
        for m in messages:
            # m: sender_id, text, timestamp
            is_me = (m[0] == self.current_user_id)
            align = ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START
            color = "teal" if is_me else "white"
            txt_col = "white" if is_me else "black"
            
            self.chat_area.controls.append(
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(m[1], color=txt_col),
                            ft.Text(m[2].strftime("%H:%M"), size=10, color="white70" if is_me else "grey")
                        ]),
                        bgcolor=color, padding=10, border_radius=10,
                        shadow=ft.BoxShadow(blur_radius=2, color="grey")
                    )
                ], alignment=align)
            )
        
        if self.chat_area.page:
            self.chat_area.update()
            try: self.chat_area.scroll_to(offset=-1, duration=300)
            except: pass

    def send_message(self, e):
        if self.receiver_id and self.txt_message.value:
            # DB'ye kaydet
            self.db.send_message(self.current_user_id, self.receiver_id, self.txt_message.value)
            
            self.txt_message.value = ""
            self.txt_message.focus()
            self.txt_message.update()
            
            # Anında ekranda göster
            self.load_messages()

    def chat_listener(self):
        """Arka planda mesajları kontrol et"""
        while self.is_active:
            if self.page.route == "/chat" and self.receiver_id:
                try:
                    # Basitlik adına her 3 saniyede bir UI yenile
                    # (Daha verimli yöntem: Sadece yeni mesaj varsa yenilemek, ama bu garanti çalışır)
                    if self.chat_area.page:
                        self.load_messages()
                except:
                    break
            time.sleep(3)