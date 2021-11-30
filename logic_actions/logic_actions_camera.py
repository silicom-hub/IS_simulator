from colorama import Fore, Style
from .logic_actions_utils import install, execute_command, restart_service, change_permission, change_fileorfolder_user_owner, change_fileorfolder_group_owner, create_execute_command_remote_bash

def install_motion(instance, arg, verbose=True):
    install(instance, {"module":"motion"}, verbose=False)
    for name in instance.execute(["ls","/dev"]).stdout.split("\n"):
        if "video" in name:
            video_name = name
            break
    create_execute_command_remote_bash(instance, {"script_name":"general_configure_motion.sh", "commands":[
        "sed -i -e \'s|stream_port 8081|stream_port "+arg["motion_port"]+"|\' /etc/motion/motion.conf",
        "sed -i -e \'s|stream_localhost on|stream_localhost off|\' /etc/motion/motion.conf",
        "sed -i -e \'s|video0|"+video_name+"|\' /etc/motion/motion.conf"
                                                                                            ], "delete":"false"}, verbose=False)
    if arg["security"] != {}:
        create_execute_command_remote_bash(instance, {"script_name":"security_configure_motion.sh", "commands":[
            "sed -i -e \'s|stream_auth_method 0|stream_auth_method 1|\' /etc/motion/motion.conf",
            "sed -i -e \'s|; stream_authentication username:password|; stream_authentication "+arg["security"]["username"]+":"+arg["security"]["password"]+"|\' /etc/motion/motion.conf"
            "echo 'webcontrol_tls on' >> /etc/motion/motion.conf",
            "echo 'stream_tls on' >> /etc/motion/motion.conf",
            "echo 'webcontrol_cert /certs/"+arg["security"]["private_key_certificate_name"]+"/"+arg["security"]["private_key_certificate_name"]+".cert' >> /etc/motion/motion.conf",
            "echo 'webcontrol_key /certs/"+arg["security"]["private_key_certificate_name"]+"/"+arg["security"]["private_key_certificate_name"]+".key' >> /etc/motion/motion.conf"
                                                                                        ], "delete":"false"}, verbose=False)
    execute_command(instance, {"command":["motion", "-b", "-c", "/etc/motion/motion.conf"], "expected_exit_code":"0"}, verbose=False)

def install_zoneminder(instance, arg, verbose=True):
    install(instance, {"module":"apache2"}, verbose=False)
    install(instance, {"module":"mysql-server"}, verbose=False)
    install(instance, {"module":"zoneminder"}, verbose=False)

    change_permission(instance, {"owner":"7", "group":"4", "other":"0", "file_path":"/etc/zm/zm.conf"}, verbose=False)
    change_fileorfolder_user_owner(instance, {"new_owner":"root", "file_path":"/etc/zm/zm.conf"}, verbose=False)
    change_fileorfolder_group_owner(instance, {"new_group":"www-data", "fileorfolder_path":"/etc/zm/zm.conf"}, verbose=False)
   
    execute_command(instance, {"command":["mysql", "-e", "source /usr/share/zoneminder/db/zm_create.sql;"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["mysql", "-e", "create user zmuser@localhost identified by 'zmpass';"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["mysql", "-e", "grant all privileges on zm.* to zmuser@localhost;"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["mysql", "-e", "flush privileges;"], "expected_exit_code":"0"}, verbose=False)

    execute_command(instance, {"command":["a2enmod", "cgi"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["a2enconf", "zoneminder"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["a2enmod", "rewrite"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["a2enmod", "headers"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["a2enmod", "expires"], "expected_exit_code":"0"}, verbose=False)

    restart_service(instance, {"service":"mysql"}, verbose=False)
    restart_service(instance, {"service":"zoneminder"}, verbose=False)
    restart_service(instance, {"service":"apache2"}, verbose=False)