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
    for i in range(int(args["nb_actions"])):
        action = random.choices(actions, weights=[1,1])
        time.sleep(random.randint(10,30))
        if action == ["upload"]:
            upload(username, password, workstation_name, server_name, server_ip, service_name, "/", "", "/tmp/Documents/")
        elif action == ["download"]:
            if len(get_remote_dir(username, password, workstation_name, server_name, server_ip, service_name,"/", verbose=False)) > 2:
                download(username, password, workstation_name, server_name, server_ip, service_name, "/", random.choice(get_remote_dir(username, password, workstation_name, server_name, server_ip, service_name,"/", verbose=False)[2:]).filename,"/tmp/Documents/")

