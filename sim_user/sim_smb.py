import os
import time
import random
from essential_generators import DocumentGenerator
from smbLib import upload, download, get_remote_dir

def smb_cycle(args):
    """ Execute multiple smb actions.
        args (dict of str): This argument list maps arguments and their value.
            {
                nb_actions (str): This value is the number of actions performed.
                server_ip (str): This value is the ip smb server's ip. 
                share (str): This value is the share file name.
                username (str): This value is the login username required to connect to smb service.
                password (str): This value is the login password required to connect to smb service.
                fullname (str): This value is the user fullname
                domain (str): This value is the server domain name.
            }
    Returns:
        None
    """
    server_ip = args["server_ip"]
    share = args["share"]
    username = args["username"]
    password = args["password"]
    domain = args["domain"]

    actions = ["upload","download"]
    for i in range(int(args["nb_actions"])):
        action = random.choices(actions, weights=[1,1])
        time.sleep(random.randint(10,30))
        if action == ["upload"]:
            gen = DocumentGenerator()
            filename = gen.word()+".txt"
            local_file = open("/sim_user/Documents/"+filename,"w")
            local_file.write(gen.paragraph())
            local_file.close()

            upload(server_ip, share, username, password, domain, filename, "/sim_user/Documents/"+filename, verbose=True)
        elif action == ["download"]:
            if len(get_remote_dir(server_ip, share, username, password, domain, "/",verbose=False)) > 2:
                file = random.choice(get_remote_dir(server_ip, share, username, password, domain, "/", verbose=False))
                download(server_ip, share, username, password, domain, file, "/sim_user/Documents/"+file, verbose=True)
