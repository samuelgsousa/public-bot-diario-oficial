from selenium import webdriver
import os
from selenium.webdriver.chrome.options import Options
import platform
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager



def get_user_data_dir():
    if platform.system() == "Windows":
        print("Sistema operacional Windows")
        return os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data')
    elif platform.system() == "Darwin":  # macOS
        print("Sistema operacional macOS")
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:
        raise Exception("Sistema operacional não suportado")

def start_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-extensions")
    # options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36")
    
    # Identifica automaticamente o diretório do usuário do Chrome
    # user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data')
    user_data_dir = get_user_data_dir()
    # options.add_argument(f"--user-data-dir={user_data_dir}")
    # options.add_argument("--profile-directory=Default")
    
    
    prefs = {
        "download.default_directory": os.path.join(os.getcwd(), 'data'),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_settings.popups": 0,
         "profile.default_content_setting_values.automatic_downloads": 1,  # Permite downloads múltiplos
        # "safebrowsing.enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    
    
    # Usar a versão mais recente automaticamente
    driver_path = ChromeDriverManager().install()
    print(f"Driver baixado para: {driver_path}")
    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    
    return driver