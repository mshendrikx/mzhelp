import os
import math
import time
import random
import asyncio

from requests import session
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
    Bids,
)
from project.common import (
    get_db,
    only_numerics,
    countries_data,
    get_utc_string,
    process_training_data,
    utc_input,
    date_input,
)

from . import logger

load_dotenv()


def job_nations():
    session = get_db()

    with SB(
        # browser="chrome",
        headless=True,
        uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST", None),
        port=os.environ.get("SELENIUM_HUB_PORT", None),
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
        # browser="chrome",
        headless=True,
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


def job_transfers():

    count_transfer = 0

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
        logger.warning("No searches to process")
        return

    logger.info(f"Start Seleniumbase")
    with SB(
        # browser="chrome",
        headless=True,
        uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST", None),
        port=os.environ.get("SELENIUM_HUB_PORT", None),
    ) as sb:
        logger.info(f"Seleniumbase loaded")
        logger.info(f"Open ManagerZone")
        sb.open("https://www.managerzone.com/")
        logger.info(f"Confirm cookies")
        sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
        logger.info(f"Enter login data")
        sb.type('input[id="login_username"]', os.environ.get("MZUSER"))
        sb.type('input[id="login_password"]', os.environ.get("MZPASS"))
        logger.info(f"Click Login button")
        sb.click('a[id="login"]')
        logger.info(f"Wait for start page load")
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

        logger.info("Start SOUP data")
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
                        logger.error(message)
                        logger.error(e)
                        break

        except Exception as e:
            logger.error(e)

        logger.info("End SOUP data")

        utc_now = utc_input()

        session.query(Transfers).filter(
            Transfers.deadline < utc_now, Transfers.active == 1
        ).update({"active": 0})

        session.commit()

        logger.info("Start basic player data")
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
                    if player_id in players:
                        continue
                    player_name = header.find(class_="player_name").text
                    del player
                    player = session.query(Players).filter_by(id=player_id).first()
                    if not player:
                        message = "Add player: " + str(player_id) + " " + player_name
                        logger.info(message)
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
                        logger.info(message)
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
                            player.speedscout = 1
                        else:
                            player.speedscout = 2
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
                            player.staminascout = 1
                        else:
                            player.staminascout = 2
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
                            player.intelligencescout = 1
                        else:
                            player.intelligencescout = 2
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
                            player.passingscout = 1
                        else:
                            player.passingscout = 2
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
                            player.shootingscout = 1
                        else:
                            player.shootingscout = 2
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
                            player.headingscout = 1
                        else:
                            player.headingscout = 2
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
                            player.keepingscout = 1
                        else:
                            player.keepingscout = 2
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
                            player.controlscout = 1
                        else:
                            player.controlscout = 2
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
                            player.tacklingscout = 1
                        else:
                            player.tacklingscout = 2
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
                            player.aerialscout = 1
                        else:
                            player.aerialscout = 2
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
                            player.playsscout = 1
                        else:
                            player.playsscout = 2
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

                    transfer = (
                        session.query(Transfers)
                        .filter(Transfers.playerid == player.id, Transfers.active == 1)
                        .first()
                    )
                    if not transfer:
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
                    logger.error(e)

            session.commit()

        logger.info("End basic player data")

        logger.info("Start training data")
        # Training Data
        utc_now = utc_input()
        session.query(Transfers).filter(
            Transfers.deadline < utc_now, Transfers.active == 1
        ).update({"active": 0})
        session.commit()
        transfers = (
            session.query(Transfers)
            .filter(Transfers.active == 1)
            .order_by(Transfers.deadline)
            .all()
        )

        for transfer in transfers:
            url = (
                "https://www.managerzone.com/ajax.php?p=trainingGraph&sub=getJsonTrainingHistory&sport=soccer&player_id="
                + str(transfer.playerid)
            )
            player_training = (
                session.query(PlayersTraining).filter_by(id=transfer.playerid).first()
            )
            if not player_training:
                player_training = PlayersTraining()
                player_training.id = transfer.playerid
                session.add(player_training)

            player_training.trainingdate = utc_input()

            try:
                sb.open(url)
                sb.wait_for_element("/html/body", timeout=1)
                player_training.trainingdata = process_training_data(
                    sb.driver.page_source
                )
                session.commit()
            except Exception as e:
                logger.error(
                    "Error processing training data for player ID %s: %s",
                    transfer.playerid,
                    e,
                )
                continue

        logger.info("End training data")


def job_teams():

    return


def job_bid(userid):

    session = get_db()

    user = session.query(Users).filter_by(id=userid).first()
    if not user:
        return

    utc_int = utc_input()
    bids = (
        session.query(Bids)
        .filter(Bids.userid == userid, Bids.dtstart < utc_int, Bids.active == 1)
        .all()
    )

    if bids:

        with SB(
            # browser="chrome",
            headless=True,
            uc=True,
            servername=os.environ.get("SELENIUM_HUB_HOST", None),
            port=os.environ.get("SELENIUM_HUB_PORT", None),
        ) as sb:
            try:
                sb.open("https://www.managerzone.com/")
                sb.click(
                    'button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]'
                )
                sb.type('input[id="login_username"]', user.mzuser)
                sb.type('input[id="login_password"]', user.mzpass)
                sb.click('a[id="login"]')
                sb.wait_for_element('//*[@id="header-stats-wrapper"]/h5[3]')
            except Exception as e:
                logger.error("Error logging in user: " + str(userid))
                logger.error(e)
                return

            while bids:

                for bid in bids:
                    transfer = (
                        session.query(Transfers)
                        .filter_by(id=bid.transferid, active=1)
                        .first()
                    )
                    try:
                        sb.open(
                            f"https://www.managerzone.com/?p=transfer&sub=players&u={transfer.playerid}"
                        )
                        sb.wait_for_element('//*[@id="thePlayers_0"]')
                        sb.click(
                            '//*[@id="thePlayers_0"]/div/div/div[2]/div/div[2]/table/tbody/tr/td[2]/span[1]/a'
                        )
                        next_bid = math.ceil(
                            int(
                                only_numerics(
                                    sb.get_text(
                                        '//*[@id="lightboxContent_transfer_buy_form"]/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td/div/div/dl/dd[4]/span[2]'
                                    ).split("R$")[0]
                                )
                            )
                            * 1.05
                        )
                    except Exception as e:
                        try:
                            sb.wait_for_element('//*[@id="players_container"]/div/p')
                            if (
                                sb.get_text('//*[@id="players_container"]/div/p')
                                == "Waiting for playerlist"
                            ):
                                transfer.active = 0
                                bid.active = 0
                                session.commit()
                        except:
                            continue
                        continue

                    if next_bid <= bid.maxbid:
                        try:
                            sb.wait_for_element('//*[@id="transfer_place_bid_button"]')
                            sb.execute_script(
                                "window.confirm = function() { return true; }"
                            )
                            sb.click('//*[@id="transfer_place_bid_button"]')
                        except:
                            continue

                    try:
                        sb.open(
                            f"https://www.managerzone.com/?p=transfer&sub=players&u={transfer.playerid}"
                        )
                        latest_bid = int(
                            only_numerics(
                                sb.get_text(
                                    '//*[@id="thePlayers_0"]/div/div/div[2]/div/div[2]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/strong'
                                )
                            )
                        )
                        transfer.actualprice = latest_bid
                        bid.finalvalue = latest_bid
                        deadline_str = sb.get_text(
                            '//*[@id="thePlayers_0"]/div/div/div[2]/div/div[1]/table/tbody/tr[3]/td[2]/strong'
                        )
                        transfer.deadline = date_input(date=deadline_str)
                        session.commit()
                    except Exception as e:
                        logger.error(
                            "Error updating bid and transfer info for user: "
                            + str(userid)
                            + " transferid: "
                            + str(transfer.id)
                        )
                        logger.error(e)
                        continue

                time.sleep(random.randint(45, 60))
                utc_int = utc_input()
                bids = (
                    session.query(Bids)
                    .filter(Bids.dtstart < utc_int, Bids.active == 1)
                    .all()
                )


def job_claim(userid):

    session = get_db()

    user = session.query(Users).filter_by(id=userid).first()
    if not user:
        return

    with SB(
        # browser="chrome",
        headless=True,
        uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST", None),
        port=os.environ.get("SELENIUM_HUB_PORT", None),
    ) as sb:
        try:
            sb.open("https://www.managerzone.com/")
            sb.click(
                'button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]'
            )
            sb.type('input[id="login_username"]', user.mzuser)
            sb.type('input[id="login_password"]', user.mzpass)
            sb.click('a[id="login"]')
            sb.wait_for_element('//*[@id="header-stats-wrapper"]/h5[3]')
        except Exception as e:
            logger.error("Error logging in user: " + str(userid))
            logger.error(e)
            return


def job_team(userid):

    session = get_db()

    user = session.query(Users).filter_by(id=userid).first()
    if not user:
        return

    with SB(
        # browser="chrome",
        headless=True,
        uc=True,
        servername=os.environ.get("SELENIUM_HUB_HOST", None),
        port=os.environ.get("SELENIUM_HUB_PORT", None),
    ) as sb:
        try:
            sb.open("https://www.managerzone.com/")
            sb.click(
                'button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]'
            )
            sb.type('input[id="login_username"]', user.mzuser)
            sb.type('input[id="login_password"]', user.mzpass)
            sb.click('a[id="login"]')
            sb.wait_for_element('//*[@id="header-stats-wrapper"]/h5[3]')
        except Exception as e:
            logger.error("Error logging in user: " + str(userid))
            logger.error(e)
            return

        sb.open("https://www.managerzone.com/?p=players")

        try:
            sb.wait_for_element('//*[@id="thePlayers_0"]', timeout=10)
            players_container = sb.find_elements("#players_container")
            soup = BeautifulSoup(players_container.get_attribute("outerHTML"), "lxml")
            players_soup = soup.find_all(class_="playerContainer")
        except Exception as e:
            logger.error("Error loading team page for user: " + str(userid))
            logger.error(e)
            return

        

        for player_soup in players_soup:
            try:
                header = player_soup.h2
                player_id = 0
                player_id = int(header.find(class_="player_id_span").text)
                player_name = header.find(class_="player_name").text
            except Exception as e:
                logger.error("Error parsing player info for user: " + str(userid))
                logger.error(e)
                continue


        for player in players_container:
            try:
                player.get_e
                sb.wait_for_element('//*[@id="transfer_place_bid_button"]')
                sb.execute_script("window.confirm = function() { return true; }")
                sb.click('//*[@id="transfer_place_bid_button"]')
            except Exception as e:
                logger.error("Error buying player for user: " + str(userid))
                logger.error(e)
                return

    return
