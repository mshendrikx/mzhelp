import os

from seleniumbase import SB
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from project.models import Player, PlayerTraining, Countries, Tranfers, Mzcontrol
from project.common import (
    get_db,
    only_numerics,
    countries_data,
    get_utc_string,
    format_training_data,
    set_player_scout,
    utc_input,
    date_input,
    get_player_maxs,
)

from dotenv import load_dotenv

load_dotenv()

session = get_db()

utc_string = get_utc_string(format="%Y-%m-%d")


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


with SB(uc=True) as sb:
    sb.open("https://www.managerzone.com/")
    sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
    sb.type('input[id="login_username"]', os.environ.get("MZUSER"))
    sb.type('input[id="login_password"]', os.environ.get("MZPASS"))
    sb.click('a[id="login"]')
    sb.open(
        "https://www.managerzone.com/ajax.php?p=settings&sub=profile-change&sport=soccer"
    )

    # Get Time Zone
    sb.wait_for_element('//*[@id="profile"]/div[4]/div/select')
    select_element = sb.find_element('//*[@id="profile"]/div[4]/div/select')
    select = Select(select_element)
    selected_option = select.first_selected_option
    time_zone = selected_option.text

    sb.open("https://www.managerzone.com/?p=transfer")
    sb.wait_for_element('//*[@id="players_container"]')
    utc_string = get_utc_string(format="%Y-%m-%d")

    searches = get_transfer_searches(session.query(Countries).all())
    pages_soup = []

    # update control table with deadline
    mzcontrol = session.query(Mzcontrol).first()
    deadline_control = mzcontrol.deadline
    utc_string = get_utc_string(format="%d/%m/%Y %I:%M%p")
    mzcontrol.deadline = date_input(utc_string, 1, "UTC")
    session.commit()

    for search in searches:
        sb.click_xpath('//*[@id="resetb"]')
        sb.select_option_by_value('//*[@id="deadline"]', "3")
        sb.select_option_by_value('//*[@id="nationality"]', search[0])
        sb.type('input[id="agea"]', search[1])
        sb.type('input[id="ageb"]', search[2])
        sb.click_xpath('//*[@id="searchb"]')
        next_link = True
        while next_link:
            sb.wait_for_element('//*[@id="players_container"]')
            players_container = sb.find_element("#players_container")
            soup = BeautifulSoup(players_container.get_attribute("outerHTML"), "lxml")
            pages_soup.append(soup)
            try:
                button_next = sb.find_element(
                    "div.transferSearchPages a:contains('Next')", timeout=2
                )
                button_next.click()
            except:
                next_link = False
            break
        break

    countries = countries_data(index=1)
    utc_now = utc_input()
    transfers_db = session.query(Tranfers).filter(Tranfers.deadline >= utc_now).all()
    players_db = []
    for transfer_db in transfers_db:
        players_db.append(transfer_db.playerid)

    for page_soup in pages_soup:
        players_soup = page_soup.find_all(class_="playerContainer")
        players = []
        players_training = []

        for player_soup in players_soup:
            header = player_soup.h2
            player_id = int(header.find(class_="player_id_span").text)
            if player_id in players_db:
                continue
            player = session.query(Player).filter_by(id=player_id).first()
            if not player:
                player = Player()
                player.id = player_id
                player.country = 0
                player.teamid = 0
                player.number = 0
                player.retiring = 0
                player.national = 0
                session.add(player)

            player.changedat = utc_input()
            player.country = countries[header.div.img.get("title")].id
            player.name = header.find(class_="player_name").text
            float_left = player_soup.find(class_="floatLeft")
            float_left = float_left.table.tbody
            float_left = float_left.find_all("tr")
            player_chars = float_left[0].find_all("tr")
            player_skills = float_left[8].find_all("tr")
            float_right = player_soup.find(class_="floatRight transfer-control-area")
            float_right = float_right.find_all(class_="box_dark")
            scout_report = float_right[1].find(title="Scout report")
            training_graph = float_right[1].find(
                class_="fa-regular fa-chart-line-up training-graphs-icon"
            )
            if scout_report == None:
                player.starhigh = 0
                player.starlow = 0
                player.startraining = 0

            if training_graph == None:
                player.traininginfo = 0
            else:
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

            count = 0
            for player_skill in player_skills:
                match count:
                    case 0:
                        player.speedscout = 0
                        player.speed = int(only_numerics(player_skill.text))
                    case 1:
                        player.staminascout = 0
                        player.stamina = int(only_numerics(player_skill.text))
                    case 2:
                        player.intelligencescout = 0
                        player.intelligence = int(only_numerics(player_skill.text))
                    case 3:
                        player.passingscout = 0
                        player.passing = int(only_numerics(player_skill.text))
                    case 4:
                        player.shootingscout = 0
                        player.shooting = int(only_numerics(player_skill.text))
                    case 5:
                        player.headingscout = 0
                        player.heading = int(only_numerics(player_skill.text))
                    case 6:
                        player.keepingscout = 0
                        player.keeping = int(only_numerics(player_skill.text))
                    case 7:
                        player.controlscout = 0
                        player.control = int(only_numerics(player_skill.text))
                    case 8:
                        player.tacklingscout = 0
                        player.tackling = int(only_numerics(player_skill.text))
                    case 9:
                        player.aerialscout = 0
                        player.aerial = int(only_numerics(player_skill.text))
                    case 10:
                        player.playsscout = 0
                        player.plays = int(only_numerics(player_skill.text))
                    case 11:
                        player.experience = int(only_numerics(player_skill.text))
                    case 12:
                        player.form = int(only_numerics(player_skill.text))

                count += 1
            strongs = float_right[0].find_all("strong")
            transfer = Tranfers()
            transfer.playerid = player.id
            transfer.deadline = date_input(strongs[1].text, 0, time_zone)
            transfer.askingprice = int(only_numerics(strongs[2].text))
            strongs = float_right[1].find_all("strong")
            transfer.actualprice = int(only_numerics(strongs[0].text))
            if transfer.actualprice < transfer.askingprice:
                transfer.actualprice = transfer.askingprice
            session.add(transfer)
            session.commit()
            players.append(player)

        # Scout and Training Data
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

            if player.traininginfo == 1:
                player_training = (
                    session.query(PlayerTraining).filter_by(id=player.id).first()
                )
                if not player_training:
                    player_training = PlayerTraining()
                    player_training.id = player.id
                    session.add(player_training)
                player_training.trainingdate = utc_input()
                url = (
                    "https://www.managerzone.com/ajax.php?p=trainingGraph&sub=getJsonTrainingHistory&sport=soccer&player_id="
                    + str(player_training.id)
                )
                sb.open(url)
                player_training.trainingdata = format_training_data(
                    sb.driver.page_source
                )
                maxs = get_player_maxs(player_training.trainingdata)

                if 1 in maxs:
                    player.speedmax = 1
                else:
                    player.speedmax = 0
                if 2 in maxs:
                    player.staminamax = 1
                else:
                    player.staminamax = 0
                if 3 in maxs:
                    player.intelligencemax = 1
                else:
                    player.intelligencemax = 0
                if 4 in maxs:
                    player.passingmax = 1
                else:
                    player.passingmax = 0
                if 5 in maxs:
                    player.shootingmax = 1
                else:
                    player.shootingmax = 0
                if 6 in maxs:
                    player.headingmax = 1
                else:
                    player.headingmax = 0
                if 7 in maxs:
                    player.keepingmax = 1
                else:
                    player.keepingmax = 0
                if 8 in maxs:
                    player.controlmax = 1
                else:
                    player.controlmax = 0
                if 9 in maxs:
                    player.tacklingmax = 1
                else:
                    player.tacklingmax = 0
                if 10 in maxs:
                    player.aerialmax = 1
                else:
                    player.aerialmax = 0
                if 11 in maxs:
                    player.playsmax = 1
                else:
                    player.playsmax = 0
            else:
                if player.speedmax != 1:
                    player.speedmax = 2
                if player.staminamax != 1:
                    player.staminamax = 2
                if player.intelligencemax != 1:
                    player.intelligencemax = 2
                if player.passingmax != 1:
                    player.passingmax = 2
                if player.shootingmax != 1:
                    player.shootingmax = 2
                if player.headingmax != 1:
                    player.headingmax = 2
                if player.keepingmax != 1:
                    player.keepingmax = 2
                if player.controlmax != 1:
                    player.controlmax = 2
                if player.tacklingmax != 1:
                    player.tacklingmax = 2
                if player.aerialmax != 1:
                    player.aerialmax = 2
                if player.playsmax != 1:
                    player.playsmax = 2

            session.commit()
