import os
import random
import json
import getpass
import socket
from colorama import Fore, Style
from sim_web import dvwa, chat_web_application_signup, chat_web_application, gnu_social_signup, gnu_social
from sim_mail import mail_cycle, read_mailbox_download_execute
from sim_smb import smb_cycle
from sim_attack import attack_cycle
from sim_ssh import upgrade_python_lib, restart_apache_service, upgrade_food_delivery

def load_json_file(path_conf):
    with open(path_conf, "r") as f:
        conf_physic = json.load(f)
    return conf_physic

def choose_action(action_name, args):
    if action_name =="dvwa":
        dvwa(args)
    elif action_name == "attack_cycle":
        attack_cycle(args)
    elif action_name == "mail_cycle":
        mail_cycle(args)
    elif action_name == "smb_cycle":
        smb_cycle(args)
    elif action_name == "chat_web_application_signup":
        chat_web_application_signup(args)
    elif action_name == "chat_web_application":
        chat_web_application(args)
    elif action_name == "gnu_social_signup":
        gnu_social_signup(args)
    elif action_name == "gnu_social":
        gnu_social(args)
    elif action_name == "upgrade_food_delivery":
        upgrade_food_delivery(args)
    elif action_name == "read_mailbox_download_execute":
        read_mailbox_download_execute(args)
    else:
        print(Fore.YELLOW+ action_name +" does'nt exist!" +Style.RESET_ALL)

def simulation():
    os.chdir("/sim_user/")
    username = getpass.getuser()
    hostname = socket.gethostname()
    print("Begin simulation with user: "+Fore.GREEN+username+Style.RESET_ALL+" and workstation: "+Fore.GREEN+hostname+Style.RESET_ALL)
    users = load_json_file("/sim_user/users.json")

    max_rep = 0
    for user in users["users"]:
        if username == user["name"]:
            for scenari in user["scenarios"]:
                max_rep_tmp = int(scenari["begin"]) + int(scenari["rep"])
                if max_rep_tmp > max_rep:
                    max_rep = max_rep_tmp

    for i in range(max_rep):
        for user in users["users"]:
            if user["name"] == username:
                for scenari in user["scenarios"]:
                    if i >= int(scenari["begin"]) and i <= int(scenari["begin"])+int(scenari["rep"]):
                        print(Fore.YELLOW+ "[ " +scenari["name"]+ " ]" +Style.RESET_ALL)
                        choose_action(scenari["name"], scenari["args"])

############################
########### MAIN ###########
############################
simulation()
