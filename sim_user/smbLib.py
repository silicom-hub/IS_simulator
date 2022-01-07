import os
import time
import tempfile
from datetime import datetime
from smb.SMBConnection import SMBConnection
from colorama import Style, Fore
from essential_generators import DocumentGenerator

def connect_samba_server(username,password,workstation_name,server_name,server_ip, verbose=True):
    smb_session = SMBConnection(username,password,workstation_name,server_name,use_ntlm_v2=True)
    try:
        smb_session.connect(server_ip,445)
        if verbose:
            print(Fore.GREEN+" ===> Samba connection: "+server_name+" was successfully   -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return smb_session
    except:
        print(Fore.RED+" ===> Samba connection: "+server_name+" failed   -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return False

def get_service_name(smb_session):
    share_names = []
    shares = smb_session.listShares()
    for share in shares:
        share_names.append(share.name)
    return share_names

def diconnnect(smb_session, verbose=True):
    try:
        smb_session.close()
        if verbose:
            print(Fore.GREEN+" ===> Samba logout was successfully   -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return True
    except:
        print(Fore.RED+" ===> Samba logout failed   -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return False



def get_remote_dir(username, password, workstation_name, server_name, server_ip, service_name,path, verbose=True):
    smb_session = connect_samba_server(username, password, workstation_name, server_name, server_ip, verbose=False)
    try:
        dirs = []
        files = smb_session.listPath(service_name,path)
        if verbose:
            print(Fore.GREEN+" ===> [get_remote_dir]  {"+len(files)+"}   -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return files
    except Exception as e:
        print(e)
        print(Fore.RED+" ===> [get_remote_dir]  failed!   -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return False

def upload(username, password, workstation_name, server_name, server_ip, service_name,path,filename,local_path, verbose=True):
    smb_session = connect_samba_server(username, password, workstation_name, server_name, server_ip, verbose=False)
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
        if verbose:
            upload_file.seek(0, os.SEEK_END)
            print(Fore.GREEN+" ===> [upload]  {"+filename+"}  "+str(upload_file.tell())+" bytes -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        upload_file.close()
        diconnnect(smb_session, verbose=False)
        return True
    except Exception as e:
        print(e)
        print(Fore.RED+" ===> [upload]  {"+filename+"}  failed! -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        diconnnect(smb_session, verbose=False)
        return False

def download(username, password, workstation_name, server_name, server_ip, service_name,path,remote_filename,local_path, verbose=True):
    smb_session = connect_samba_server(username,password,workstation_name,server_name,server_ip, verbose=False)
    try:
        download_file = tempfile.NamedTemporaryFile()
        local_file = open(local_path+remote_filename,"w")
        smb_session.retrieveFile(service_name,remote_filename,download_file)
        download_file.seek(0)
        for line in download_file:
            local_file.write(line.decode(("utf-8")))
        if verbose:
            download_file.seek(0, os.SEEK_END)
            print(Fore.GREEN+" ===> [download]  {"+local_path+remote_filename+"}  "+str(local_file.tell())+" bytes -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        local_file.close()
        diconnnect(smb_session, verbose=False)
        return True
    except Exception as e:
        print(e)
        print(Fore.RED+" ===> [download]  {"+local_path+remote_filename+"}  failed! -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        diconnnect(smb_session, verbose=False)
        return False
