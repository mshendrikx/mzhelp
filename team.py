import os

from seleniumbase import SB
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from project.models import Player, User
from project.common import get_db, only_numerics

from dotenv import load_dotenv

load_dotenv()

session = get_db()

users = session.query(User).filter(User.id > 1).all()

for user in users:

    with SB(uc=True) as sb:
        
        sb.open("https://www.managerzone.com/")
        sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
        sb.type('input[id="login_username"]', user.mzuser)
        sb.type('input[id="login_password"]', user.mzpass)
        sb.click('a[id="login"]')   
        sb.open("https://www.managerzone.com/?p=team") 
        text = sb.get_text('//*[@id="infoAboutTeam"]/dd[1]/span[3]')
        teamid = int(only_numerics(text))

        players = session.query(Player).filter_by(teamid=teamid)
        
        for player in players:
            player.teamid = 0
            
        session.commit()
        
        sb.open("https://www.managerzone.com/?p=players")

        players_container = sb.find_element("#players_container")
        soup = BeautifulSoup(players_container.get_attribute("outerHTML"), 'html.parser')
        players_soup = soup.find_all(class_="playerContainer")

        players = []        
        for player_soup in players_soup:
            player = Player()
            player.teamid = teamid
            header = player_soup.h2
            player.id = int(header.find(class_="player_id_span").text)
            player.name = header.find(class_="player_name").text
            container = player_soup.div.div
            player_info = container.find(class_="dg_playerview_info")
            player_info = player_info.find("tbody")
            player_chars = player_info.find_all("tr")
            player.salary = 0
            for player_char in player_chars:
                if 'Age' in player_char.text:
                    tds = player_char.find_all("td")
                    player.age = int(only_numerics(tds[0].text))
                    player.transferage = player.age
                    if 'Left' in tds[1].text:
                        player.foot = 0
                    elif 'Right' in tds[1].text:
                        player.foot = 1
                    else:
                        player.foot = 2
                elif 'Height' in player_char.text:
                    tds = player_char.find_all("td")
                    player.height = int(only_numerics(tds[0].text))
                    player.weight = int(only_numerics(tds[1].text))
                elif 'Birth' in player_char.text:
                    player.season = int(only_numerics(player_char.td.text))
                elif 'Nationality' in player_char.text:
                    breakpoint
                elif 'Value' in player_char.text:
                    player.value = int(only_numerics(player_char.td.text))
                elif 'Salary' in player_char.text:
                    player.salary = int(only_numerics(player_char.td.text))
                elif 'Balls' in player_char.text:
                    player.totalskill = int(only_numerics(player_char.td.text))
            player_skills = container.find(class_="skills-container floatLeft clearfix")
            player_skills = player_skills.find("tbody")
            player_skills = player_skills.find_all("tr")
            count = 0
            for player_skill in player_skills:
                match count:
                    case 0:
                        player.speedscout = 0
                        player.speed = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.speedmax = 1
                        else:
                            player.speedmax = 0                            
                    case 1:
                        player.staminascout = 0
                        player.stamina = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.staminamax = 1
                        else:
                            player.staminamax = 0                            
                    case 2:
                        player.intelligencescout = 0
                        player.intelligence = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.intelligencemax = 1
                        else:
                            player.intelligencemax = 0                            
                    case 3:
                        player.passingscout = 0
                        player.passing = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.passingmax = 1
                        else:
                            player.passingmax = 0                            
                    case 4:                       
                        player.shootingscout = 0
                        player.shooting = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.shootingmax = 1
                        else:
                            player.shootingmax = 0                            
                    case 5:
                        player.headingscout = 0
                        player.heading = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.headingmax = 1
                        else:
                            player.headingmax = 0                            
                    case 6:
                        player.keepingscout = 0
                        player.keeping = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.keepingmax = 1
                        else:
                            player.keepingmax = 0                            
                    case 7:
                        player.controlscout = 0
                        player.control = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.controlmax = 1
                        else:
                            player.controlmax = 0                            
                    case 8:
                        player.tacklingscout = 0
                        player.tackling = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.tacklingmax = 1
                        else:
                            player.tacklingmax = 0                            
                    case 9:
                        player.aerialscout = 0
                        player.aerial = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.aerialmax = 1
                        else:
                            player.aerialmax = 0                            
                    case 10:
                        player.playsscout = 0
                        player.plays = int(only_numerics(player_skill.text))
                        maxed = player_skill.find(class_="maxed")
                        if maxed:
                            player.playsmax = 1
                        else:
                            player.playsmax = 0                            
                    case 11:
                        player.experience = int(only_numerics(player_skill.text))
                    case 12:
                        player.form = int(only_numerics(player_skill.text))
                
                count += 1
                
            
            players.append(player)
        
        for player in players:
            url = 'https://www.managerzone.com/ajax.php?p=players&sub=scout_report&pid=' + str(player.id) + '&sport=soccer'
            sb.open(url)
            soup = BeautifulSoup(sb.driver.page_source, 'html.parser')
            scouts_dd = soup.find_all("dd")
            count = 0
            for scout_dd in scouts_dd:
                stars = len(scout_dd.find_all(class_="fa fa-star fa-2x lit"))
                if count != 2:
                    if count == 0:
                        player.starhigh = stars
                    else:
                        player.starlow = stars
                    if 'Speed' in scout_dd.text:
                        player.speedscout = stars
                    if 'Stamina' in scout_dd.text:
                        player.staminascout = stars
                    if 'Intelligence' in scout_dd.text:
                        player.intelligencescout = stars
                    if 'Passing' in scout_dd.text:
                        player.passingscout = stars
                    if 'Shooting' in scout_dd.text:
                        player.shootingscout = stars
                    if 'Heading' in scout_dd.text:
                        player.headingscout = stars
                    if 'Keeping' in scout_dd.text:
                        player.keepingscout = stars
                    if 'Control' in scout_dd.text:
                        player.controlscout = stars
                    if 'Tackling' in scout_dd.text:
                        player.tacklingscout = stars
                    if 'Aerial' in scout_dd.text:
                        player.aerialscout = stars
                    if 'Plays' in scout_dd.text:
                        player.playsscout = stars
                else:
                    player.startraining = stars
                
