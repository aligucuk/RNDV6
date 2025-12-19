from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import psycopg2
from datetime import datetime, timedelta

# DB Ayarları
DB_CONN = "dbname='klinik_db' user='postgres' password='1234' host='localhost'"

def get_tomorrow_appointments():
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Yarınki randevular
    cur.execute("""
        SELECT p.phone, p.full_name, a.appointment_date 
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.id 
        WHERE DATE(a.appointment_date) = %s AND a.status = 'Bekliyor'
    """, (tomorrow,))
    return cur.fetchall()

def send_whatsapp_messages():
    apps = get_tomorrow_appointments()
    if not apps:
        print("Yarına randevu yok.")
        return

    print("WhatsApp Başlatılıyor (QR Kodu Okutun)...")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Arka planda çalışması için (QR okuttuktan sonra açılabilir)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://web.whatsapp.com")
    
    input("QR Kodu okuttuysanız ENTER'a basın...")

    for phone, name, date in apps:
        try:
            time_str = date.strftime("%H:%M")
            msg = f"Merhaba Sayın {name}, yarın saat {time_str} randevunuzu hatırlatırız. - RNDV6 Klinik"
            
            # WhatsApp Web Linki (API kullanmadan)
            url = f"https://web.whatsapp.com/send?phone={phone}&text={msg}"
            driver.get(url)
            time.sleep(10) # Sayfa yüklenmesi için bekle
            
            # Enter'a basıp gönder (Bu kısım class name'e göre değişebilir, Selenium ile 'Send Button' bulunur)
            # Web scraping risklidir, Whatsapp class isimlerini sürekli değiştirir.
            # En güvenlisi:
            webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
            time.sleep(5)
            print(f"Gönderildi: {name}")
            
        except Exception as e:
            print(f"Hata ({name}): {e}")

    driver.quit()

if __name__ == "__main__":
    send_whatsapp_messages()