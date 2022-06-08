import time
from sshLib import connect_ssh_server, execute_remote_ssh_commands

def upgrade_python_lib(args):
    """ Upgrade python3 librairy with pip3 command.
            hostname (str): This is the IP or domain name of ssh server.
            username (str): This value is the username use to login to ssh server.
            password (str): This value is the password use to login to ssh server.
            verbose (boolean): Print information about function progress.

        Returns:
            None
    """
    execute_remote_ssh_commands(hostname=args["hostname"], username=args["username"], password=args["password"], commands=["pip3 freeze --local | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip3 install -U"], verbose=False)

def restart_apache_service(args):
    """ Restart apache2 service with systemctl
            hostname (str): This is the IP or domain name of ssh server.
            username (str): This value is the username use to login to ssh server.
            password (str): This value is the password use to login to ssh server.
            verbose (boolean): Print information about function progress.

        Returns:
            None
    """
    execute_remote_ssh_commands(hostname=args["hostname"], username=args["username"], password=args["password"], commands=["systemctl restart apache2"], verbose=False)

def upgrade_food_delivery(args):
    """ Upgrade specif python3 librairya and restart food delivery django web service.
            hostname (str): This is the IP or domain name of ssh server.
            username (str): This value is the username use to login to ssh server.
            password (str): This value is the password use to login to ssh server.
            verbose (boolean): Print information about function progress.

        Returns:
            None
    """
    execute_remote_ssh_commands(hostname=args["hostname"], username=args["username"], password=args["password"], commands=["echo "+args["password"]+" | sudo -S pip3 install six --trusted-host pypi.org --upgrade"], verbose=True)
    time.sleep(10)
    execute_remote_ssh_commands(hostname=args["hostname"], username=args["username"], password=args["password"], commands=["echo "+args["password"]+" | sudo -S systemctl restart delivery_food"], verbose=True)

