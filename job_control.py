import os

from seleniumbase import SB
from dotenv import load_dotenv
from project.common import get_db, only_numerics
from project.models import Mzcontrol
from bs4 import BeautifulSoup

from project.models import Countries

load_dotenv()

session = get_db()

with SB(
    headless=True,
    #browser="firefox",
    uc=True,
    servername=os.environ.get("SELENIUM_HUB_HOST", None),
    port=os.environ.get("SELENIUM_HUB_PORT", None),
) as sb:
    
    sb.open("https://www.managerzone.com/")
    sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
    sb.type('input[id="login_username"]', os.environ.get("MZUSER"))
    sb.type('input[id="login_password"]', os.environ.get("MZPASS"))
    sb.click('a[id="login"]')     
    try:
        text = sb.get_text('//*[@id="header-stats-wrapper"]/h5[3]')   
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
    sb.open("https://www.managerzone.com/?p=national_teams&type=senior")
    
    countries_sel = sb.find_element("#cid")
    soup = BeautifulSoup(countries_sel.get_attribute("outerHTML"), 'html.parser')
    countries_sel = soup.find_all("option")
    
    for country_sel in countries_sel:        
        country_id = int(country_sel.get("value"))
        sb.select_option_by_value('//*[@id="cid"]', country_sel.get("value"))
        sb.wait_for_element('//*[@id="ui-tabs-1"]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[1]/img')
        country_db = session.query(Countries).filter_by(id=country_id).first()
        if country_db:
            continue
        country = Countries()
        country.id = country_id
        country.name = country_sel.text
        flag_el = sb.get('//*[@id="ui-tabs-1"]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[1]/img')
        country.flag = flag_el.screenshot_as_base64
        country.ages = 0
        session.add(country)
        session.commit()
