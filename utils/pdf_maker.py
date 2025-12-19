import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

class PDFManager:
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=A4)
        self.width, self.height = A4
        self._register_fonts()

    def _register_fonts(self):
        """Türkçe karakter destekleyen fontları kaydeder."""
        # Windows/Linux sistem fontlarını dener, yoksa standart font kullanır
        try:
            # Genellikle Windows'ta bulunan Arial fontu
            if os.name == 'nt':
                pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
                self.font_reg = 'Arial'
                self.font_bold = 'Arial-Bold'
            else:
                # Linux/Mac için alternatif (Sistemde yüklü olmalı veya assets'e eklenmeli)
                # Şimdilik standart Helvetica kullanıyoruz (TR karakter sorunu olabilir)
                # Doğrusu: assets klasörüne bir .ttf dosyası koyup onu yüklemektir.
                self.font_reg = 'Helvetica'
                self.font_bold = 'Helvetica-Bold'
        except:
            self.font_reg = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

    def create_header(self):
        # Logo
        if os.path.exists("assets/logo.png"):
            self.c.drawImage("assets/logo.png", 10*mm, 270*mm, width=30*mm, preserveAspectRatio=True, mask='auto')

        # Başlıklar
        self.c.setFont(self.font_bold, 18)
        self.c.drawRightString(200*mm, 280*mm, "RNDV5 KLİNİK SİSTEMİ")
        
        self.c.setFont(self.font_reg, 10)
        self.c.drawRightString(200*mm, 275*mm, f"Tarih: {datetime.date.today().strftime('%d.%m.%Y')}")
        
        # Çizgi
        self.c.setStrokeColor(colors.teal)
        self.c.setLineWidth(1)
        self.c.line(10*mm, 265*mm, 200*mm, 265*mm)

    def create_patient_info(self, doctor_name, patient_name):
        self.c.setStrokeColor(colors.black)
        y = 250*mm
        
        self.c.setFont(self.font_bold, 12)
        self.c.drawString(15*mm, y, "DOKTOR:")
        self.c.setFont(self.font_reg, 12)
        self.c.drawString(45*mm, y, f"Dr. {doctor_name}")
        
        y -= 10*mm
        self.c.setFont(self.font_bold, 12)
        self.c.drawString(15*mm, y, "HASTA:")
        self.c.setFont(self.font_reg, 12)
        self.c.drawString(45*mm, y, patient_name)

    def create_body(self, diagnosis, prescription):
        # Tanı Alanı
        y = 220*mm
        self.c.setFillColor(colors.teal)
        self.c.rect(10*mm, y, 190*mm, 8*mm, fill=1, stroke=0)
        self.c.setFillColor(colors.white)
        self.c.setFont(self.font_bold, 12)
        self.c.drawString(15*mm, y+2*mm, "TANI (TEŞHİS)")
        
        self.c.setFillColor(colors.black)
        self.c.setFont(self.font_reg, 11)
        
        # Metni sarmalamak (Text Wrapping) için basit çözüm
        text_object = self.c.beginText(15*mm, y-6*mm)
        text_object.setFont(self.font_reg, 11)
        text_object.textLines(diagnosis)
        self.c.drawText(text_object)
        
        # Reçete Alanı
        y = 180*mm
        self.c.setFillColor(colors.teal)
        self.c.rect(10*mm, y, 190*mm, 8*mm, fill=1, stroke=0)
        self.c.setFillColor(colors.white)
        self.c.setFont(self.font_bold, 12)
        self.c.drawString(15*mm, y+2*mm, "REÇETE / TEDAVİ PLANI")
        
        self.c.setFillColor(colors.black)
        self.c.setFont(self.font_reg, 11)
        
        text_object = self.c.beginText(15*mm, y-6*mm)
        text_object.textLines(prescription)
        self.c.drawText(text_object)

    def create_footer(self):
        # İmza Alanı
        self.c.setDash(3, 3) # Kesik çizgi
        self.c.line(130*mm, 40*mm, 190*mm, 40*mm)
        self.c.setFont(self.font_reg, 10)
        self.c.drawCentredString(160*mm, 35*mm, "Kaşe / İmza")
        
        # Karekod (Placeholder)
        self.c.setDash(1, 0) # Düz çizgiye dön
        self.c.rect(10*mm, 10*mm, 25*mm, 25*mm)
        self.c.setFont(self.font_reg, 8)
        self.c.drawCentredString(22.5*mm, 20*mm, "e-Reçete QR")

    def save(self):
        self.c.save()
        return self.filename

def create_prescription_pdf(doctor_name, patient_name, diagnosis, prescription):
    """Eski fonksiyon ile uyumlu sarmalayıcı (wrapper)"""
    filename = f"recete_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
    
    pdf = PDFManager(filename)
    pdf.create_header()
    pdf.create_patient_info(doctor_name, patient_name)
    pdf.create_body(diagnosis, prescription)
    pdf.create_footer()
    pdf.save()
    
    # Dosyayı Otomatik Aç
    try:
        if os.name == 'nt': os.startfile(filename)
        else: os.system(f"open {filename}")
    except: pass
    
    return filename