#                match count:
#                    case: 0
#                    case: 1
#                    case: 2
                count += 1
                
            
        breakpoint
       

                
#        for element in elements:
#            player_info = element.find_element(By.CLASS_NAME, "dg_playerview_info")
#            soup = BeautifulSoup(player_info.get_attribute("outerHTML"), 'html5lib')
#            tables = soup= soup.find_all("table")
#            breakpoint

#            container_id = element.get_attribute('id')
#            player_xpath = '//*[@id="' + container_id + '"]'
#            player = Player()




#        for player_element in players_table:
#            player = Player()
#            player_xpath = '//*[@id="thePlayers_' + str(player_seq) + '"]'
#            player.id = int(only_numerics(player_element.find_element(By.CLASS_NAME, 'player_id_span').text))
#            player.name = player_element.find_element(By.CLASS_NAME, 'player_name').text            
#            player.country = 
#            xpath = player_xpath + '/div/div[1]/div[1]/table[1]/tbody/tr[1]/td[1]/strong'
#            player.age = int(only_numerics(player_element.find_element(By.XPATH, xpath).text))
#            xpath = player_xpath + '/div/div[1]/div[1]/table[1]/tbody/tr[3]/td/strong'
#            player.season = int(only_numerics(player_element.find_element(By.XPATH, xpath).text))
#            player.teamid = teamid
#            player.national = 
#            player.transferage = 
#            player.totalskill = 
#            player.height = 
#            player.weight = 
#            player.foot = 
#            player.starhigh = 
#            player.starlow = 
#            player.startraining = 
#            player.value = 
#            player.salary = 
#            player.speed = 
#            player.speedmax = 
#            player.speedscout = 
#            player.stamina = 
#            player.staminamax = 
#            player.staminascout = 
#            player.intelligence = 
#            player.intelligencemax = 
#            player.intelligencescout = 
#            player.passing = 
#            player.passingmax = 
#            player.passingscout = 
#            player.shooting = 
#            player.shootingmax = 
#            player.shootingscout = 
#            player.heading = 
#            player.headingmax = 
#            player.headingscout = 
#            player.keeping = 
#            player.keepingmax = 
#            player.keepingscout = 
#            player.control = 
#            player.controlmax = 
#            player.controlscout = 
#            player.tackling = 
#            player.tacklingmax = 
#            player.tacklingscout = 
#            player.aerial = 
#            player.aerialmax = 
#            player.aerialscout = 
#            player.plays = 
#            player.playsmax = 
#            player.playsscout = 
#            player.experience = 
#            player.form = 
#
#            #session.add(player)
#        breakpoint