import os
import logging
import time

from pathlib import Path
from seleniumbase import SB
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from project.models import Player, PlayerTraining, Countries, Tranfers, Mzcontrol
from project.common import (
    get_db,
    only_numerics,
    countries_data,
    get_utc_string,
    process_training_data,
    set_player_scout,
    utc_input,
    date_input,
)

from dotenv import load_dotenv

load_dotenv()

utc_string = get_utc_string(format="%Y%m%d%H%M")
log_file_name = "job_transfer_" + utc_string + ".log"

# Get the directory of the script
script_dir = Path(__file__).parent
# Define the logs directory (same level as the script)
logs_dir = script_dir / "logs"
# Create the logs directory if it doesn't exist
logs_dir.mkdir(exist_ok=True)
# Configure logging to save logs in the logs folder
log_file = logs_dir / log_file_name  # Path to the log file
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define the log format
    filename=str(log_file),  # Optional: Log to a file instead of the console
    filemode="a",  # Optional: 'a' for append, 'w' for overwrite
)

logging.info("Starting the script")

count_transfer = 0
count_training = 0

with SB(
    headless=True,
    uc=True,
    servername=os.environ.get("SELENIUM_HUB_HOST"),
    port=os.environ.get("SELENIUM_HUB_PORT"),
) as sb:

    session = get_db()

    sb.open("https://www.managerzone.com/")
    sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
    sb.type('input[id="login_username"]', os.environ.get("MZUSER"))
    sb.type('input[id="login_password"]', os.environ.get("MZPASS"))
    sb.click('a[id="login"]')
    sb.wait_for_element('//*[@id="header-username"]')
    sb.open("https://www.managerzone.com/?p=profile&sub=change")

    # Get Time Zone
    sb.wait_for_element('//*[@id="profile"]/div[4]/div/select')
    select_element = sb.find_element('//*[@id="profile"]/div[4]/div/select')
    select = Select(select_element)
    selected_option = select.first_selected_option
    time_zone = selected_option.text

    sb.open("https://www.managerzone.com/?p=transfer")
    sb.wait_for_element('//*[@id="players_container"]')
    utc_string = get_utc_string(format="%Y-%m-%d")

    countries = session.query(Countries).all()

    searches = []
    for country in countries:
        if country.ages > 18:
            age = 19
            while age <= country.ages:
                search = []
                search.append(str(country.id))
                search.append(str(age))
                search.append(str(age))
                age += 1
                searches.append(search)
            search = []
            search.append(str(country.id))
            search.append(str(age))
            search.append("37")
            searches.append(search)
        else:
            search = []
            search.append(str(country.id))
            search.append("19")
            search.append("37")
            searches.append(search)

    pages_soup = []

    # update control table with deadline
    mzcontrol = session.query(Mzcontrol).first()
    deadline_control = mzcontrol.deadline
    utc_string = get_utc_string(format="%d/%m/%Y %I:%M%p")
    mzcontrol.deadline = date_input(utc_string, 1, "UTC")
    session.commit()

    logging.info("Start SOUP data")
    try:
        for search in searches:
            sb.click_xpath('//*[@id="resetb"]')
            sb.select_option_by_value('//*[@id="deadline"]', "3")
            sb.select_option_by_value('//*[@id="nationality"]', search[0])
            sb.type('input[id="agea"]', search[1])
            sb.type('input[id="ageb"]', search[2])
            sb.click_xpath('//*[@id="searchb"]')
            next_link = True
            count = 0
            while next_link:
                time.sleep(2)
                count += 1
                try:
                    sb.wait_for_element('//*[@id="thePlayers_0"]', timeout=2)
                    players_container = sb.find_element("#players_container")
                    soup = BeautifulSoup(
                        players_container.get_attribute("outerHTML"), "lxml"
                    )
                    page_soup = []
                    page_soup.append(soup)
                    page_soup.append(int(search[0]))

                    pages_soup.append(page_soup)
                    try:
                        button_next = sb.find_element(
                            "div.transferSearchPages a:contains('Next')", timeout=2
                        )
                        button_next.click()
                    except:
                        break
                except Exception as e:
                    message = (
                        "Error in search: "
                        + str(search[0])
                        + " "
                        + str(search[1])
                        + " "
                        + str(search[2])
                        + " "
                        + str(count)
                    )
                    logging.error(message)
                    logging.error(e)
                    break

    except Exception as e:
        logging.error(e)

    logging.info("End SOUP data")

    countries = countries_data(index=1)
    utc_now = utc_input()
    transfers_db = session.query(Tranfers).filter(Tranfers.deadline >= utc_now).all()
    session.query(Tranfers).filter(
        Tranfers.deadline < utc_now, Tranfers.active == 1
    ).update({"active": 0})
    session.commit()
    players_db = []
    for transfer_db in transfers_db:
        players_db.append(transfer_db.playerid)

    logging.info("Start basic player data")
    player = None
    players = []
    reuse_players = []
    for page_soup in pages_soup:
        players_soup = page_soup[0].find_all(class_="playerContainer")

        for player_soup in players_soup:
            try:
                header = player_soup.h2
                player_id = 0
                player_id = int(header.find(class_="player_id_span").text)
                if player_id in players_db or player_id in players:
                    continue
                player_name = header.find(class_="player_name").text
                del player
                player = session.query(Player).filter_by(id=player_id).first()
                if not player:
                    message = "Add player: " + str(player_id) + " " + player_name
                    logging.info(message)
                    player = Player()
                    player.id = player_id
                    player.country = 0
                    player.teamid = 0
                    player.number = 0
                    player.retiring = 0
                    player.national = 0
                    add_player = True
                else:
                    message = "Modify player: " + str(player_id) + " " + player_name
                    logging.info(message)
                    add_player = False
                player.changedat = utc_input()
                player.country = page_soup[1]
                player.name = player_name
                float_left = player_soup.find(class_="floatLeft")
                float_left = float_left.table.tbody
                scout_report = float_left.find(class_="scout_report_row box_dark")
                float_left = float_left.find_all("tr")
                player_chars = float_left[0].find_all("tr")
                player_skills = float_left[8].find_all("tr")
                float_right = player_soup.find(
                    class_="floatRight transfer-control-area"
                )
                float_right = float_right.find_all(class_="box_dark")
                player.traininginfo = 1
                player.salary = 0
                for player_char in player_chars:
                    if "Age" in player_char.text:
                        player.age = int(only_numerics(player_char.text))
                        player.transferage = player.age
                    elif "Foot" in player_char.text:
                        if "Left" in player_char.text:
                            player.foot = 0
                        elif "Right" in player_char.text:
                            player.foot = 1
                        else:
                            player.foot = 2
                    elif "Height" in player_char.text:
                        player.height = int(only_numerics(player_char.text))
                    elif "Weight" in player_char.text:
                        player.weight = int(only_numerics(player_char.text))
                    elif "Born" in player_char.text:
                        player.season = int(only_numerics(player_char.text))
                    elif "Balls" in player_char.text:
                        player.totalskill = int(only_numerics(player_char.text))
                money_info = float_right[0].find_all("span")
                player.value = int(only_numerics(money_info[0].text))
                player.salary = int(only_numerics(money_info[1].text))

                try:
                    stars_data = player_skills[13]
                    stars_data = stars_data.find_all(class_="scout_report_stars")
                    star_high = stars_data[0].find_all("i")
                    player.starhigh = int(len(star_high))
                    star_low = stars_data[1].find_all("i")
                    player.starlow = int(len(star_low))
                    star_trainning = stars_data[2].find_all("i")
                    player.startraining = int(len(star_trainning))
                    player.scoutinfo = 1
                except:
                    player.starhigh = 0
                    player.starlow = 0
                    player.startraining = 0
                    player.scoutinfo = 0

                player_skill = player_skills[0]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.speedscout = player.starhigh
                    else:
                        player.speedscout = player.starlow
                except:
                    player.speedscout = 0
                player.speed = int(only_numerics(player_skill.text.split('(')[1]))
                if player_skill.find(class_="maxed"):
                    player.speedmax = 1
                else:
                    player.speedmax = 0

                player_skill = player_skills[1]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.staminascout = player.starhigh
                    else:
                        player.staminascout = player.starlow
                except:
                    player.staminascout = 0
                player.stamina = int(only_numerics(player_skill.text.split('(')[1]))

                if player_skill.find(class_="maxed"):
                    player.staminamax = 1
                else:
                    player.staminamax = 0
                                
                player_skill = player_skills[2]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.intelligencescout = player.starhigh
                    else:
                        player.intelligencescout = player.starlow
                except:
                    player.intelligencescout = 0
                player.intelligence = int(only_numerics(player_skill.text.split('(')[1]))

                if player_skill.find(class_="maxed"):
                    player.intelligencemax = 1
                else:
                    player.intelligencemax = 0

                player_skill = player_skills[3]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.passingscout = player.starhigh
                    else:
                        player.passingscout = player.starlow
                except:
                    player.passingscout = 0
                player.passing = int(only_numerics(player_skill.text.split('(')[1]))
                            
                if player_skill.find(class_="maxed"):
                    player.passingmax = 1
                else:
                    player.passingmax = 0
                                
                player_skill = player_skills[4]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.shootingscout = player.starhigh
                    else:
                        player.shootingscout = player.starlow
                except:
                    player.shootingscout = 0
                player.shooting = int(only_numerics(player_skill.text.split('(')[1]))
                            
                if player_skill.find(class_="maxed"):
                    player.shootingmax = 1
                else:
                    player.shootingmax = 0
                                
                player_skill = player_skills[5]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.headingscout = player.starhigh
                    else:
                        player.headingscout = player.starlow
                except:
                    player.headingscout = 0
                player.heading = int(only_numerics(player_skill.text.split('(')[1]))

                if player_skill.find(class_="maxed"):
                    player.headingmax = 1
                else:
                    player.headingmax = 0

                player_skill = player_skills[6]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.keepingscout = player.starhigh
                    else:
                        player.keepingscout = player.starlow
                except:
                    player.keepingscout = 0
                player.keeping = int(only_numerics(player_skill.text.split('(')[1]))

                if player_skill.find(class_="maxed"):
                    player.keepingmax = 1
                else:
                    player.keepingmax = 0
                                
                player_skill = player_skills[7]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.controlscout = player.starhigh
                    else:
                        player.controlscout = player.starlow
                except:
                    player.controlscout = 0
                player.control = int(only_numerics(player_skill.text.split('(')[1]))
                            
                if player_skill.find(class_="maxed"):
                    player.controlmax = 1
                else:
                    player.controlmax = 0
                                
                player_skill = player_skills[8]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.tacklingscout = player.starhigh
                    else:
                        player.tacklingscout = player.starlow
                except:
                    player.tacklingscout = 0
                player.tackling = int(only_numerics(player_skill.text.split('(')[1]))
                            
                if player_skill.find(class_="maxed"):
                    player.tacklingmax = 1
                else:
                    player.tacklingmax = 0
                                
                player_skill = player_skills[9]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.aerialscout = player.starhigh
                    else:
                        player.aerialscout = player.starlow
                except:
                    player.aerialscout = 0
                player.aerial = int(only_numerics(player_skill.text.split('(')[1]))
                            
                if player_skill.find(class_="maxed"):
                    player.aerialmax = 1
                else:
                    player.aerialmax = 0
                                
                player_skill = player_skills[10]
                try:
                    skill_sup = int(player_skill.find(class_="sup").text)
                    if skill_sup == 1:
                        player.playsscout = player.starhigh
                    else:
                        player.playsscout = player.starlow
                except:
                    player.playsscout = 0
                player.plays = int(only_numerics(player_skill.text.split('(')[1]))
                            
                if player_skill.find(class_="maxed"):
                    player.playsmax = 1
                else:
                    player.playsmax = 0
                                
                player_skill = player_skills[11]
                player.experience = int(only_numerics(player_skill.text.split('(')[1]))
                
                player_skill = player_skills[12]
                player.form = int(only_numerics(player_skill.text.split('(')[1]))

                strongs = float_right[0].find_all("strong")
                if add_player:
                    session.add(player)
                transfer = Tranfers()
                transfer.playerid = player.id
                transfer.deadline = date_input(strongs[1].text, 0, time_zone)
                transfer.askingprice = int(only_numerics(strongs[2].text))
                strongs = float_right[1].find_all("strong")
                transfer.actualprice = int(only_numerics(strongs[0].text))
                if transfer.actualprice < transfer.askingprice:
                    transfer.actualprice = transfer.askingprice
                transfer.active = 1
                session.add(transfer)
                count_transfer += 1
                players.append(player.id)
                reuse_players.append(player)

            except Exception as e:
                logging.error(e)

        session.commit()

    logging.info("End basic player data")
    # Scout and Training Data
    message = "Start training data, players: " + str(len(reuse_players))
    logging.info(message)
    count_players = 0
    for player in reuse_players:
        try:
            add_training = False
            if player.traininginfo == 1:
                player_training = (
                    session.query(PlayerTraining).filter_by(id=player.id).first()
                )
                if not player_training:
                    add_training = True
                    player_training = PlayerTraining()
                    player_training.id = player.id

                player_training.trainingdate = utc_input()

                url = (
                    "https://www.managerzone.com/ajax.php?p=trainingGraph&sub=getJsonTrainingHistory&sport=soccer&player_id="
                    + str(player_training.id)
                )

                sb.open(url)
                sb.wait_for_element("/html/body", timeout=1)

                player_training.trainingdata, maxs = process_training_data(
                    sb.driver.page_source
                )

            if add_training:
                session.add(player_training)

        except Exception as e:
            message = "Error training report: " + str(player.id) + " " + player.name
            logging.error(message)
            logging.error(e)

        session.commit()

    logging.info("End scout and training data")

    text = "Trainings: " + str(count_training) + " Transfers: " + str(count_transfer)
    logging.info(text)
    logging.info("Script finished")
