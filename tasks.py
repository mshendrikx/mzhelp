import os

from seleniumbase import SB
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv

load_dotenv()

def get_team_players_data(user, password):

    with SB(uc=True) as sb:
        sb.open("https://www.managerzone.com/")
        sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
        sb.type('input[id="login_username"]', user)
        sb.type('input[id="login_password"]', password)
        sb.click('a[id="login"]')

        sb.open("https://www.managerzone.com/?p=players")
        
        driver = sb.driver

        try:
            players_container = driver.find_element(
                        By.ID, "players_container"
                    )
            players_table = players_container.find_elements(
                        By.CLASS_NAME, "playerContainer"
                    )
        except Exception as e:
            1 == 1
        
        for player_element in players_table:
            breakpoint


        breakpoint