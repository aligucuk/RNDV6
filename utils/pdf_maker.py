from fpdf import FPDF
import datetime
import os

class PDFReport(FPDF):
    def header(self):
        # Logo (Eğer assets klasöründe logo.png varsa kullanır, yoksa hata vermez)
        if os.path.exists("assets/logo.png"):
            self.image("assets/logo.png", 10, 8, 33)
        
        self.set_font('Arial', 'B', 15)
        # Türkçe karakter sorunu olmaması için encode/latin-1 hilesi veya font yükleme gerekir.
        # FPDF'in standart fontları Türkçe karakter (ş,ğ,İ) desteklemez.
        # Bu yüzden basit ASCII karakterler veya Windows fontu yüklemek gerekir.
        # Profesyonel çözüm için 'DejaVuSans.ttf' indirip add_font yapmak gerekir.
        # Şimdilik "tr_chars" fonksiyonu ile harfleri dönüştüreceğiz.
        
        self.cell(80) # Sağa kaydır
        self.cell(30, 10, 'RNDV4 KLINIK SISTEMI', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

def tr_chars(text):
    """Türkçe karakterleri FPDF'in anlayacağı formata çevirir"""
    # Basit FPDF sürümlerinde Türkçe karakter sorunu vardır.
    # Bu basit değişim harfleri okunur hale getirir.
    replacements = {
        "ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S", "ı": "i", "İ": "I",
        "ü": "u", "Ü": "U", "ö": "o", "Ö": "O", "ç": "c", "Ç": "C"
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    return text

def create_prescription_pdf(doctor_name, patient_name, diagnosis, prescription):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Tarih
    date_str = datetime.date.today().strftime("%d.%m.%Y")
    pdf.cell(0, 10, f"Tarih: {date_str}", 0, 1, 'R')
    
    # Başlık
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "RECETE / MUAYENE RAPORU", 0, 1, 'C')
    pdf.ln(10)
    
    # Hasta ve Doktor Bilgisi
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, tr_chars(f"Sayin Dr. {doctor_name}"), 0, 1)
    pdf.cell(0, 10, tr_chars(f"Hasta: {patient_name}"), 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Çizgi çek
    pdf.ln(10)
    
    # Tanı
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, tr_chars("TANI (TESHIS):"), 0, 1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, tr_chars(diagnosis))
    pdf.ln(5)
    
    # Reçete / Tedavi
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, tr_chars("RECETE / TEDAVI:"), 0, 1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, tr_chars(prescription))
    
    # İmza Bloğu
    pdf.set_y(-50)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "Kase / Imza", 0, 1, 'R')
    
    # Dosyayı Kaydet
    filename = f"recete_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
    pdf.output(filename)
    
    # Dosyayı Otomatik Aç (Windows/Mac)
    try:
        if os.name == 'nt': # Windows
            os.startfile(filename)
        else: # Mac/Linux
            os.system(f"open {filename}")
    except:
        pass
        
    return filename