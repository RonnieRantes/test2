from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service 
from webdriver_manager.chrome import ChromeDriverManager
import selenium.webdriver.support.expected_conditions as ec
import undetected_chromedriver as uc
import requests

from time import sleep

#CONFIG
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'

woptions = Options()
woptions.page_load_strategy = 'eager'
woptions.add_argument("start-maximized")
#woptions.add_argument('--headless=new')
woptions.add_argument("--ignore-certificate-errors")
woptions.add_argument("--allow-running-insecure-content")
woptions.add_argument(f'user-agent={user_agent}')
woptions.add_argument('--disable-blink-features=AutomationControlled')
woptions.add_experimental_option("excludeSwitches", ["enable-automation"])
woptions.add_experimental_option('excludeSwitches', ['enable-logging'])
woptions.add_experimental_option('useAutomationExtension', False)

'''
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-extensions")
options.add_argument("--proxy-server='direct://'")
options.add_argument("--proxy-bypass-list=*")
options.add_argument("--start-maximized")
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
'''


options  = uc.ChromeOptions()
uc.ChromeOptions.page_load_strategy = 'eager'
options.add_argument("--headless")
options.add_argument(f'--user-agent={user_agent}')
driver = uc.Chrome(options=options)
#driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=woptions) 
driver.set_script_timeout(10)

#
'''
print("Cargando web...")
driver.get("https://ruc.pe/consulta/")
print("Web cargada!")
'''
wait = WebDriverWait(driver, 10)


def rerun():
    driver.delete_all_cookies()
    driver.refresh()

def buscarRUC(ruc):
    #Buscar ruc
    try:
        wait.until(ec.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@src='https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp']")))
        driver.find_element(By.ID,"txtRuc").send_keys(ruc)
        print("RUC ingresado")
    except:
        print("ERROR: RUC no ingresado")
        driver.save_screenshot("INGRESAR_RUC.png")
        rerun()
        return buscarRUC(ruc)

    sleep(1)
    try:
        wait.until(ec.element_to_be_clickable((By.ID,"btnAceptar")))
        driver.find_element(By.ID,"btnAceptar").send_keys(Keys.ENTER,Keys.ENTER,Keys.ENTER)
        print("Boton clickeado")
    except:
        print("ERROR: Boton no clickeado")
        driver.save_screenshot("CLICK BOTON.png")
        rerun()
        return buscarRUC(ruc)
        
    sleep(1)
    #Scrap
    driver._switch_to.default_content()
    try:
        wait.until(ec.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@src='https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp']")))
        print("Frame con data cargado")
    except:
        print("ERROR: Frame con data no cargado")
        driver.save_screenshot("CAMBIO_FRAME.png")
        driver.back()
        rerun()
        return buscarRUC(ruc)

    sleep(1)
    try:
        wait.until(ec.presence_of_element_located((By.XPATH,"//div[@class='list-group-item']")))
        scrap = driver.find_elements(By.XPATH,"//div[contains(@class,'list-group-item')]//div[@class='col-sm-7']//p")
        print("Data obtenida")
    except:
        print("ERROR: Data no obtenida")
        driver.save_screenshot("OBTENER_DETALLE.png")
        driver.back()
        rerun()
        return buscarRUC(ruc)

    
    #Output
    lst = list()
    for idx,r in enumerate(scrap):
        if idx in range(1,5): lst.append(r.text)

    driver.back()
    rerun()

    out = '|'.join(lst)
    return out

def buscarRUCAPI(ruc):
    URL = "https://api.sunat.dev/ruc/" + ruc + "?apikey=wXQRSOaC7DbfnHQUsuYBFqnJ2BUxNGyhNMnhcWpDYpXL0ck4TcvDLhkoZjCLVEhG"
    data = requests.get(url = URL).json()["body"]["datosContribuyente"]

    out = data["desRazonSocial"] + "|" + data["codEstado"] + "|" + data["codDomHabido"] + "|" + " ".join(data["desDireccion"].split())
    return out