import os
import math

from seleniumbase import SB
from dotenv import load_dotenv
from project.common import get_db, only_numerics, date_input, utc_input

from project.models import Bids, Transfers


load_dotenv()

session = get_db()

utc_int = utc_input()
bids = session.query(Bids).filter(Bids.dtstart < utc_int, Bids.active ==1).all()

if bids:

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

        while bids:
    
            for bid in bids:
                transfer = session.query(Transfers).filter_by(id=bid.transferid, active=1).first()
                sb.open(f"https://www.managerzone.com/?p=transfer&sub=players&u={transfer.playerid}")
    
                try:
                    sb.wait_for_element('//*[@id="thePlayers_0"]')
                    sb.click('//*[@id="thePlayers_0"]/div/div/div[2]/div/div[2]/table/tbody/tr/td[2]/span[1]/a')
                    next_bid = math.ceil(int( only_numerics(sb.get_text(
                            '//*[@id="lightboxContent_transfer_buy_form"]/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td/div/div/dl/dd[4]/span[2]'
                    ).split('R$')[0])) * 1.05)
                except Exception as e:
                    try:
                        sb.wait_for_element('//*[@id="players_container"]/div/p')
                        if sb.get_text('//*[@id="players_container"]/div/p') == "Waiting for playerlist":
                            transfer.active = 0
                            bid.active = 0
                            session.commit()
                    except:
                        continue
                    continue
                
                if next_bid <= bid.maxbid:
                    try:
                        sb.wait_for_element('//*[@id="transfer_place_bid_button"]')
                        sb.execute_script("window.confirm = function() { return true; }")
                        sb.click('//*[@id="transfer_place_bid_button"]')
                    except:
                        continue                    
    
                sb.open(f"https://www.managerzone.com/?p=transfer&sub=players&u={transfer.playerid}")       
                latest_bid = int( only_numerics(sb.get_text('//*[@id="thePlayers_0"]/div/div/div[2]/div/div[2]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/strong')))
                transfer.actualprice = latest_bid
                bid.finalvalue = latest_bid
                deadline_str = sb.get_text('//*[@id="thePlayers_0"]/div/div/div[2]/div/div[1]/table/tbody/tr[3]/td[2]/strong')
                transfer.deadline = date_input(date=deadline_str)
    
                session.commit()
                
            utc_int = utc_input()
            bids = session.query(Bids).filter(Bids.dtstart < utc_int, Bids.active ==1).all()

