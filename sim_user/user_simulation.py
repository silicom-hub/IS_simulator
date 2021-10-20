import random
import json
import getpass
import socket
from colorama import Fore, Style


from sim_web import dvwa, dvwa_attack, chat_web_application_signup, chat_web_application
from sim_mail import mail_cycle
from sim_smb import smb_cycle

def load_json_file(path_conf):
    with open(path_conf, "r") as f:
        conf_physic = json.load(f)
    return conf_physic

def choose_action(action_name, args):
    if action_name =="dvwa":
        dvwa(args)
    elif action_name == "dvwa_attack":
        dvwa_attack(args)
    elif action_name == "mail_cycle":
        mail_cycle(args)
    elif action_name == "smb_cycle":
        smb_cycle(args)
    elif action_name == "chat_web_application_signup":
        chat_web_application_signup(args)
    elif action_name == "chat_web_application":
        chat_web_application(args)
    
    else:
        print(Fore.YELLOW+ action_name +" does'nt exist!" +Style.RESET_ALL)

def simulation():
    username = getpass.getuser()
    hostname = socket.gethostname()
    print("Begin simulation with user: "+Fore.GREEN+username+Style.RESET_ALL+" and workstation: "+Fore.GREEN+hostname+Style.RESET_ALL)
    users = load_json_file("/tmp/sim_user/users.json")

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