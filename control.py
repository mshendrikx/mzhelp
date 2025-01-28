import os

from seleniumbase import SB
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from project.common import get_db, only_numerics
from project.models import Mzcontrol

load_dotenv()

with SB(uc=True) as sb:
    sb.open("https://www.managerzone.com/")
    sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
    sb.type('input[id="login_username"]', os.environ.get("MZUSER"))
    sb.type('input[id="login_password"]', os.environ.get("MZPASS"))
    sb.click('a[id="login"]')
    
    driver = sb.driver
    season = 0
    try:
        
        text = driver.find_element(
                    By.XPATH, '//*[@id="header-stats-wrapper"]/h5[3]'
                ).text
        season = int(only_numerics(text.split('·')[0])) 
    except Exception as e:
        1 == 1

if season > 0:
    session = get_db()
    control = session.query(Mzcontrol).first()
    if control:
        control.season = season
        session.commit()