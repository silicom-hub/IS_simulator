import time
from paramiko import SSHClient, AutoAddPolicy
from colorama import Style, Fore

def connect_ssh_server(hostname, username, password, verbose=True):
    """ Connection to a remote ssh server.
            hostname (str): This is the IP or domain name of ssh server.
            username (str): This value is the username use to login to ssh server.
            password (str): This value is the password use to login to ssh server.
            verbose (boolean): Print information about function progress.

        Returns:
            client_ssh: 0 Return ssh socket.
    """
    try:
        client = SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(AutoAddPolicy())
        print(client.connect(hostname=hostname,username=username,password=password))
        if verbose == True:
            print(Fore.GREEN+" ===> SSH connection: "+hostname+" was successfully   -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        return client
    except Exception as e:
        print(Fore.RED+" ===> SSH connection failed   -- "+time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)
        print(e)
        return 1

def execute_remote_ssh_commands(hostname, username, password, commands, verbose=True):
    """ Execute a remote command line.
            hostname (str): This is the IP or domain name of ssh server.
            username (str): This value is the username use to login to ssh server.
            password (str): This value is the password use to login to ssh server.
            verbose (boolean): Print information about function progress.

        Returns:
            client_ssh: Return ssh socket.
    """
    client = connect_ssh_server(hostname, username, password, verbose=False)
    if client == 1:
        return 1
    for command in commands:
        stdin, stdout, stderr = client.exec_command(command)
        print(stdout.readlines())
    client.close()

