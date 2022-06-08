import re
import time
from colorama import Style, Fore
import smbclient
import os

def connect_samba_server(server_ip, share, username, password, domain, verbose=True):
    """ Connect user to smb service.
            server_ip (str): This value is the ip smb server's ip. 
            share (str): This value is the share file name.
            username (str): This value is the login username required to connect to smb service.
            password (str): This value is the login password required to connect to smb service.
            domain (str): This value is the server domain name.
            verbose (boolean): Print information about function progress.
    Returns:
        smb_object
    """
    smb = smbclient.SambaClient(server=server_ip, share=share, username=username, password=password, domain='WORKGROUP')
    return smb

def get_remote_dir(server_ip, share, username, password, domain, remote_path, verbose=True):
    """ Get file and folder on the remote file server.
            server_ip (str): This value is the ip smb server's ip. 
            share (str): This value is the share file name.
            username (str): This value is the login username required to connect to smb service.
            password (str): This value is the login password required to connect to smb service.
            domain (str): This value is the server domain name.
            remote_path (str): This value is the remote path where the user is located.
            verbose (boolean): Print information about function progress.
    Returns:
        list: Return all files.
    """
    smb = connect_samba_server(server_ip, share, username, password, domain, verbose=True)
    files = smb.listdir(remote_path)
    smb.close()
    return files

def upload(server_ip, share, username, password, domain, remote_path, local_path, verbose=True):
    """ Get file and folder on the remote file server.
            server_ip (str): This value is the ip smb server's ip. 
            share (str): This value is the share file name.
            username (str): This value is the login username required to connect to smb service.
            password (str): This value is the login password required to connect to smb service.
            domain (str): This value is the server domain name.
            remote_path (str): This value is the remote file path to uploaded.
            local_path (str): This value is the remote path where the file will uploaded.
            verbose (boolean): Print information about function progress.
    Returns:
        boolean: 0 if fuction runs correctly. If an error occured return 1.
    """
    try:
        smb = connect_samba_server(server_ip, share, username, password, domain, verbose=True)
        smb.upload(local_path, remote_path)
        smb.close()
        regex = re.compile("((?:[^/]*/)*)(.*)")
        for file in get_remote_dir(server_ip, share, username, password, domain, "/", verbose=True):
            if regex.match(remote_path).group(2) in file:
                print(Fore.GREEN+" ===> [upload]  {"+regex.match(local_path).group(2)+"}  -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
                return True
        print(Fore.RED+" ===> [upload]  {"+regex.match(local_path).group(2)+"}  failed! -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return False
    except Exception as e:
        print(Fore.RED+" ===> [upload]  failed during execution! -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return False

def download(server_ip, share, username, password, domain, remote_path, local_path, verbose=True):
    """ Get file and folder on the remote file server.
            server_ip (str): This value is the ip smb server's ip. 
            share (str): This value is the share file name.
            username (str): This value is the login username required to connect to smb service.
            password (str): This value is the login password required to connect to smb service.
            domain (str): This value is the server domain name.
            remote_path (str): This value is the remote file path to download.
            local_path (str): This value is the remote path where the file will download.
            verbose (boolean): Print information about function progress.
    Returns:
        boolean: 0 if fuction runs correctly. If an error occured return 1.
    """
    try:
        smb = connect_samba_server(server_ip, share, username, password, domain, verbose=True)
        smb.download(remote_path, local_path)
        smb.close()
        regex = re.compile("((?:[^/]*/)*)(.*)")
        files = os.listdir(regex.match(local_path).group(1))
        if regex.match(local_path).group(2) in files:
            if verbose:
                print(Fore.GREEN+" ===> [download]  {"+regex.match(local_path).group(2)+"}  -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
            return True
        print(Fore.RED+" ===> [download]  {"+regex.match(local_path).group(2)+"}  failed! -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return False
    except Exception as e:
        print(Fore.RED+" ===> [download]  failed during execution! -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        print(e)
        return False
