import os
import re
import time
import pprint
import random
import getpass
from colorama import Style, Fore
from bs4 import BeautifulSoup as BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

def create_driver(proxy=""):
    try:
        firefox_options = Options()
        firefox_options.headless = True
        firefox_binary = FirefoxBinary("/usr/bin/firefox")
        executable_path = "/tmp/sim_user/drivers/geckodriver"
        log_path = "/tmp/sim_user/geckodriver.log"

        if proxy != "":
            firefox_capabilities = webdriver.DesiredCapabilities.FIREFOX
            firefox_capabilities["proxy"] = {
                "proxyType":"MANUAL",
                "httpProxy":proxy
            }
            return webdriver.Firefox(executable_path=executable_path,options=firefox_options,firefox_binary=firefox_binary,log_path=log_path,capabilities=firefox_capabilities)
        else:
            return webdriver.Firefox(executable_path=executable_path,options=firefox_options,firefox_binary=firefox_binary,log_path=log_path)
    except Exception as e :
        print( Fore.RED+ " => create_driver failed!    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL )
        print(e)

def get_current_page(driver=None, url=None):
    if driver == None and url == None:
        driver = create_driver()
        driver.get(url)
        driver.quit()
    if url:
        driver.get(url)
    else:
        driver.get(driver.current_url)

    return driver.page_source

def move_2_link(driver, verbose=True):
    try:
        soup = BeautifulSoup(driver.page_source, features='html.parser')
        links = soup.find_all(href=True)
        link = random.choice(links)
        
        if verbose:
            print(Fore.GREEN+" ==> [move_2_link] Old url: "+driver.current_url, end="")
        action = ActionChains(driver).move_to_element(driver.find_element_by_link_text(link.string)).pause(1)
        action.click().pause(1)
        action.perform()
        time.sleep(2)
        if verbose:
            print(" --> New url: "+driver.current_url+"-- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return 0
    except:
        print(Fore.RED+" ==> [move_2_link] failed!  -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return 1

################################# DVWA #################################

def dvwa_login_(driver, base_url, username, password):
    driver.get(base_url+"login.php")
    action = ActionChains(driver)

    action.move_to_element(driver.find_element_by_name("username")).pause(1)
    action.click().pause(1)
    action.send_keys(username).pause(1)

    action.move_to_element(driver.find_element_by_name("password")).pause(1)
    action.click().pause(1)
    action.send_keys(password).pause(1)

    action.send_keys(Keys.ENTER).pause(1)
    action.perform()
    time.sleep(2)
    driver.get(driver.current_url)
    time.sleep(2)

def dvwa_login(driver, base_url, username, password, verbose=True):
    try:
        dvwa_login_(driver, base_url, username, password)
        if driver.current_url == base_url+"setup.php":
            driver.find_element_by_name("create_db").location_once_scrolled_into_view
            action = ActionChains(driver)
            action.move_to_element(driver.find_element_by_name("create_db")).pause(1)
            action.click().pause(1)
            action.send_keys(Keys.ENTER).pause(1)
            action.perform()
            dvwa_login_(driver, base_url, username, password)
        if "index.php" in driver.current_url:
            if verbose:
                print(Fore.GREEN+ " ==> [dvwa_login] "+base_url+" was succesfull!    -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
            return 0
        print(Fore.RED+ " ==> [dvwa_login] "+base_url+" failed! #current_url: "+driver.current_url+"#   -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
        return 1
    except:
        print(Fore.RED+ " ==> [dvwa_login] "+base_url+" failed!  -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
        return 1

def dvwa_command_injection(driver,base_url,ip, verbose=True):
    driver.get(base_url+"vulnerabilities/exec")
    try:
        action = ActionChains(driver)
        action.move_to_element(driver.find_element_by_name("ip")).pause(1)
        action.click().pause(1)
        action.send_keys(ip).pause(1)
        action.move_to_element(driver.find_element_by_name("Submit")).pause(1)
        action.click().pause(5)
        action.perform()

        if 1 < len(driver.find_element_by_tag_name("pre").text):
            if verbose:
                print(Fore.GREEN+ " ==> [dvwa_command_injection] was succesfull!  ["+driver.find_element_by_tag_name("pre").text[:10]+" ... "+driver.find_element_by_tag_name("pre").text[-10:]+"]  -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
            return 0
        print(Fore.RED+ " ==> [dvwa_command_injection] failed! ["+driver.find_element_by_tag_name("pre").text+"] -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
        return 1
    except:
        print(Fore.RED+ " ==> [dvwa_command_injection] failed!  -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
        return 1

def dvwa_xss_reflected(driver, base_url, name, verbose=True):
    driver.get(base_url+"vulnerabilities/xss_r")
    try:
        action = ActionChains(driver)
        action.move_to_element(driver.find_element_by_name("name")).pause(1)
        action.click().pause(1)
        action.send_keys(getpass.getuser()).pause(1)
        action.send_keys(Keys.ENTER).pause(1)
        action.perform()

        if name in driver.find_element_by_tag_name("pre").text:
            if verbose:
                print(Fore.GREEN+ " ==> [dvwa_xss_reflected] was succesfull!  #"+driver.find_element_by_tag_name("pre").text+"#  -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
            return 0
        else:
            print(Fore.RED+ " ==> [dvwa_xss_reflected] failed!  #"+driver.find_element_by_tag_name("pre").text+"#  -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
            return 1
    except:
        print(Fore.RED+ " ==> [dvwa_xss_reflected] failed!  -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
        return 1

def change_security(driver, base_url, difficulty=1):
    driver.get(base_url+"security.php")
    time.sleep(3)

    diff_button = driver.find_element_by_name("security")
    diff_button.click()

    xpath = f"/html/body/div/div[3]/div/form/select/option[{difficulty}]"
    driver.find_element_by_xpath(xpath).click()
    time.sleep(1)
    driver.find_element_by_name("seclev_submit").click()
    time.sleep(1)
    return 0

################################# Chat-web-application #################################

def chat_web_application_login(driver, base_url, username, password, verbose=True):
    try:
        driver.get(base_url+"index.php")
        action = ActionChains(driver)

        action.move_to_element(driver.find_element_by_id("login_btn")).pause(1)
        action.click().pause(1)

        action.move_to_element(driver.find_element_by_id("login-uname")).pause(1)
        action.click().pause(1)
        action.send_keys(username).pause(1)

        action.move_to_element(driver.find_element_by_id("pass")).pause(1)
        action.click().pause(1)
        action.send_keys(password).pause(1)

        action.move_to_element(driver.find_element_by_name("loginbtn")).pause(1)
        action.click().pause(1)
        action.send_keys(Keys.ENTER).pause(1)
        action.perform()

        if "chat.php" in driver.current_url:
            if verbose:
                print(Fore.GREEN+ " ==> [chat_web_application_login] #login: "+username+"# was succesfull!    -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL)
            return 0
        else:
            print(Fore.RED+ " ==> [chat_web_application_login] #login: "+username+"# user can't log to the service!    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
            return 1
    except:
        print(Fore.RED+ " ==> [chat_web_application_login] #login: "+username+"# failed!    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        return 1

def chat_web_application_signup_(driver, base_url, username, email, password, verbose=True):
    try:
        driver.get(base_url+"index.php")
        action = ActionChains(driver)

        action.move_to_element(driver.find_element_by_id("signup_btn")).pause(1)
        action.click().pause(1)

        action.move_to_element(driver.find_element_by_id("signup-uname")).pause(1)
        action.click().pause(1)
        action.send_keys(username).pause(1)

        action.move_to_element(driver.find_element_by_id("email")).pause(1)
        action.click().pause(1)
        action.send_keys(email).pause(1)

        action.move_to_element(driver.find_element_by_id("pwd")).pause(1)
        action.click().pause(1)
        action.send_keys(password).pause(1)

        action.move_to_element(driver.find_element_by_id("rpwd")).pause(1)
        action.click().pause(1)
        action.send_keys(password).pause(1)

        action.move_to_element(driver.find_element_by_name("signupbtn")).pause(1)
        action.click().pause(1)
        action.send_keys(Keys.ENTER).pause(1)
        action.perform()

        if chat_web_application_login(driver, base_url, username, password, verbose=False) == 0:
            chat_web_application_logout(driver, verbose=False)
            if verbose:
                print( Fore.GREEN+ " ==> [chat_web_application_signup_] #signup-name: "+username+"# was succesfull!    -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL )
            return 0
        else:
            print( Fore.RED+ " ==> [chat_web_application_signup_] #signup-name: "+username+"# can't sign up!    -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL )
            return 1
    except:
        print( Fore.RED+ " ==> [chat_web_application_signup_] #signup-name: "+username+"# failed!    -- "+ time.strftime("%H:%M:%S", time.localtime())+ Style.RESET_ALL )
        return 1

def chat_web_application_search_user(driver, username, verbose=True):
    try:
        action = ActionChains(driver)

        action.move_to_element(driver.find_element_by_xpath("/html/body/main/div/div/input[@id='search']")).pause(1)
        action.click().pause(1)
        action.send_keys(username).pause(1)

        action.move_to_element(driver.find_element_by_xpath("/html/body/main/div/div[@class='subelement62']/button[@id='send_button']")).pause(1)
        action.click().pause(1)
        action.send_keys(Keys.ENTER).pause(1)
        action.perform()
        time.sleep(3)

        if username == driver.find_element_by_xpath("/html/body/main/div/ul[@id='contacts']/li/div[@class='pelement3']/h1").text:
            if verbose:
                print(Fore.GREEN+ " ==> [chat_web_application_search_user] #username: "+username+"# was successfull!   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
            return 0
        else:
            print(Fore.RED+ " ==> [chat_web_application_search_user] #username: "+username+"# can't find user: "+username+" !    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
            return 1
    except:
        print(Fore.RED+ " ==> [chat_web_application_search_user] #username: "+username+"# failed!    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        return 1

def chat_web_application_send_msg(driver, username, msg, verbose=True):
    try:
        msg = msg.strip()
        action = ActionChains(driver)
        contacts = driver.find_elements_by_xpath("/html/body/main/div/ul[@id='contacts']/*")
        for contact in contacts:
            if username == driver.find_element_by_xpath("/html/body/main/div/ul[@id='contacts']/li/div[@class='pelement3']/h1").text:
                action.move_to_element(contact).pause(1)
                action.click().pause(3)
        
        action.move_to_element(driver.find_element_by_id("msg")).pause(1)
        action.click().pause(1)
        action.send_keys(msg).pause(1)

        action.move_to_element(driver.find_element_by_xpath("/html/body/main/div/div/button[@id='send_button']")).pause(1)
        action.click().pause(5)
        action.perform()

        time.sleep(4)
        if msg in driver.find_element_by_id("box4").text:
            if verbose:
                print(Fore.GREEN+ " ==> [chat_web_application_send_msg] #receiver :"+username+"# was succesfull!     -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
            return 0
        print(Fore.RED+ " ==> [chat_web_application_send_msg] can't send message!    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        return 1
    except:
        print(Fore.RED+ " ==> [chat_web_application_send_msg] #username :"+username+"# failed!    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        return 1

def chat_web_application_logout(driver, verbose=True):
    try:
        action = ActionChains(driver)
        action.move_to_element(driver.find_element_by_xpath("/html/body/main/div/div[@class='subelement13']"))
        action.click().pause(3)
        action.perform()
        if ("index.php" in driver.current_url):
            if verbose:
                print( Fore.GREEN+ " ==> [chat_web_application_logout] was succefull!    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL )
        else:
            print( Fore.RED+ " ==> [chat_web_application_logout] can't log out!    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL )
    except:
        print( Fore.RED+ " ==> [chat_web_application_logout] failed!    -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL )

################################ Gnu social ###################################

def gnu_social_register_account(driver, url, nickname, password, email, fullname, bio, location, verbose=True):
    captcha=""
    driver.get(url+"index.php/main/register")

    action = ActionChains(driver)
    action.move_to_element(driver.find_element_by_id("nickname")).pause(1)
    action.click().pause(1)
    action.send_keys(nickname).pause(1)

    action.move_to_element(driver.find_element_by_id("password")).pause(1)
    action.click().pause(1)
    action.send_keys(password).pause(1)

    action.move_to_element(driver.find_element_by_id("confirm")).pause(1)
    action.click().pause(1)
    action.send_keys(password).pause(1)

    action.move_to_element(driver.find_element_by_id("email")).pause(1)
    action.click().pause(1)
    action.send_keys(email).pause(1)

    action.move_to_element(driver.find_element_by_id("fullname")).pause(1)
    action.click().pause(1)
    action.send_keys(fullname).pause(1)
    action.perform()

    driver.find_element_by_id("bio").location_once_scrolled_into_view
    for li in driver.find_elements_by_xpath("/html/body/div/div/div/div/div/div/div/form/fieldset/ul/li"):
        if "Captcha" in li.text:
            captcha = re.findall(r'"(.*?)"', li.text)[0]
    action = ActionChains(driver)
    action.move_to_element(driver.find_element_by_id("bio")).pause(1)
    action.click().pause(1)
    action.send_keys(bio).pause(1)

    action.move_to_element(driver.find_element_by_id("location")).pause(1)
    action.click().pause(1)
    action.send_keys(location).pause(1)

    action.move_to_element(driver.find_element_by_id("simplecaptcha")).pause(1)
    action.click().pause(1)
    action.send_keys(captcha).pause(1)

    action.move_to_element(driver.find_element_by_id("license")).pause(1)
    action.click().pause(1)

    action.move_to_element(driver.find_element_by_id("submit")).pause(1)
    action.click().pause(1)
    action.perform()

    if gnu_social_login(driver, url, nickname, password, verbose=False) == 0:
        if verbose:
            print(Fore.GREEN+ " ==> [gnu_social_register_account] #nickname: "+nickname+"# was successfull!   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        return 0
    print(Fore.RED+ " ==> [gnu_social_register_account] failed!   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
    return 1

def gnu_social_login(driver, url, nickname, password, verbose=True):
    driver.get(url+"index.php/main/login")

    action = ActionChains(driver)
    action.move_to_element(driver.find_element_by_id("nickname")).pause(1)
    action.click().pause(1)
    action.send_keys(nickname).pause(1)

    action.move_to_element(driver.find_element_by_id("password")).pause(1)
    action.click().pause(1)
    action.send_keys(password).pause(1)

    action.move_to_element(driver.find_element_by_id("submit")).pause(1)
    action.click().pause(1)
    action.perform()

    if nickname in driver.current_url:
        if verbose:
            print(Fore.GREEN+ " ==> [gnu_social_login] #nickname: "+nickname+"# was successfull!   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        return 0
    print(Fore.RED+ " ==> [gnu_social_login] failed!   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
    return 1

def gnu_social_send_status(driver, url, status="Example status", verbose=True):
    driver.get(url+"index.php/main/public")

    action = ActionChains(driver)
    action.move_to_element(driver.find_element_by_name("status_textarea")).pause(1)
    action.click().pause(1)
    action.send_keys(status).pause(1)

    action.move_to_element(driver.find_element_by_id("notice_action-submit")).pause(1)
    action.click().pause(1)
    action.perform()

def gnu_social_read_timeline(driver, url):
    status = []
    driver.get(url+"index.php/main/public")

    i = 0
    for author in driver.find_elements_by_xpath("/html/body/div/div/div/div/div/div/div/div/ol/li/section"):
        status.append({"author":author.text})
        i= i+1

    i = 0
    for content in driver.find_elements_by_xpath("/html/body/div/div/div/div/div/div/div/div/ol/li/article"):
        status[i]["content"] = content.text
        i=i+1

    i = 0
    for timestamp in driver.find_elements_by_xpath("/html/body/div/div/div/div/div/div/div/div/ol/li/footer/a[@class='timestamp']"):
        status[i]["timestamp"] = timestamp.text
        i=i+1

    return status