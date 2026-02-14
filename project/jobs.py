import os
import logging
import time
import asyncio

from seleniumbase import SB
from selenium.webdriver.support.ui import Select
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from pathlib import Path
from project.models import (
    Players,
    PlayersTraining,
    Countries,
    Transfers,
    Mzcontrol,
    Users,
)
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

load_dotenv()


def job_nations():
    session = get_db()

    with SB(
        headless=True,
        # browser="firefox",
        uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST"),
        port=os.environ.get("SELENIUM_HUB_PORT"),
    ) as sb:

        sb.open("https://www.managerzone.com/")
        sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
        sb.type('input[id="login_username"]', os.environ.get("MZUSER"))
        sb.type('input[id="login_password"]', os.environ.get("MZPASS"))
        sb.click('a[id="login"]')
        sb.open("https://www.managerzone.com/?p=national_teams&type=senior")

        countries_sel = sb.find_element("#cid")
        soup = BeautifulSoup(countries_sel.get_attribute("outerHTML"), "lxml")
        countries_sel = soup.find_all("option")

        for country_sel in countries_sel:
            country_id = int(country_sel.get("value"))
            sb.select_option_by_value('//*[@id="cid"]', country_sel.get("value"))
            sb.wait_for_element(
                '//*[@id="ui-tabs-1"]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[1]/img'
            )
            country_db = session.query(Countries).filter_by(id=country_id).first()
            if country_db:
                continue
            country = Countries()
            country.id = country_id
            country.name = country_sel.text
            flag_el = sb.get(
                '//*[@id="ui-tabs-1"]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[1]/img'
            )
            country.flag = flag_el.screenshot_as_base64
            country.ages = 0
            session.add(country)
            session.commit()


def job_control():

    with SB(
        headless=True,
        # browser="firefox",
        uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST", None),
        port=os.environ.get("SELENIUM_HUB_PORT", None),
    ) as sb:

        session = get_db()
        sb.open("https://www.managerzone.com/")
        sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
        sb.type('input[id="login_username"]', os.environ.get("MZUSER"))
        sb.type('input[id="login_password"]', os.environ.get("MZPASS"))
        sb.click('a[id="login"]')
        try:
            text = sb.get_text('//*[@id="header-stats-wrapper"]/h5[3]')
            season = int(only_numerics(text.split("·")[0]))
        except Exception as e:
            season = None
        if season != None:
            control = session.query(Mzcontrol).first()
            if control:
                control.season = season
                session.commit()

        # Determine Countries
        sb.open("https://www.managerzone.com/?p=national_teams&type=senior")

        countries_sel = sb.find_element("#cid")
        soup = BeautifulSoup(countries_sel.get_attribute("outerHTML"), "html.parser")
        countries_sel = soup.find_all("option")

        for country_sel in countries_sel:
            country_id = int(country_sel.get("value"))
            sb.select_option_by_value('//*[@id="cid"]', country_sel.get("value"))
            sb.wait_for_element(
                '//*[@id="ui-tabs-1"]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[1]/img'
            )
            country_db = session.query(Countries).filter_by(id=country_id).first()
            if country_db:
                continue
            country = Countries()
            country.id = country_id
            country.name = country_sel.text
            flag_el = sb.get(
                '//*[@id="ui-tabs-1"]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[1]/img'
            )
            country.flag = flag_el.screenshot_as_base64
            country.ages = 0
            session.add(country)
            session.commit()


def get_transfer_searches(countries):

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

    return searches


def job_teams():
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

    users = session.query(Users).all()

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
            sb.click(
                'button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]'
            )
            sb.type('input[id="login_username"]', user.mzuser)
            sb.type('input[id="login_password"]', user.mzpass)
            sb.click('a[id="login"]')
            sb.open("https://www.managerzone.com/?p=team")
            text = sb.get_text('//*[@id="infoAboutTeam"]/dd[1]/span[3]')
            teamid = int(only_numerics(text))

            players = session.query(Players).filter_by(teamid=teamid)

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
                player = session.query(Players).filter_by(id=player_id).first()
                if not player:
                    player = Players()
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
                        session.query(PlayersTraining).filter_by(id=player.id).first()
                    )
                    if not player_training:
                        player_training = PlayersTraining()
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
                player_skills = container.find(
                    class_="skills-container floatLeft clearfix"
                )
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
                player_training.trainingdata = process_training_data(
                    sb.driver.page_source
                )
                session.add(player_training)

            session.commit()

    logging.info("Finishing the script")


