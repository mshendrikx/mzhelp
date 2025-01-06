import os

from seleniumbase import SB
from dotenv import load_dotenv

load_dotenv()

with SB(uc=True) as sb:
    sb.open("https://www.managerzone.com/")
    sb.click('button[id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]')
    sb.type('input[id="login_username"]', os.getenv("MZUSER"))
    sb.type('input[id="login_password"]', os.getenv("MZPASS"))
    sb.click('a[id="login"]')
    
    sb.open("https://www.managerzone.com/?p=transfer")

    next_page = True

    while next_page == True:
        try:
            sb.click('a:contains("Next")')
        except Exception as e:
            next_page = False
    
    breakpoint    
