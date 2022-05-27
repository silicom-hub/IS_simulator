import os
import time
import pprint
import random
import socket
import getpass
import datetime
import threading
from colorama import Fore, Style
from essential_generators import DocumentGenerator
from webLib import create_driver, dvwa_login, dvwa_command_injection, dvwa_xss_reflected, move_2_link, change_security, chat_web_application_login, chat_web_application_signup_, chat_web_application_search_user, chat_web_application_send_msg, chat_web_application_logout, gnu_social_register_account, gnu_social_login, gnu_social_send_status, gnu_social_read_timeline, move_2_random_link

def dvwa(args):
    """ Execute multiple user action on dvwa server.
        args (dict of str): This argument list maps arguments and their value.
            {
                url (str): This value is the website's url.
                nb_actions (int): This value is the number of actions performed.
                proxy (str Optional):
            }
    
    Returns:
        None
    """
    base_url = args["url"]
    username = "admin"
    password = "password"
    driver = create_driver(proxy=args["proxy"])
    if driver == 1:
        return 1
    driver.implicitly_wait(10)

    actions = ["dvwa_command_injection","dvwa_xss_reflected","move_2_random_link"]

    dvwa_login(driver, base_url, username, password)
    for i in range(int(args["nb_actions"])):
        action = random.choices(actions, weights=[5,5,5])
        time.sleep(random.randint(10,30))
        if action == ["dvwa_command_injection"]:
            change_security(driver, base_url)
            dvwa_command_injection(driver, base_url, "8.8.8.8")
        elif action == ["dvwa_xss_reflected"]:
            dvwa_xss_reflected(driver, base_url, getpass.getuser())
        elif action == ["move_2_random_link"]:
            move_2_random_link(driver)

    driver.close()
    driver.quit()

def chat_web_application_signup(args):
    """ Create an account on the chat application.
        args (dict of str): This argument list maps arguments and their value.
            {
                url (str): This value is the website's url.
                username (str): This value is username on the chat application who will represent the user.
                password (str): This value is the user's password o this chat application.
                email (str): This value is the user's email for the subcription.
                proxy (str Optional):
            }
    Returns:
        None
    """
    base_url = args["url"]
    username = args["username"]
    email = args["email"]
    password = args["password"]
    driver = create_driver(proxy=args["proxy"])
    if driver == 1:
        return 1
    driver.implicitly_wait(10)

    chat_web_application_signup_(driver, base_url, username, email, password)

    driver.close()
    driver.quit()

def chat_web_application(args):
    """ Execute multiple attack and scan as new workstations and servicesare discovered.
        args (dict of str): This argument list maps arguments and their value.
            {
                url (str): This value is the website's url.
                username (str): This value is the username on this web application.
                password (str): This value is the password on this web application.
                receivers (list): This value is a list of multiple username wich the user who can send messages.
                proxy (str Optional): 
            }
    Returns:
        None
    """
    base_url = args["url"]
    username = args["username"]
    receivers = args["receivers"]
    password = args["password"]
    
    gen = DocumentGenerator()

    driver = create_driver(proxy=args["proxy"])
    if driver == 1:
        return 1
    driver.implicitly_wait(10)

    if chat_web_application_login(driver, base_url, username, password, verbose=False) == 0:
        for i in range(int(args["nb_actions"])):
            receiver = random.choice(receivers)
            if chat_web_application_search_user(driver, receiver, verbose=False) == 0:
                chat_web_application_send_msg(driver, receiver, gen.sentence())
    
        chat_web_application_logout(driver, verbose=False)
    time.sleep(10)
    driver.close()
    driver.quit()

def gnu_social_signup(args):
    """ Execute multiple attack and scan as new workstations and servicesare discovered.
        args (dict of str): This argument list maps arguments and their value.
            {
                url (str): This value is the website's url.
                nickname (str): This value is the username on this website.
                password (list): This value is the user's password on this website.
                email (list): This value is the user's email for the subcription.
                fullname (list): This value is the complete 
                bio (list): This value is a user's description.
                location (str): email (str): This value is the user's location.
                proxy (str Optional):
            }
    Returns:
        None
    """
    url = args["url"]
    nickname = args["nickname"]
    password = args["password"]
    email = args["email"]
    fullname = args["fullname"]
    bio = args["bio"]
    location = args["location"]

    driver = create_driver(proxy=args["proxy"])
    driver.implicitly_wait(10)

    gnu_social_register_account(driver, url, nickname, password, email, fullname, bio, location, verbose=True)

    time.sleep(4)
    driver.close()
    driver.quit()

def gnu_social(args):
    """ Execute multiple attack and scan as new workstations and servicesare discovered.
        args (dict of str): This argument list maps arguments and their value.
            {
                url (str): This value is the website's url.
                nickname (str): This value is the username on this website.
                password (list): This value is the user's password on this website.
                proxy (str Optional):
            }
    Returns:
        None
    """
    url = args["url"]
    nickname = args["nickname"]
    password = args["password"]

    driver = create_driver(proxy=args["proxy"])
    if driver == 1:
        return 1
    driver.implicitly_wait(10)

    gen = DocumentGenerator()

    if gnu_social_login(driver, url, nickname, password, verbose=False) == 0:
        gnu_social_send_status(driver, url, gen.sentence())
    # gnu_social_read_timeline(driver, url)
    time.sleep(4)
    driver.close()
    driver.quit()
