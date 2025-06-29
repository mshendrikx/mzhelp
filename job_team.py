import os
import logging

from seleniumbase import SB
from pathlib import Path
from bs4 import BeautifulSoup
from project.models import Player, PlayerTraining, User
from project.common import (
    get_db,
    only_numerics,
    countries_data,
    get_utc_string,
    get_mz_day,
    process_training_data,
    set_player_scout,
    utc_input,
)

from dotenv import load_dotenv

load_dotenv()

session = get_db()

utc_string = get_utc_string(format="%Y%m%d%H%M")
log_file_name = "job_team_" + utc_string + ".log"

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

users = session.query(User).all()

for user in users:
    logging.info(f"Processing user: {user.mzuser}")
    with SB(
        headless=True,
        browser="firefox",
        # uc=True,
        # servername=os.environ.get("SELENIUM_HUB_HOST"),
        # port=os.environ.get("SELENIUM_HUB_PORT"),
    ) as sb:
        
        logging.info("Login to ManagerZone")
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
        soup = BeautifulSoup(players_container.get_attribute("outerHTML"), "lxml")
        players_soup = soup.find_all(class_="playerContainer")

        players = []
        players_training = []
        countries = countries_data(index=1)
        for player_soup in players_soup:
            header = player_soup.h2
            player_id = int(header.find(class_="player_id_span").text)
            player = session.query(Player).filter_by(id=player_id).first()
            if not player:
                player = Player()
                player.id = player_id
                player.country = 0
                player.teamid = 0
                session.add(player)
                session.commit()
            player.changedat = utc_input()
            player.teamid = teamid
            player.name = header.find(class_="player_name").text
            player.number = int(header.a.text.split(".")[0])
            if player_soup.find(class_="dg_playerview_retire") != None:
                player.retiring = 1
            else:
                player.retiring = 0
            container = player_soup.div.div
            playerview_info = container.find(class_="dg_playerview_info")
            player_info = playerview_info.find("tbody")
            player_chars = player_info.find_all("tr")
            scout_report = playerview_info.find(title="Scout report")
            if scout_report == None:
                player.starhigh = 0
                player.starlow = 0
                player.startraining = 0
            training_graph = playerview_info.find(
                class_="player_icon_placeholder training_graphs soccer"
            )
            if training_graph != None:
                player.traininginfo = 1
                player_training = (
                    session.query(PlayerTraining).filter_by(id=player.id).first()
                )
                if not player_training:
                    player_training = PlayerTraining()
                    player_training.id = player.id
                    session.commit()
                    players_training.append(player_training)
            else:
                player.traininginfo = 0
            player.salary = 0
            for player_char in player_chars:
                if "Age" in player_char.text:
                    tds = player_char.find_all("td")
                    player.age = int(only_numerics(tds[0].text))
                    player.transferage = player.age
                    if "Left" in tds[1].text:
                        player.foot = 0
                    elif "Right" in tds[1].text:
                        player.foot = 1
                    else:
                        player.foot = 2
                elif "Height" in player_char.text:
                    tds = player_char.find_all("td")
                    player.height = int(only_numerics(tds[0].text))
                    player.weight = int(only_numerics(tds[1].text))
                elif "Birth" in player_char.text:
                    player.season = int(only_numerics(player_char.td.text))
                elif "Nationality" in player_char.text:
                    player.country = countries[player_char.td.span.text].id
                    if len(player_char.find_all("a")) == 0:
                        player.national = 0
                    else:
                        player.national = 1
                elif "Value" in player_char.text:
                    player.value = int(only_numerics(player_char.td.text))
                elif "Salary" in player_char.text:
                    player.salary = int(only_numerics(player_char.td.text))
                elif "Balls" in player_char.text:
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
            session.commit()
            players.append(player)

        # Scout Data
        for player in players:
            if player.startraining == None:
                url = (
                    "https://www.managerzone.com/ajax.php?p=players&sub=scout_report&pid="
                    + str(player.id)
                    + "&sport=soccer"
                )
                sb.open(url)
                player = set_player_scout(
                    scout_page=sb.driver.page_source, player=player
                )

            session.add(player)

        # Training Data
        for player_training in players_training:
            player_training.trainingdate = utc_input()
            url = (
                "https://www.managerzone.com/ajax.php?p=trainingGraph&sub=getJsonTrainingHistory&sport=soccer&player_id="
                + str(player_training.id)
            )
            sb.open(url)
            player_training.trainingdata = process_training_data(sb.driver.page_source)
            session.add(player_training)

        session.commit()

logging.info("Finishing the script")