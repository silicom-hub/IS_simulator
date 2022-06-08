""" This file contains function who configure ldap service """
import os
import time
from colorama import Fore, Style
from .logic_actions_utils import update, add_nameserver, clear_nameserver, save_nameserver_ip, execute_command, upload_file, restart_service, delete_file, create_execute_command_remote_bash, change_fileorfolder_user_owner, change_fileorfolder_group_owner

##############################
########## Server  ###########
##############################
def ldap_create_domaine(instance, arg, verbose=True):
    """ Install and configure openldap with values in variables arg on the remote instance. It's possible to configure ldap or ldaps
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                root_password (str): This value is the administrator's password.
                domain_name (str): This value is the ldap's domain name.
                    Examples:
                    domain_name -> xxxx.xxxx.xxxx
                domain (str): This value is the ldap's domain name.
                    Examples:
                    domain -> dc=xxxx,dc=xxxx,dc=xxxx
                organization (str): This value informs the name of the organization.
                security (dict): This dictionnary contain all security value.
                    folder (str): This value is the path where the differents certificates and keys are stored.
                    CA (str): This value is the path where the Authority certificate is stored.
                    cert (str): This value is the path where the ldap certificate is stored.
                    key (str): This value is the path where the ldap key is stored.

            }

    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    
    """
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

    if arg["tls"] != {}:
        change_fileorfolder_user_owner(instance, {"new_owner":"openldap", "file_path":arg["tls"]["folder"]}, verbose=False)
        change_fileorfolder_group_owner(instance, {"new_group":"openldap", "fileorfolder_path":arg["tls"]["folder"]}, verbose=False)
        create_execute_command_remote_bash(instance, {"script_name":"tmp-slapd_tls.sh", "commands":["sed -i 's#ldap:/// ldapi:///#ldapi:/// ldaps:///#g' /etc/default/slapd \n"
                                                                                                              ], "delete":"false"}, verbose=False)
        if restart_service(instance, {"service":"slapd"}, verbose=False) == 1:
            return 1
        
        tls_CA_ldif = open("simulation/workstations/"+instance.name+"/tls_ca.ldif", "w")
        tls_CA_ldif.write("\n")
        tls_CA_ldif.write("dn: cn=config\n")
        tls_CA_ldif.write("changetype: modify\n")
        tls_CA_ldif.write("add: olcTLSCACertificateFile\n")
        tls_CA_ldif.write("olcTLSCACertificateFile: "+arg["tls"]["CA"]+"\n")
        tls_CA_ldif.write("\n\n")
        tls_CA_ldif.close()
        if upload_file(instance, {"instance_path":"/root/tls_ca.ldif", "host_manager_path":"simulation/workstations/"+instance.name+"/tls_ca.ldif"}, verbose=False) == 1:
            return 1
        execute_command(instance, {"command":["ldapmodify", "-Y", "external", "-H", "ldapi:///", "-f", "/root/tls_ca.ldif"], "expected_exit_code":"0"}, verbose=False)
        
        tls_key_ldif = open("simulation/workstations/"+instance.name+"/tls_key.ldif", "w")
        tls_key_ldif.write("\n")
        tls_key_ldif.write("dn: cn=config\n")
        tls_key_ldif.write("changetype: modify\n")
        tls_key_ldif.write("add: olcTLSCertificateKeyFile\n")
        tls_key_ldif.write("olcTLSCertificateKeyFile: "+arg["tls"]["key"]+"\n")
        tls_key_ldif.write("\n\n")
        tls_key_ldif.close()
        if upload_file(instance, {"instance_path":"/root/tls_key.ldif", "host_manager_path":"simulation/workstations/"+instance.name+"/tls_key.ldif"}, verbose=False) == 1:
            return 1
        instance.execute(["ldapmodify", "-Y", "external", "-H", "ldapi:///", "-f", "/root/tls_key.ldif"])

        tls_cert_ldif = open("simulation/workstations/"+instance.name+"/tls_cert.ldif", "w")
        tls_cert_ldif.write("\n")
        tls_cert_ldif.write("dn: cn=config\n")
        tls_cert_ldif.write("changetype: modify\n")
        tls_cert_ldif.write("add: olcTLSCertificateFile\n")
        tls_cert_ldif.write("olcTLSCertificateFile: "+arg["tls"]["cert"]+"\n")
        tls_cert_ldif.write("\n\n")
        tls_cert_ldif.close()
        if upload_file(instance, {"instance_path":"/root/tls_cert.ldif", "host_manager_path":"simulation/workstations/"+instance.name+"/tls_cert.ldif"}, verbose=False) == 1:
            return 1
        execute_command(instance, {"command":["ldapmodify", "-Y", "external", "-H", "ldapi:///", "-f", "/root/tls_cert.ldif"], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["ldapmodify", "-Y", "external", "-H", "ldapi:///", "-f", "/root/tls_key.ldif"], "expected_exit_code":"0"}, verbose=False)

        tls_client_ldif = open("simulation/workstations/"+instance.name+"/tls_client.ldif", "w")
        tls_client_ldif.write("\n")
        tls_client_ldif.write("dn: cn=config\n")
        tls_client_ldif.write("changetype: modify\n")
        tls_client_ldif.write("add: olcTLSVerifyClient\n")
        tls_client_ldif.write("olcTLSVerifyClient: stats\n")
        tls_client_ldif.write("\n\n")
        tls_client_ldif.close()
        if upload_file(instance, {"instance_path":"/root/tls_client.ldif", "host_manager_path":"simulation/workstations/"+instance.name+"/tls_client.ldif"}, verbose=False) == 1:
            return 1
        execute_command(instance, {"command":["ldapmodify", "-Y", "external", "-H", "ldapi:///", "-f", "/root/tls_client.ldif"], "expected_exit_code":"0"}, verbose=False)

    ##### Configure slapd log
    slapd_ldif = open("simulation/workstations/"+instance.name+"/slapd.ldif", "w")
    slapd_ldif.write("dn: cn=config\n")
    slapd_ldif.write("changeType: modify\n")
    slapd_ldif.write("replace: olcLogLevel\n")
    slapd_ldif.write("olcLogLevel: stats\n")
    slapd_ldif.close()
    if upload_file(instance, {"instance_path":"/etc/ldap/schema/slapd.ldif", "host_manager_path":"simulation/workstations/"+instance.name+"/slapd.ldif"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["ldapmodify", "-Y", "external", "-H", "ldapi:///", "-f", "/etc/ldap/schema/slapd.ldif"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["systemctl", "force-reload", "slapd"], "expected_exit_code":"0"}, verbose=False)
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
    """ Create and configure an user in openldap database with values in variable args on the remote instance
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                objectClass (list): This value is a list  user's objectClass .
                    Examples:
                    objectClass -> ["top", "inetOrgPerson", "posixAccount"]
                mail (str): This value is the users' mail.
                    Examples:
                    domain_name -> user1@mycompany.com
                sn: (str): This is value is the user's surname.
                dn: (str): This value is the user dinstingued name.
                    Examples:
                    dn -> user1.mycompany.com
                domain (str): This value is the ldap's domain name.
                    Examples:
                    domain -> dc=xxxx,dc=xxxx,dc=xxxx
                homeDirectory (str): This value is the path of user's directory.
                loginShell (str): This value is the executable path who will be launch when the user will connect to his workstation.
                password (str): This is the user's password.
                uidNumber (str):
                    Examples:
                    uidNumber -> 1501
                gidNumber (str): 
                    Examples:
                    gidNumber -> 101
            }

    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    
    """
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
                                                                                            "ldapadd -H ldapi:/// -x -w $(cat /root/.env/LDAP_PASSWORD) -D cn=admin,"+arg["domain"]+" -f /etc/ldap/schema/"+arg["username"]+".ldif",
                                                                                            "ldappasswd -H ldapi:/// -s "+ arg["password"] +" -w $(cat /root/.env/LDAP_PASSWORD) -D \"cn=admin,"+arg["domain"]+"\" -x "+ arg["dn"]
                                                                                            ], "delete":"false"}, verbose=False)
        
    my_password = execute_command(instance, {"command":["cat", "/root/.env/LDAP_PASSWORD"], "expected_exit_code":"0"}, verbose=False).stdout[:-1]
    result = execute_command(instance, {"command":["ldapsearch", "-x", "-b", arg["domain"], "-H", "ldapi:///", "-D", "cn=admin,"+arg["domain"], "-w", my_password, "(uid="+arg["username"]+")", "uid"], "expected_exit_code":"0"}, verbose=False)
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
    """ Configure instance to be synchronize xith openldap service
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                ldap_ip (str): This value is the ldap server's ip.
                base (str): This value is the ldap's domain name.
                    Examples:
                    domain_name -> dc=xxxx,dc=xxxx,dc=xxxx
                uri (str): uri's server.
                    Examples:
                    uri -> uri ldap://mycompany.com/
                ldap_admin (str): This value is the ldap administrator's distinguished name.
                    Examples:
                    ldap_admin -> cn=admin,dc=mycompany,dc=com
                tls (str): This value is a boolean wether the ldap protocol is encrypted. 
                    Examples:
                    tls -> true
            }

    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    
    """
    
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
                                                                                                "DEBIAN_FRONTEND=noninteractive apt-get install -y -q nslcd-utils",
                                                                                                "echo 'TLS_REQCERT never' >> /etc/ldap/ldap.conf"
                                                                                                ], "delete":"false"}, verbose=False)
    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)

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
    if arg["tls"] == "true":
        conf_ldap.write("ssl on\n")
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