def job_transfers():

    count_transfer = 0
    count_training = 0
    
    session = get_db()

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
            
    if len(searches) == 0:
        logging.warning("No searches to process")
        return

    with SB(
        headless=True,
        uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST"),
        port=os.environ.get("SELENIUM_HUB_PORT"),
    ) as sb:

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

        utc_now = utc_input()
        transfers_db = (
            session.query(Transfers).filter(Transfers.deadline >= utc_now).all()
        )
        session.query(Transfers).filter(
            Transfers.deadline < utc_now, Transfers.active == 1
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
                    player = session.query(Players).filter_by(id=player_id).first()
                    if not player:
                        message = "Add player: " + str(player_id) + " " + player_name
                        logging.info(message)
                        player = Players()
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
                    player.speed = int(only_numerics(player_skill.text.split("(")[1]))
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
                    player.stamina = int(only_numerics(player_skill.text.split("(")[1]))

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
                    player.intelligence = int(
                        only_numerics(player_skill.text.split("(")[1])
                    )

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
                    player.passing = int(only_numerics(player_skill.text.split("(")[1]))

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
                    player.shooting = int(
                        only_numerics(player_skill.text.split("(")[1])
                    )

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
                    player.heading = int(only_numerics(player_skill.text.split("(")[1]))

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
                    player.keeping = int(only_numerics(player_skill.text.split("(")[1]))

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
                    player.control = int(only_numerics(player_skill.text.split("(")[1]))

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
                    player.tackling = int(
                        only_numerics(player_skill.text.split("(")[1])
                    )

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
                    player.aerial = int(only_numerics(player_skill.text.split("(")[1]))

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
                    player.plays = int(only_numerics(player_skill.text.split("(")[1]))

                    if player_skill.find(class_="maxed"):
                        player.playsmax = 1
                    else:
                        player.playsmax = 0

                    player_skill = player_skills[11]
                    player.experience = int(
                        only_numerics(player_skill.text.split("(")[1])
                    )

                    player_skill = player_skills[12]
                    player.form = int(only_numerics(player_skill.text.split("(")[1]))

                    strongs = float_right[0].find_all("strong")
                    if add_player:
                        session.add(player)
                    transfer = Transfers()
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

#        # Training Data
#        message = "Start training data, players: " + str(len(reuse_players))
#        logging.info(message)
#
#        for player in reuse_players:
#            try:
#                add_training = False
#                if player.traininginfo == 1:
#                    player_training = (
#                        session.query(PlayersTraining).filter_by(id=player.id).first()
#                    )
#                    if not player_training:
#                        add_training = True
#                        player_training = PlayersTraining()
#                        player_training.id = player.id
#
#                    player_training.trainingdate = utc_input()
#
#                    url = (
#                        "https://www.managerzone.com/ajax.php?p=trainingGraph&sub=getJsonTrainingHistory&sport=soccer&player_id="
#                        + str(player_training.id)
#                    )
#
#                    sb.open(url)
#                    sb.wait_for_element("/html/body", timeout=1)
#
#                    player_training.trainingdata = process_training_data(
#                        sb.driver.page_source
#                    )
#
#                if add_training:
#                    session.add(player_training)
#
#            except Exception as e:
#                message = "Error training report: " + str(player.id) + " " + player.name
#                logging.error(message)
#                logging.error(e)
#
#            session.commit()
#
#        logging.info("End scout and training data")
#
#        text = (
#            "Trainings: " + str(count_training) + " Transfers: " + str(count_transfer)
#        )
#        logging.info(text)
#        logging.info("Script finished")


# async def process_lxml(lxml_data, coutry_id=0):
#
#    players_soup = lxml_data.find_all(class_="playerContainer")
#    for player_soup in players_soup:
#        try:
#            header = player_soup.h2
#            player_id = 0
#            player_id = int(header.find(class_="player_id_span").text)
#            if player_id in players_db or player_id in players:
#                continue
#            player_name = header.find(class_="player_name").text
#            del player
#            player = session.query(Player).filter_by(id=player_id).first()
#            if not player:
#                message = "Add player: " + str(player_id) + " " + player_name
#                logging.info(message)
#                player = Player()
#                player.id = player_id
#                player.country = 0
#                player.teamid = 0
#                player.number = 0
#                player.retiring = 0
#                player.national = 0
#                add_player = True
#            else:
#                message = "Modify player: " + str(player_id) + " " + player_name
#                logging.info(message)
#                add_player = False
#            player.changedat = utc_input()
#            player.country = coutry_id
#            player.name = player_name
#            float_left = player_soup.find(class_="floatLeft")
#            float_left = float_left.table.tbody
#            scout_report = float_left.find(class_="scout_report_row box_dark")
#            float_left = float_left.find_all("tr")
#            player_chars = float_left[0].find_all("tr")
#            player_skills = float_left[8].find_all("tr")
#            float_right = player_soup.find(
#                class_="floatRight transfer-control-area"
#            )
#            float_right = float_right.find_all(class_="box_dark")
#            training_graph = float_right[1].find(
#                class_="fa-regular fa-chart-line-up training-graphs-icon"
#            )
#            player.starhigh = 0
#            player.starlow = 0
#            player.startraining = 0
#            if scout_report == None:
#                player.scoutinfo = 0
#            else:
#                player.scoutinfo = 1
#            if training_graph == None:
#                player.traininginfo = 0
#            else:
#                count_training += 1
#                player.traininginfo = 1
#            player.salary = 0
#            for player_char in player_chars:
#                if "Age" in player_char.text:
#                    player.age = int(only_numerics(player_char.text))
#                    player.transferage = player.age
#                elif "Foot" in player_char.text:
#                    if "Left" in player_char.text:
#                        player.foot = 0
#                    elif "Right" in player_char.text:
#                        player.foot = 1
#                    else:
#                        player.foot = 2
#                elif "Height" in player_char.text:
#                    player.height = int(only_numerics(player_char.text))
#                elif "Weight" in player_char.text:
#                    player.weight = int(only_numerics(player_char.text))
#                elif "Born" in player_char.text:
#                    player.season = int(only_numerics(player_char.text))
#                elif "Balls" in player_char.text:
#                    player.totalskill = int(only_numerics(player_char.text))
#            money_info = float_right[0].find_all("span")
#            player.value = int(only_numerics(money_info[0].text))
#            player.salary = int(only_numerics(money_info[1].text))
#            count = 0
#            for player_skill in player_skills:
#                match count:
#                    case 0:
#                        player.speedscout = 0
#                        player.speed = int(only_numerics(player_skill.text))
#                    case 1:
#                        player.staminascout = 0
#                        player.stamina = int(only_numerics(player_skill.text))
#                    case 2:
#                        player.intelligencescout = 0
#                        player.intelligence = int(only_numerics(player_skill.text))
#                    case 3:
#                        player.passingscout = 0
#                        player.passing = int(only_numerics(player_skill.text))
#                    case 4:
#                        player.shootingscout = 0
#                        player.shooting = int(only_numerics(player_skill.text))
#                    case 5:
#                        player.headingscout = 0
#                        player.heading = int(only_numerics(player_skill.text))
#                    case 6:
#                        player.keepingscout = 0
#                        player.keeping = int(only_numerics(player_skill.text))
#                    case 7:
#                        player.controlscout = 0
#                        player.control = int(only_numerics(player_skill.text))
#                    case 8:
#                        player.tacklingscout = 0
#                        player.tackling = int(only_numerics(player_skill.text))
#                    case 9:
#                        player.aerialscout = 0
#                        player.aerial = int(only_numerics(player_skill.text))
#                    case 10:
#                        player.playsscout = 0
#                        player.plays = int(only_numerics(player_skill.text))
#                    case 11:
#                        player.experience = int(only_numerics(player_skill.text))
#                    case 12:
#                        player.form = int(only_numerics(player_skill.text))
#                count += 1
#            strongs = float_right[0].find_all("strong")
#            if add_player:
#                session.add(player)
#            transfer = Tranfers()
#            transfer.playerid = player.id
#            transfer.deadline = date_input(strongs[1].text, 0, time_zone)
#            transfer.askingprice = int(only_numerics(strongs[2].text))
#            strongs = float_right[1].find_all("strong")
#            transfer.actualprice = int(only_numerics(strongs[0].text))
#            if transfer.actualprice < transfer.askingprice:
#                transfer.actualprice = transfer.askingprice
#            transfer.active = 1
#            session.add(transfer)
#            count_transfer += 1
#            players.append(player.id)
#            reuse_players.append(player)
#        except Exception as e:
#            logging.error(e)
#    session.commit()
