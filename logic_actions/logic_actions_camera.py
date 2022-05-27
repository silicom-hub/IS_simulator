from colorama import Fore, Style
from .logic_actions_utils import install, execute_command, restart_service, change_permission, change_fileorfolder_user_owner, change_fileorfolder_group_owner, create_execute_command_remote_bash

def install_motion(instance, arg, verbose=True):
    """ Install motion application on the workstation. Configure motion file to send video stream on specific port with optional security access.
    Webcontrol is also available with login and password and secure with https if private key and certificate were given.
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                motion_port (str): This value indicate the port of the outgoing video stream.
                security (dict): This dictionnary contain all security value.
                    username (str): This value is the login username.
                    password (str): This value is the password of the login username.
                    private_key_certificate_name (str): This value indicate the folder where the application can find private key and certificate to secure motion application.
            }

    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    
    """
    if install(instance, {"module":"motion"}, verbose=False) == 1:
        return 1
    
    for name in instance.execute(["ls","/dev"]).stdout.split("\n"):
        if "video" in name:
            video_name = name
            break
    
    if create_execute_command_remote_bash(instance, {"script_name":"general_configure_motion.sh", "commands":[
        "sed -i -e \'s|stream_port 8081|stream_port "+arg["motion_port"]+"|\' /etc/motion/motion.conf",
        "sed -i -e \'s|stream_localhost on|stream_localhost off|\' /etc/motion/motion.conf",
        "sed -i -e \'s|video0|"+video_name+"|\' /etc/motion/motion.conf"
        ], "delete":"false"}, verbose=False) == 1:
        return 1

    if arg["security"] != {}:
        if create_execute_command_remote_bash(instance, {"script_name":"security_configure_motion.sh", "commands":[
            "sed -i -e \'s|stream_auth_method 0|stream_auth_method 1|\' /etc/motion/motion.conf",
            "sed -i -e \'s|; stream_authentication username:password|; stream_authentication "+arg["security"]["username"]+":"+arg["security"]["password"]+"|\' /etc/motion/motion.conf"
            "echo 'webcontrol_tls on' >> /etc/motion/motion.conf",
            "echo 'stream_tls on' >> /etc/motion/motion.conf",
            "echo 'webcontrol_cert /certs/"+arg["security"]["private_key_certificate_name"]+"/"+arg["security"]["private_key_certificate_name"]+".cert' >> /etc/motion/motion.conf",
            "echo 'webcontrol_key /certs/"+arg["security"]["private_key_certificate_name"]+"/"+arg["security"]["private_key_certificate_name"]+".key' >> /etc/motion/motion.conf"
            ], "delete":"false"}, verbose=False) == 1:
            return 1

    if execute_command(instance, {"command":["motion", "-b", "-c", "/etc/motion/motion.conf"], "expected_exit_code":"0"}, verbose=False) == 1:
        return 1
    return 0

def install_zoneminder(instance, arg, verbose=True):
    """ Install zoneminder application on the workstation.
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                This dictionnary is empty.
            }

        Returns:
                int: Return 1 if the function works successfully, otherwise 0.
    """
    output = 0

    output = install(instance, {"module":"apache2"}, verbose=False)
    output = install(instance, {"module":"mysql-server"}, verbose=False)
    output = install(instance, {"module":"zoneminder"}, verbose=False)

    output = change_permission(instance, {"owner":"7", "group":"4", "other":"0", "file_path":"/etc/zm/zm.conf"}, verbose=False)
    output = change_fileorfolder_user_owner(instance, {"new_owner":"root", "file_path":"/etc/zm/zm.conf"}, verbose=False)
    output = change_fileorfolder_group_owner(instance, {"new_group":"www-data", "fileorfolder_path":"/etc/zm/zm.conf"}, verbose=False)

    output = execute_command(instance, {"command":["mysql", "-e", "source /usr/share/zoneminder/db/zm_create.sql;"], "expected_exit_code":"0"}, verbose=False)
    output = execute_command(instance, {"command":["mysql", "-e", "create user zmuser@localhost identified by 'zmpass';"], "expected_exit_code":"0"}, verbose=False)
    output = execute_command(instance, {"command":["mysql", "-e", "grant all privileges on zm.* to zmuser@localhost;"], "expected_exit_code":"0"}, verbose=False)
    output = execute_command(instance, {"command":["mysql", "-e", "flush privileges;"], "expected_exit_code":"0"}, verbose=False)

    output = execute_command(instance, {"command":["a2enmod", "cgi"], "expected_exit_code":"0"}, verbose=False)
    output = execute_command(instance, {"command":["a2enconf", "zoneminder"], "expected_exit_code":"0"}, verbose=False)
    output = execute_command(instance, {"command":["a2enmod", "rewrite"], "expected_exit_code":"0"}, verbose=False)
    output = execute_command(instance, {"command":["a2enmod", "headers"], "expected_exit_code":"0"}, verbose=False)
    output = execute_command(instance, {"command":["a2enmod", "expires"], "expected_exit_code":"0"}, verbose=False)

    output = restart_service(instance, {"service":"mysql"}, verbose=False)
    output = restart_service(instance, {"service":"zoneminder"}, verbose=False)
    output = restart_service(instance, {"service":"apache2"}, verbose=False)
    return output