""" This file contains function who configure ldap service """
import os
import time
from colorama import Fore, Style
from .logic_actions_utils import update, add_nameserver, clear_nameserver, save_nameserver_ip, execute_command, upload_file, restart_service, delete_file, create_execute_command_remote_bash

##############################
########## Server  ###########
##############################
def ldap_create_domaine(instance, arg, verbose=True):
    """ Install and configure ldap with values in variables arg on the remote instance """
    ##### Install and launch sldap
    nameserver_ips = save_nameserver_ip(instance)
    clear_nameserver(instance, verbose=False)
    add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)
    create_execute_command_remote_bash(instance, {"script_name":"tmp-slapd_launch.sh", "commands":["echo \"slapd slapd/no_configuration boolean false\" | debconf-set-selections",
                                                                                                               "echo \"slapd slapd/domain string "+ arg["domaine_name"] +"\" | debconf-set-selections\n",
                                                                                                               "echo \"slapd shared/organization string \'"+ arg["organization"] +"\'\" | debconf-set-selections\n",
                                                                                                               "echo \"slapd slapd/password1 password "+ arg["root_password"] +"\" | debconf-set-selections\n",
                                                                                                               "echo \"slapd slapd/password2 password "+ arg["root_password"] +"\" | debconf-set-selections\n",
                                                                                                               "echo \"slapd slapd/backend select HDB\" | debconf-set-selections\n",
                                                                                                               "echo \"slapd slapd/purge_database boolean true\" | debconf-set-selections\n",
                                                                                                               "echo \"slapd slapd/allow_ldap_v2 boolean false\" | debconf-set-selections\n",
                                                                                                               "echo \"slapd slapd/move_old_database boolean true\" | debconf-set-selections\n",
                                                                                                               "DEBIAN_FRONTEND=noninteractive apt-get install -y -q slapd\n",
                                                                                                               "DEBIAN_FRONTEND=noninteractive apt-get install -y -q ldap-utils\n",
                                                                                                               "echo '"+arg["root_password"]+"' > /root/.env/LDAP_PASSWORD \n",
                                                                                                               "sed -i /imklog/s/^/#/ /etc/rsyslog.conf \n"
                                                                                                              ], "delete":"false"}, verbose=False)
    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)

    execute_command(instance, {"command":["echo", "LDAP_PASSWORD="+arg["root_password"], ">>", "/root/.env"], "expected_exit_code":"0"}, verbose=False)
    if restart_service(instance, {"service":"slapd"}, verbose=False) == 1:
        return 1
    result = execute_command(instance, {"command":["slapcat"], "expected_exit_code":"0"}, verbose=False)
    if arg["domain"] in result.stdout:
        if verbose:
            print(Fore.GREEN + "      Domain name is ["+arg["domaine_name"]+"]" + Style.RESET_ALL)
    else:
        print(Fore.RED + "      Ldap configuration has failed..." + Style.RESET_ALL)
        return 1

    ##### Configure slapd log
    slapd_ldif = open("simulation/workstations/"+instance.name+"/slapd.ldif", "w")
    slapd_ldif.write("dn: cn=config\n")
    slapd_ldif.write("changeType: modify\n")
    slapd_ldif.write("replace: olcLogLevel\n")
    slapd_ldif.write("olcLogLevel: any\n")
    slapd_ldif.close()
    if upload_file(instance, {"instance_path":"/etc/ldap/schema/slapd.ldif", "host_manager_path":"simulation/workstations/"+instance.name+"/slapd.ldif"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["ldapmodify", "-Y", "external", "-H", "ldapi:///", "-f", "/etc/ldap/schema/slapd.ldif"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["systemctl", "force-reload", "slapd"], "expected_exit_code":"0"}, verbose=False)

    slapd_rsyslog_conf = open("simulation/workstations/"+instance.name+"/slapd_rsyslog.conf", "w")
    slapd_rsyslog_conf.write("$template slapdtmpl,\"[%$DAY%-%$MONTH%-%$YEAR% %timegenerated:12:19:date-rfc3339%] %app-name% %syslogseverity-text% %msg% \\n\"\n")
    slapd_rsyslog_conf.write("local4.*    /var/log/slapd.log;slapdtmpl\n")
    slapd_rsyslog_conf.write("local4.* @"+arg["ip_log_server"]+":5001\n")
    slapd_rsyslog_conf.close()
    if upload_file(instance, {"instance_path":"/etc/rsyslog.d/slapd.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/slapd_rsyslog.conf"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["chmod", "-R", "777", "/etc/rsyslog.d"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["systemctl", "restart", "rsyslog"], "expected_exit_code":"0"}, verbose=False)
    time.sleep(10)
    result = execute_command(instance, {"command":["ls", "/var/log/"], "expected_exit_code":"0"}, verbose=False)
    if result.exit_code == 0:
        if verbose:
            print(Fore.GREEN+ "      Slapd log is configured [ /var/log/slapd.log ]" +Style.RESET_ALL)
    else:
        print(Fore.RED+ "      Error during slapd log configuration" +Style.RESET_ALL)
        return 1
    print(Fore.GREEN+ "      Openldap service have been installed and configured successfully" +Style.RESET_ALL)
    return 0

def ldap_add_user(instance, arg, verbose=True):
    """ Create and configure an user in openldap database with values in variable args on the remote instance"""
    ##### Create LDIF file
    user_file = open("simulation/workstations/"+instance.name+"/"+arg["username"]+".ldif", "w")
    user_file.write("dn: "+arg["dn"]+"\n")
    if arg["objectClass"] != []:
        for object_class in arg["objectClass"]:
            user_file.write("objectClass: "+ object_class +"\n")
        user_file.write("cn: "+arg["username"]+"\n")
    if arg["sn"] != "":
        user_file.write("sn: "+arg["sn"]+"\n")
    user_file.write("uid: "+arg["username"]+"\n")
    if arg["homeDirectory"] != "":
        user_file.write("homeDirectory: "+arg["homeDirectory"]+"\n")
    if arg["loginShell"] != "":
        user_file.write("loginShell: "+arg["loginShell"]+"\n")
    if arg["mail"] != "":
        user_file.write("mail: "+arg["mail"]+"\n")

    if arg["uidNumber"] != "":
        user_file.write("uidNumber: "+ arg["uidNumber"] +"\n")
    if arg["gidNumber"] != "":
        user_file.write("gidNumber: "+ arg["gidNumber"] +"\n")
    user_file.close()
    if upload_file(instance, {"instance_path":"/etc/ldap/schema/"+arg["username"]+".ldif", "host_manager_path": "simulation/workstations/"+instance.name+"/"+arg["username"]+".ldif"}, verbose=False) == 1:
        return 1

    ##### Add user
    create_execute_command_remote_bash(instance, {"script_name":"ldap_user-"+arg["username"]+".sh", "commands":[
                                                                                            "ldapadd -x -w $(cat /root/.env/LDAP_PASSWORD) -D cn=admin,"+arg["domain"]+" -f /etc/ldap/schema/"+arg["username"]+".ldif",
                                                                                            "ldappasswd -s "+ arg["password"] +" -w $(cat /root/.env/LDAP_PASSWORD) -D \"cn=admin,"+arg["domain"]+"\" -x "+ arg["dn"]
                                                                                            ], "delete":"false"}, verbose=False)
        
    # launch_file = open("simulation/workstations/"+instance.name+"/ldap_user-"+arg["username"]+".sh", "w")
    # launch_file.write("#!/bin/bash \n")
    # launch_file.write("ldapadd -x -w $(cat /root/.env/LDAP_PASSWORD) -D cn=admin,"+arg["domain"]+" -f /etc/ldap/schema/"+arg["username"]+".ldif \n")
    # launch_file.write("ldappasswd -s "+ arg["password"] +" -w $(cat /root/.env/LDAP_PASSWORD) -D \"cn=admin,"+arg["domain"]+"\" -x "+ arg["dn"]+" \n")
    # launch_file.close()
    # if upload_file(instance, {"instance_path":"/root/ldap_user-"+arg["username"]+".sh", "host_manager_path": "simulation/workstations/"+instance.name+"/ldap_user-"+arg["username"]+".sh"}, verbose=False) == 1:
    #     return 1
    # execute_command(instance, {"command":["chmod", "+x", "/root/ldap_user-"+arg["username"]+".sh"], "expected_exit_code":"0"}, verbose=False)
    # execute_command(instance, {"command":["./ldap_user-"+arg["username"]+".sh"], "expected_exit_code":"0"}, verbose=False)
    
    my_password = execute_command(instance, {"command":["cat", "/root/.env/LDAP_PASSWORD"], "expected_exit_code":"0"}, verbose=False).stdout[:-1]
    result = execute_command(instance, {"command":["ldapsearch", "-x", "-b", arg["domain"], "-H", "ldap://127.0.0.1", "-D", "cn=admin,"+arg["domain"], "-w", my_password, "(uid="+arg["username"]+")", "uid"], "expected_exit_code":"0"}, verbose=False)
    if arg["username"] in result.stdout:
        if verbose:
            print(Fore.GREEN + "      User "+arg["username"]+" has been added to LDAP server with password: "+arg["password"] +Style.RESET_ALL)
            return 0

    print(Fore.RED + "      User "+arg["username"]+" failed to add to LDAP server" +Style.RESET_ALL)
    return 1
#############################
########### Client ##########
#############################
def ldap_client_config(instance, arg, verbose=True):
    """ Configure instance to be synchronize xith openldap service """
    ### Init
    os.makedirs("simulation/workstations/"+instance.name+"/ldap/")
    ### Install require packages
    update(instance, verbose=False)
    nameserver_ips = save_nameserver_ip(instance)
    clear_nameserver(instance, verbose=False)
    add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)
    create_execute_command_remote_bash(instance, {"script_name":"install_module.sh", "commands":[
                                                                                                "DEBIAN_FRONTEND=noninteractive apt-get install -y -q libpam-ldap",
                                                                                                "DEBIAN_FRONTEND=noninteractive apt-get install -y -q nscd",
                                                                                                "DEBIAN_FRONTEND=noninteractive apt-get install -y -q nslcd",
                                                                                                "DEBIAN_FRONTEND=noninteractive apt-get install -y -q nslcd-utils"
                                                                                                ], "delete":"false"}, verbose=False)
    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)
    # install_module = open("simulation/workstations/"+instance.name+"/ldap/install_module.sh", "w")
    # install_module.write("apt-get -y update \n")
    # install_module.write("DEBIAN_FRONTEND=noninteractive apt-get install -y -q libpam-ldap \n")
    # install_module.write("DEBIAN_FRONTEND=noninteractive apt-get install -y -q nscd \n")
    # install_module.write("DEBIAN_FRONTEND=noninteractive apt-get install -y -q nslcd \n")
    # install_module.write("DEBIAN_FRONTEND=noninteractive apt-get install -y -q nslcd-utils \n")
    # install_module.close()
    # if upload_file(instance, {"instance_path":"/root/install_module.sh", "host_manager_path": "simulation/workstations/"+instance.name+"/ldap/install_module.sh"}, verbose=False) == 1:
    #     return 1
    # execute_command(instance, {"command":["chmod", "+x", "/root/install_module.sh"], "expected_exit_code":"0"}, verbose=False)
    # result = execute_command(instance, {"command":["./install_module.sh"], "expected_exit_code":"0"}, verbose=False)
    # if result.exit_code == 0:
    #     if verbose:
    #         print(Fore.GREEN + "      All module have been installed!" + Style.RESET_ALL)
    # else:
    #     print(Fore.RED + "      Error during modules installation" + Style.RESET_ALL)
    #     return 1
    # delete_file(instance, {"instance_path":"/root/install_module.sh"}, verbose=False)

    ### Configure nsswitch.conf
    conf_nsswitch = open("simulation/workstations/"+instance.name+"/ldap/nsswitch.conf", "w")
    conf_nsswitch.write("passwd:         files ldap\n")
    conf_nsswitch.write("group:          files ldap\n")
    conf_nsswitch.write("shadow:         files ldap\n")
    conf_nsswitch.write("gshadow:        files\n")
    conf_nsswitch.write("hosts:          files dns\n")
    conf_nsswitch.write("networks:       files\n")
    conf_nsswitch.write("protocols:      db files\n")
    conf_nsswitch.write("services:       db files\n")
    conf_nsswitch.write("ethers:         db files\n")
    conf_nsswitch.write("rpc:            db files\n")
    conf_nsswitch.write("netgroup:       nis\n")
    conf_nsswitch.close()
    if upload_file(instance, {"instance_path":"/etc/nsswitch.conf", "host_manager_path": "simulation/workstations/"+instance.name+"/ldap/nsswitch.conf"}, verbose=False) == 1:
        return 1

    ### Configure ldap.conf
    conf_ldap = open("simulation/workstations/"+instance.name+"/ldap/ldap.conf", "w")
    conf_ldap.write("host "+arg["ldap_ip"]+"\n")
    conf_ldap.write("base "+ arg["base"] +"\n")
    conf_ldap.write("ldap_version 3\n")
    conf_ldap.write("rootbinddn "+ arg["ldap_admin"]+"\n")
    conf_ldap.write("pam_password md5\n")
    conf_ldap.close()
    if upload_file(instance, {"instance_path":"/etc/ldap.conf", "host_manager_path": "simulation/workstations/"+instance.name+"/ldap/ldap.conf"}, verbose=False) == 1:
        return 1

    ### Configure PAM
    ### Configure common-account
    conf_common_account = open("simulation/workstations/"+instance.name+"/ldap/common-account", "w")
    conf_common_account.write("account	sufficient	pam_ldap.so\n")
    conf_common_account.write("account	required	pam_unix.so\n")
    conf_common_account.close()
    if upload_file(instance, {"instance_path":"/etc/pam.d/common-account", "host_manager_path": "simulation/workstations/"+instance.name+"/ldap/common-account"}, verbose=False) == 1:
        return 1

    ### Configure common-auth
    conf_common_auth = open("simulation/workstations/"+instance.name+"/ldap/common-auth", "w")
    conf_common_auth.write("account	sufficient	pam_ldap.so\n")
    conf_common_auth.write("account	required	pam_unix.so\n")
    conf_common_auth.close()
    if upload_file(instance, {"instance_path":"/root/install_module.sh", "host_manager_path": "simulation/workstations/"+instance.name+"/ldap/common-auth"}, verbose=False) == 1:
        return 1

    ### Configure common-password
    conf_common_auth = open("simulation/workstations/"+instance.name+"/ldap/common-password", "w")
    conf_common_auth.write("account	sufficient	pam_ldap.so\n")
    conf_common_auth.write("account	required	pam_unix.so\n")
    conf_common_auth.close()
    if upload_file(instance, {"instance_path":"/etc/pam.d/common-password", "host_manager_path": "simulation/workstations/"+instance.name+"/ldap/common-password"}, verbose=False) == 1:
        return 1

    ### Configure common-session
    conf_common_session = open("simulation/workstations/"+instance.name+"/ldap/common-session", "w")
    conf_common_session.write("session required        pam_unix.so\n")
    conf_common_session.write("session required        pam_mkhomedir.so skel=/etc/skel/\n")
    conf_common_session.write("session optional        pam_ldap.so\n")
    conf_common_session.close()
    if upload_file(instance, {"instance_path":"/etc/pam.d/common-session", "host_manager_path": "simulation/workstations/"+instance.name+"/ldap/common-session"}, verbose=False) == 1:
        return 1

    if restart_service(instance, {"service":"nscd"}, verbose=False) == 1:
        return 1

    print(Fore.GREEN + "      Openldap service have been installed and configured successfully!" + Style.RESET_ALL)
    return 0
