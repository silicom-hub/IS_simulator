import os
import time
import random
from smbLib import connect_samba_server, get_service_name, get_remote_dir, upload, download

def smb_cycle(args):
    username = args["username"]
    password = args["password"]
    service_name = args["service_name"]
    workstation_name = args["workstation_name"]
    server_name = args["server_name"]
    server_ip = args["server_ip"]

    actions = ["upload","download"]
    smb_session = connect_samba_server(username,password,workstation_name,server_name,server_ip)
    for i in range(int(args["nb_actions"])):
        action = random.choices(actions, weights=[1,1])
        time.sleep(random.randint(10,30))
        if action == ["upload"]:
            print(" => "+str(action[0])+"                 -- "+time.strftime("%H:%M:%S", time.localtime()))
            try:
                upload(smb_session,service_name,"/","","/tmp/Documents/")
            except:
                print("Error durind upload")
        elif action == ["download"]:
            print(" => "+str(action[0])+"               -- "+time.strftime("%H:%M:%S", time.localtime()))
            try:
                download(smb_session,service_name,"/",random.choice(get_remote_dir(smb_session,service_name,"/")[2:]).filename,"/tmp/Documents/")
            except:
                print("Error durind download")