import time
import logging
import re
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Konfiqurasiya parametrləri
CONFIG = {
    "urls": [
        "https://www.ecanlitvizle.app/xezer-tv-canli-izle/",
        "https://www.ecanlitvizle.app/xezer-tv-canli-izle/3/"
    ],  # Kanalların siyahısını almaq üçün URL-lər
    "iframe_wait_time": 30,  # Iframe yüklənməsi üçün gözləmə vaxtı (saniyə)
    "video_wait_time": 60,  # Video elementinin yüklənməsi üçün gözləmə vaxtı (saniyə)
    "log_file": "multi_channels.txt",  # Linklərin yazılacağı fayl adı
}

# Logging konfiqurasiyası
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def setup_driver():
    """
    ChromeDriver-ı quraşdırır və başsız rejimdə başlatır.
    """
    options = Options()
    options.add_argument("--headless")  # Başsız rejim
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")  # Chrome log səviyyəsini azaltmaq
    options.add_argument("--disable-blink-features=AutomationControlled")  # Bot aşkarlanmasını azaltmaq
    options.add_argument("--window-size=1920,1080")  # Pəncərə ölçüsü
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    options.add_experimental_option('perfLoggingPrefs', {'enableNetwork': True})

    # ChromeDriver-i avtomatik yüklə və quraşdır
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(CONFIG["video_wait_time"])
    return driver


def extract_m3u8_links_from_javascript(driver):
    """
    JavaScript-dən `.m3u8` linklərini çıxarır.
    """
    try:
        script = """
        const scripts = document.querySelectorAll('script');
        let m3u8Links = [];
        scripts.forEach(script => {
            const text = script.textContent;
            if (text.includes('.m3u8')) {
                // Regex ile .m3u8 linklərini axtar
                const matches = text.match(/(https?:\/\/[^\s]+\.m3u8[^"]*)/g);
                if (matches) {
                    m3u8Links.push(...matches);
                }
            }
        });
        return m3u8Links;
        """
        m3u8_links = driver.execute_script(script)
        if m3u8_links:
            logging.info(f"JavaScript-dən {len(m3u8_links)} M3U8 linki tapıldı.")
            return set(m3u8_links)
        else:
            logging.warning("JavaScript-də M3U8 linki tapılmadı.")
            return set()
    except Exception as e:
        logging.error(f"JavaScript-dən M3U8 linklərini əldə edilərkən xəta: {e}")
        return set()


def get_m3u8_links_from_network_logs(driver):
    """
    Şəbəkə loglarından `.m3u8` linklərini tapır.
    """
    try:
        logs = driver.get_log("performance")
        m3u8_links = set()

        for entry in logs:
            log = json.loads(entry["message"])
            if "method" in log and log["method"] == "Network.requestWillBeSent":
                url = log["params"]["request"]["url"]
                if ".m3u8" in url:
                    logging.info(f"Şəbəkə loglarından M3U8 linki tapıldı: {url}")
                    m3u8_links.add(url)

        if m3u8_links:
            logging.info(f"Şəbəkə loglarından {len(m3u8_links)} M3U8 linki tapıldı.")
        else:
            logging.warning("Şəbəkə loglarında M3U8 linki tapılmadı.")

        return m3u8_links
    except Exception as e:
        logging.error(f"Şəbəkə loglarının analizində xəta: {e}")
        return set()


def fetch_m3u8_links_from_api(api_url, headers):
    """
    API reqestindən `.m3u8` linklərini alır.
    """
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # API-cərvəzində `.m3u8` linklərini axtar
            data = response.text
            m3u8_links = set(re.findall(r'(https?://[^\s]+\?tkn=[^&]+&tms=\d+)', data))
            if m3u8_links:
                logging.info(f"API-dən {len(m3u8_links)} M3U8 linki tapıldı.")
                return m3u8_links
            else:
                logging.warning("API-cərvəzində M3U8 linki tapılmadı.")
                return set()
        else:
            logging.warning(f"API reqesti uğursuz oldu ({response.status_code}).")
            return set()
    except Exception as e:
        logging.error(f"API reqestindən M3U8 linklərini əldə edilərkən xəta: {e}")
        return set()


def get_all_channel_links(driver, url):
    """
    Verilmiş URL-dən bütün kanalların `.m3u8` linklərini tapır.
    """
    try:
        driver.get(url)
        logging.info(f"Səhifə yükləndi: {url}")

        # İlkin `.m3u8` linklərini şəbəkə loglarından tap
        m3u8_links = get_m3u8_links_from_network_logs(driver)

        # Əgər linklər tapılmasa, JavaScript-dən axtar
        if not m3u8_links:
            m3u8_links.update(extract_m3u8_links_from_javascript(driver))

        # Əgər linklər hələ də tapılmasa, API reqestindən axtar
        if not m3u8_links:
            api_url = "https://platform-api.sharethis.com/js/sharethis.js"
            headers = {
                "Referer": url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            }
            m3u8_links.update(fetch_m3u8_links_from_api(api_url, headers))

        if m3u8_links:
            logging.info(f"{url} - Toplam {len(m3u8_links)} M3U8 linki tapıldı.")
        else:
            logging.warning(f"{url} - Heç bir M3U8 linki tapılmadı.")

        return list(m3u8_links)
    except Exception as e:
        logging.error(f"{url} - M3U8 linklərini əldə edilərkən xəta: {e}")
        return []


def update_m3u8_links_if_changed(new_links, file_path):
    """
    Yeni linklər varsa, `.txt` faylını güncəlləyir.
    """
    try:
        # Eski linkləri oxu
        try:
            with open(file_path, "r") as file:
                old_links = [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            old_links = []

        # Yeni linklər ilə müqayisə et
        if set(new_links) != set(old_links):
            logging.info("Linklər dəyişib, fayl güncəllənir.")
            with open(file_path, "w") as file:
                for link in new_links:
                    file.write(link + "\n")
            return True
        else:
            logging.info("Linklər dəyişmir, fayl aktualdır.")
            return False
    except Exception as e:
        logging.error(f"Fayl güncəllənilərkən xəta: {e}")
        return False


def main():
    """
    Ana funksiya: Bütün URL-lərdən `.m3u8` linklərini tapır və `.txt` faylına yazır.
    """
    # ChromeDriver setup
    driver = setup_driver()

    all_m3u8_links = []

    # Hər bir URL üçün `.m3u8` linklərini tap
    for url in CONFIG["urls"]:
        m3u8_links = get_all_channel_links(driver, url)
        all_m3u8_links.extend(m3u8_links)

    # Linklər tapıldısa fayl yaradılacaq
    if all_m3u8_links:
        updated = update_m3u8_links_if_changed(all_m3u8_links, CONFIG["log_file"])
        if updated:
            logging.info(f"{len(all_m3u8_links)} M3U8 linki fayla yazıldı: {CONFIG['log_file']}")
    else:
        logging.warning("Heç bir M3U8 linki tapılmadı, fayl boşdur.")

    # ChromeDriver-ı bağla
    driver.quit()


if __name__ == "__main__":
    main()
