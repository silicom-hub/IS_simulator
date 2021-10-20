import os
import json
import random
import threading

def load_json_file(path_conf):
    with open(path_conf, "r") as f:
        conf_physic = json.load(f)
    return conf_physic

class Thread_user(threading.Thread):
    def __init__(self,user):
        threading.Thread.__init__(self)
        self.user = user

    def run(self):
        os.system("su "+self.user["name"]+" -c 'python3 /tmp/sim_user/user_simulation.py'")

users = load_json_file("/tmp/sim_user/users.json")
for user in users["users"]:
    thread = Thread_user(user)
    thread.start()