import os
import time
import tempfile
from datetime import datetime
from smb.SMBConnection import SMBConnection
from colorama import Style, Fore
from essential_generators import DocumentGenerator

def connect_samba_server(username,password,workstation_name,server_name,server_ip):
    smb_session = SMBConnection(username,password,workstation_name,server_name,use_ntlm_v2=True)
    try:
        smb_session.connect(server_ip,445)
        return smb_session
    except:
        print(Fore.RED+"Samba error connection: "+server_name+" | "+username+Style.RESET_ALL)

def get_service_name(smb_session):
    share_names = []
    shares = smb_session.listShares()
    for share in shares:
        share_names.append(share.name)
    return share_names

def get_remote_dir(smb_session,service_name,path):
    dirs = []
    files = smb_session.listPath(service_name,path)
    return files

def upload(smb_session,service_name,path,filename,local_path):
    try:
            if filename == "":
                gen = DocumentGenerator()
                filename = gen.word()+".txt"
                local_file = open(local_path+filename,"w")
                local_file.write(gen.paragraph())
                local_file.close()

            upload_file = tempfile.TemporaryFile()
            upload_file.write(open(local_path+filename,"rb").read())
            upload_file.seek(0)
            smb_session.storeFile(service_name,path+filename,upload_file)
            upload_file.close()
            return True
    except:
        return False

def download(smb_session,service_name,path,remote_filename,local_path):
    try:
        download_file = tempfile.NamedTemporaryFile()
        local_file = open(local_path+remote_filename,"w")
        smb_session.retrieveFile(service_name,remote_filename,download_file)
        download_file.seek(0)
        for line in download_file:
            local_file.write(line.decode(("utf-8")))
        local_file.close()
        return True
    except:
        return False

