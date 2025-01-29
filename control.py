import os

from seleniumbase import BaseCase
#from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
#from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from project.common import get_db, only_numerics
from project.models import Mzcontrol
from bs4 import BeautifulSoup

from project.models import Countries

load_dotenv()

class Managerzone(BaseCase):
    def general_control(self):       

        # Determine Season
        self.open("https://www.managerzone.com/")
        self.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
        self.type('input[id="login_username"]', os.environ.get("MZUSER"))
        self.type('input[id="login_password"]', os.environ.get("MZPASS"))
        self.click('a[id="login"]')     
        try:
            text = self.get_text('//*[@id="header-stats-wrapper"]/h5[3]')   
            season = int(only_numerics(text.split('·')[0]))
        except Exception as e:
            season = None

        if season != None:
            session = get_db()
            control = session.query(Mzcontrol).first()
            if control:
                control.season = season
                session.commit()
        
        # Determine Countries
        self.open("https://www.managerzone.com/?p=national_teams&type=senior")
        
        countries_sel = self.find_element("#cid")
        soup = BeautifulSoup(countries_sel.get_attribute("outerHTML"), 'html.parser')
        countries_sel = soup.find_all("option")
        
        coutries_array = []
        for country_sel in countries_sel:
            country = Countries()
            country.id = int(country_sel.get("value"))
            country.name = country_sel.text
            coutries_array.append(country)
        
        
if __name__ == "__main__":
    
    Managerzone().general_control()