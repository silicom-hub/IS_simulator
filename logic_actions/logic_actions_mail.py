""" This file contain functions about mail configuration """
from colorama import Fore, Style
from .logic_actions_utils import save_nameserver_ip, add_nameserver, clear_nameserver, create_execute_command_remote_bash, execute_command, upload_file, update, install, delete_file, restart_service, add_user2group, change_fileorfolder_group_owner

def mail_installation(instance, arg, verbose=True):
    """ Install and configure imapd-cyrus and postfix and synchronize imapd with openldap """
    if update(instance, verbose=False):
        return 1
#########################################
#### Install and configure saslauthd ####
#########################################
    if install(instance, {"module":"sasl2-bin"}, verbose=False) == 1:
        return 1
    if install(instance, {"module":"cyrus-admin"}, verbose=False) == 1:
        return 1

    saslauthd_conf = open("simulation/workstations/"+instance.name+"/saslauthd.conf", "w")
    saslauthd_conf.write("# SERVEUR LDAP \n")
    saslauthd_conf.write("LDAP_SERVERS: ldap://"+arg["ldap_ip"]+"\n")
    saslauthd_conf.write("# DOMAINE \n")
    saslauthd_conf.write("LDAP_DEFAULT_DOMAIN: "+arg["ldap_domain"]+"\n")
    saslauthd_conf.write("LDAP_TIMEOUT: 10\n")
    saslauthd_conf.write("LDAP_TIME_LIMIT: 10\n")
    saslauthd_conf.write("LDAP_CACHE_TTL: 30\n")
    saslauthd_conf.write("LDAP_CACHE_MEM: 32768\n")
    saslauthd_conf.write("# VERSION LDAP\n")
    saslauthd_conf.write("LDAP_VERSION: 3\n")
    saslauthd_conf.write("# SASL Pour l'accès au serveur\n")
    saslauthd_conf.write("LDAP_USE_SASL: no\n")
    saslauthd_conf.write("# Méthode d'authentification (bind / custom / fastbind)\n")
    saslauthd_conf.write("LDAP_AUTH_METHOD: bind\n")
    saslauthd_conf.write("# Utilisateur utilisé pour la connexion - Si vide = Anonyme\n")
    saslauthd_conf.write("LDAP_BIND_DN: "+arg["ldap_manager"]+"\n")
    saslauthd_conf.write("# Et le mot de passe\n")
    saslauthd_conf.write("LDAP_BIND_PW: "+arg["ldap_manager_password"]+"\n")
    saslauthd_conf.write("# Base de départ de la recherche\n")
    saslauthd_conf.write("LDAP_SEARCH_BASE: "+arg["ldap_dn"]+"\n")
    saslauthd_conf.write("# Et profondeur (sub / one / base )\n")
    saslauthd_conf.write("LDAP_SCOPE: sub\n")
    saslauthd_conf.write("# Filtre de recherche : uid dans notre cas\n")
    saslauthd_conf.write("LDAP_FILTER: uid=%u\n")
    saslauthd_conf.write("# Et nom du champ contenant le mot de passe\n")
    saslauthd_conf.write("LDAP_PASSWORD_ATTR: userPassword\n")
    saslauthd_conf.close()
    if upload_file(instance, {"instance_path":"/etc/saslauthd.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/saslauthd.conf"}, verbose=False) == 1:
        return 1

    saslauthd = open("simulation/workstations/"+instance.name+"/saslauthd", "w")
    saslauthd.write("START=yes\n")
    saslauthd.write("DESC=\"SASL Authentication Daemon\"\n")
    saslauthd.write("NAME=\"saslauthd\"\n")
    saslauthd.write("MECHANISMS=\"ldap\"\n")
    saslauthd.write("PARAMS=\"-O /etc/saslauthd.conf\"\n")
    saslauthd.write("MECH_OPTIONS=\"\"\n")
    saslauthd.write("THREADS=5\n")
    saslauthd.write("OPTIONS=\'-c -m /var/run/saslauthd\'\n")
    saslauthd.close()
    if upload_file(instance, {"instance_path":"/etc/default/saslauthd", "host_manager_path":"simulation/workstations/"+instance.name+"/saslauthd"}, verbose=False) == 1:
        return 1

    saslauthd_launch = open("simulation/workstations/"+instance.name+"/saslauthd_launcher.sh", "w")
    saslauthd_launch.write("#!/bin/bash \n")
    saslauthd_launch.write("systemctl restart saslauthd \n")
    saslauthd_launch.write("sed -i -e  s#OPTIONS='-c -m /var/run/saslauthd'#OPTIONS='-c -m /var/spool/postfix/var/run/saslauthd'# /etc/default/saslauthd \n")
    saslauthd_launch.write("chmod 1777 /etc/resolv.conf \n")
    saslauthd_launch.write("chmod 1777 -R /var/spool/postfix/ \n")
    saslauthd_launch.write("systemctl restart saslauthd \n")
    saslauthd_launch.close()
    if upload_file(instance, {"instance_path":"/root/saslauthd_launcher.sh", "host_manager_path":"simulation/workstations/"+instance.name+"/saslauthd_launcher.sh"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["chmod", "+x", "/root/saslauthd_launcher.sh"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["./saslauthd_launcher.sh"], "expected_exit_code":"0"}, verbose=False)
    if delete_file(instance, {"instance_path":"/root/saslauthd_launcher.sh"}, verbose=False) == 1:
        return 1
    result = execute_command(instance, {"command":["testsaslauthd", "-u", "cyrus", "-p", "cyrus123"], "expected_exit_code":"0"}, verbose=False)
    if result.exit_code == 0:
        if verbose:
            print(Fore.GREEN+"      Sasl configuration is working! "+Style.RESET_ALL)
    else:
        print(Fore.RED+"      Sasl failed during configuration... "+Style.RESET_ALL)
        return 1

###########################################
#### Install and configure cyrus-imapd ####
###########################################
    nameserver_ips = save_nameserver_ip(instance)
    clear_nameserver(instance, verbose=False)
    add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)
    create_execute_command_remote_bash(instance, {"script_name":"launch_cyrus_imapd.sh", "commands":[
                                                                                                     "debconf-set-selections <<< \"postfix postfix/mailname string "+instance.name+"."+arg["domain_name"]+"\"",
                                                                                                     "debconf-set-selections <<< \"postfix postfix/main_mailer_type string 'Internet Site'\"",
                                                                                                     "DEBIAN_FRONTEND=noninteractive apt-get install -y cyrus-imapd",
                                                                                                     "touch /var/lib/cyrus/tls_sessions.db",
                                                                                                     "chown cyrus:mail /var/lib/cyrus/tls_sessions.db",
                                                                                                     "sed -i -e \'s|#admins: cyrus|admins: cyrus|\' /etc/imapd.conf",
                                                                                                     "sed -i -e \'s|sasl_pwcheck_method: auxprop|sasl_pwcheck_method: saslauthd|\' /etc/imapd.conf",
                                                                                                     "sed -i -e \'s|#sasl_mech_list: PLAIN|sasl_mech_list: PLAIN|\' /etc/imapd.conf",
                                                                                                     "sed -i -e \'s|pop3|#pop3|\' /etc/cyrus.conf",
                                                                                                     "sed -i -e \'s|nntp|#nntp|\' /etc/cyrus.conf",
                                                                                                     "sed -i -e \'s|http|#http|\' /etc/cyrus.conf",
                                                                                                     "systemctl restart cyrus-imapd",
                                                                                                     "sleep 2",
                                                                                                     "cyradm -u cyrus -w cyrus123 localhost << sample",
                                                                                                     "".join(["cm user."+user+" \n" for user in arg["users_mailbox"]]),
                                                                                                     "sample"
                                                                                                    ], "delete":"false"}, verbose=False)
    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)

#######################################
#### Install and configure postfix ####
#######################################
    if install(instance, {"module":"postfix-ldap"}, verbose=False) == 1:
        return 1
    if install(instance, {"module":"bsd-mailx"}, verbose=False) == 1:
        return 1

    create_execute_command_remote_bash(instance, {"script_name":"update_main_cf.sh", "commands":[
                                                                                                    "echo 'cyrus   unix    -       n       n       -       -       pipe\n  flags=R user=cyrus argv=/usr/sbin/cyrdeliver -e -m\n  ${extension} ${user}' >> /etc/postfix/master.cf"
                                                                                                    ], "delete":"false"}, verbose=False)

    main_cf = open("simulation/workstations/"+instance.name+"/main.cf", "w")
    main_cf.write("myorigin = /etc/mailname \n")
    main_cf.write("smtpd_banner = $myhostname ESMTP $mail_name\n")
    main_cf.write("biff = no \n")
    main_cf.write("append_dot_mydomain = no \n")
    main_cf.write("delay_warning_time = 4h \n")
    main_cf.write("myhostname = "+instance.name+"."+arg["domain_name"]+"\n")
    main_cf.write("mailbox_maps = ldap:/etc/postfix/ldap-accounts.cf \n")
    main_cf.write("alias_maps = ldap:/etc/postfix/ldap-aliases.cf \n")
    main_cf.write("mydestination = "+arg["domain_name"]+", "+instance.name+"."+arg["domain_name"]+", localhost"+arg["domain_name"]+", localhost \n")
    main_cf.write("relayhost = \n")
    main_cf.write("mynetworks = 127.0.0.0/8 \n")
    main_cf.write("local_transport = cyrus \n")
    main_cf.write("recipient_delimiter = + \n")
    main_cf.write("smtpd_sasl_auth_enable = yes \n")
    main_cf.write("smtpd_relay_restrictions = reject_unauth_destination \n")
    main_cf.write("smtpd_sasl_security_options = noanonymous \n")
    main_cf.write("smtpd_sasl_local_domain = \n")
    main_cf.write("inet_protocols = ipv4 \n")
    main_cf.write("inet_interfaces = all \n")
    main_cf.close()
    if upload_file(instance, {"instance_path":"/etc/postfix/main.cf", "host_manager_path":"simulation/workstations/"+instance.name+"/main.cf"}, verbose=False) == 1:
        return 1

    ldap_accounts_cf = open("simulation/workstations/"+instance.name+"/ldap_accounts.cf", "w")
    ldap_accounts_cf.write("server_host = "+arg["ldap_ip"]+" \n")
    ldap_accounts_cf.write("server_port = "+arg["ldap_port"]+ "\n")
    ldap_accounts_cf.write("search_base = "+arg["ldap_dn"]+" \n")
    ldap_accounts_cf.write("query_filter = (&(objectClass=InetOrgPerson)(mail=%s)) \n")
    ldap_accounts_cf.write("result_attribute = uid \n")
    ldap_accounts_cf.write("bind = yes \n")
    ldap_accounts_cf.write("bind_dn = "+arg["ldap_manager"]+ " \n")
    ldap_accounts_cf.write("bind_pw = "+arg["ldap_manager_password"]+" \n")
    ldap_accounts_cf.write("version = 3 \n")
    ldap_accounts_cf.close()
    if upload_file(instance, {"instance_path":"/etc/postfix/ldap-accounts.cf", "host_manager_path":"simulation/workstations/"+instance.name+"/ldap_accounts.cf"}, verbose=False) == 1:
        return 1

    ldap_accounts_cf = open("simulation/workstations/"+instance.name+"/ldap-aliases.cf", "w")
    ldap_accounts_cf.write("server_host = "+arg["ldap_ip"]+" \n")
    ldap_accounts_cf.write("server_port = "+arg["ldap_port"]+ "\n")
    ldap_accounts_cf.write("search_base = "+arg["ldap_dn"]+" \n")
    ldap_accounts_cf.write("query_filter = (&(objectClass=InetOrgPerson)(mail=%s)) \n")
    ldap_accounts_cf.write("result_attribute = mail \n")
    ldap_accounts_cf.write("bind = yes \n")
    ldap_accounts_cf.write("bind_dn = "+arg["ldap_manager"]+ " \n")
    ldap_accounts_cf.write("bind_pw = "+arg["ldap_manager_password"]+" \n")
    ldap_accounts_cf.write("version = 3")
    ldap_accounts_cf.close()
    if upload_file(instance, {"instance_path":"/etc/postfix/ldap-aliases.cf", "host_manager_path":"simulation/workstations/"+instance.name+"/ldap-aliases.cf"}, verbose=False) == 1:
        return 1

    smtpd_conf = open("simulation/workstations/"+instance.name+"/smtpd.conf", "w")
    smtpd_conf.write("pwcheck_method: saslauthd \n")
    smtpd_conf.write("mech_list: plain \n")
    smtpd_conf.close()
    if upload_file(instance, {"instance_path":"/etc/postfix/sasl/smtpd.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/smtpd.conf"}, verbose=False) == 1:
        return 1
    
    print(Fore.GREEN + "      Mail service have been intalled and configured successfully!" + Style.RESET_ALL)
    return 0

# In progress ...
def install_postfix(instance, arg, verbose=True):
    """ In progress... """
#########################################
#### Install and configure saslauthd ####
#########################################
    result = instance.execute(["apt-get", "install", "-y", "sasl2-bin"])
    if result.exit_code == 0:
        if verbose:
            print(Fore.GREEN+"      SASL installation was done!"+Style.RESET_ALL)
    else:
        print(Fore.RED+"      SASL installation failed..."+Style.RESET_ALL)

    result = instance.execute(["apt-get", "install", "-y", "cyrus-admin"])
    if result.exit_code == 0:
        if verbose:
            print(Fore.GREEN+"      cyrus-admin installation was done!"+Style.RESET_ALL)
    else:
        print(Fore.RED+"      cyrus-admin installation failed..."+Style.RESET_ALL)

    saslauthd_conf = open("simulation/workstations/"+instance.name+"/saslauthd.conf", "w")
    saslauthd_conf.write("# SERVEUR LDAP \n")
    saslauthd_conf.write("LDAP_SERVERS: ldap://"+arg["ldap_ip"]+"\n")
    saslauthd_conf.write("# DOMAINE \n")
    saslauthd_conf.write("LDAP_DEFAULT_DOMAIN: "+arg["ldap_domain"]+"\n")
    saslauthd_conf.write("LDAP_TIMEOUT: 10\n")
    saslauthd_conf.write("LDAP_TIME_LIMIT: 10\n")
    saslauthd_conf.write("LDAP_CACHE_TTL: 30\n")
    saslauthd_conf.write("LDAP_CACHE_MEM: 32768\n")
    saslauthd_conf.write("# VERSION LDAP\n")
    saslauthd_conf.write("LDAP_VERSION: 3\n")
    saslauthd_conf.write("# SASL Pour l'accès au serveur\n")
    saslauthd_conf.write("LDAP_USE_SASL: no\n")
    saslauthd_conf.write("# Méthode d'authentification (bind / custom / fastbind)\n")
    saslauthd_conf.write("LDAP_AUTH_METHOD: bind\n")
    saslauthd_conf.write("# Utilisateur utilisé pour la connexion - Si vide = Anonyme\n")
    saslauthd_conf.write("LDAP_BIND_DN: "+arg["ldap_manager"]+"\n")
    saslauthd_conf.write("# Et le mot de passe\n")
    saslauthd_conf.write("LDAP_BIND_PW: "+arg["ldap_manager_password"]+"\n")
    saslauthd_conf.write("# Base de départ de la recherche\n")
    saslauthd_conf.write("LDAP_SEARCH_BASE: "+arg["ldap_dn"]+"\n")
    saslauthd_conf.write("# Et profondeur (sub / one / base )\n")
    saslauthd_conf.write("LDAP_SCOPE: sub\n")
    saslauthd_conf.write("# Filtre de recherche : uid dans notre cas\n")
    saslauthd_conf.write("LDAP_FILTER: uid=%u\n")
    saslauthd_conf.write("# Et nom du champ contenant le mot de passe\n")
    saslauthd_conf.write("LDAP_PASSWORD_ATTR: userPassword\n")
    saslauthd_conf.close()
    instance.files.put("/etc/saslauthd.conf", open("simulation/workstations/"+instance.name+"/saslauthd.conf").read(), verbose=False)

    saslauthd = open("simulation/workstations/"+instance.name+"/saslauthd", "w")
    saslauthd.write("START=yes\n")
    saslauthd.write("DESC=\"SASL Authentication Daemon\"\n")
    saslauthd.write("NAME=\"saslauthd\"\n")
    saslauthd.write("MECHANISMS=\"ldap\"\n")
    saslauthd.write("PARAMS=\"-O /etc/saslauthd.conf\"\n")
    saslauthd.write("MECH_OPTIONS=\"\"\n")
    saslauthd.write("THREADS=5\n")
    saslauthd.write("OPTIONS=\'-c -m /var/run/saslauthd\'\n")
    saslauthd.close()
    instance.files.put("/etc/default/saslauthd", open("simulation/workstations/"+instance.name+"/saslauthd").read(), verbose=False)

    saslauthd_launch = open("simulation/workstations/"+instance.name+"/saslauthd_launcher.sh", "w")
    saslauthd_launch.write("#!/bin/bash \n")
    saslauthd_launch.write("systemctl restart saslauthd \n")
    saslauthd_launch.write("sed -i -e  s#OPTIONS='-c -m /var/run/saslauthd'#OPTIONS='-c -m /var/spool/postfix/var/run/saslauthd'# /etc/default/saslauthd \n")
    saslauthd_launch.write("chmod 1777 /etc/resolv.conf \n")
    saslauthd_launch.write("chmod 1777 -R /var/spool/postfix/ \n")
    saslauthd_launch.write("systemctl restart saslauthd \n")
    saslauthd_launch.close()
    instance.files.put("/root/saslauthd_launcher.sh", open("simulation/workstations/"+instance.name+"/saslauthd_launcher.sh").read(), verbose=False)
    instance.execute(["chmod", "+x", "/root/saslauthd_launcher.sh"])
    instance.execute(["./saslauthd_launcher.sh"])

    result = instance.execute(["testsaslauthd", "-u", "cyrus", "-p", "cyrus123"])
    if result.exit_code == 0:
        if verbose:
            print(Fore.GREEN+"       Sasl configuration is working!"+Style.RESET_ALL)
    else:
        print(Fore.RED+"       Sasl failed during configuration..."+Style.RESET_ALL)

#######################################
#### Install and configure postfix ####
#######################################
    launch_postfix = open("simulation/workstations/"+instance.name+"/launch_postfix.sh", "w")
    launch_postfix.write("#!/bin/bash\n")
    launch_postfix.write("debconf-set-selections <<< \"postfix postfix/mailname string "+instance.name+"."+arg["domain_name"]+"\" \n")
    launch_postfix.write("debconf-set-selections <<< \"postfix postfix/main_mailer_type string 'Internet Site'\" \n")
    launch_postfix.write("DEBIAN_FRONTEND=noninteractive apt-get install -y postfix \n")
    launch_postfix.write("touch /var/lib/cyrus/tls_sessions.db \n")
    launch_postfix.write("chown cyrus:mail /var/lib/cyrus/tls_sessions.db \n")
    launch_postfix.close()
    instance.files.put("/root/launch_postfix.sh", open("simulation/workstations/"+instance.name+"/launch_postfix.sh", encoding="utf-8").read(), verbose=False)
    instance.execute(["chmod", "+x", "/root/launch_postfix.sh"])
    instance.execute(["./launch_postfix.sh"])
    instance.execute(["apt-get", "install", "-y", "postfix-ldap"])
    instance.execute(["systemctl", "restart", "postfix"])
    if instance.files.delete_available():
        instance.files.delete("/root/launch_postfix.sh")
        if verbose:
            print(Fore.GREEN + "       Installation script has been deleted!" + Style.RESET_ALL)
    else:
        print(Fore.RED + "       Installation script can't be deleted!" + Style.RESET_ALL)

    result = instance.execute(["apt-get", "install", "-y", "bsd-mailx"])
    if result.exit_code == 0:
        if verbose:
            print(Fore.GREEN+"      bsd-mailx installation was done!"+Style.RESET_ALL)
    else:
        print(Fore.RED+"       bsd-mailx installation failed..."+Style.RESET_ALL)

    main_cf = open("simulation/workstations/"+instance.name+"/update_main_cf.sh", "w")
    main_cf.write("#!/bin/bash \n")
    main_cf.write("echo 'cyrus   unix    -       n       n       -       -       pipe\n  flags=R user=cyrus argv=/usr/sbin/cyrdeliver -e -m\n  ${extension} ${user}' >> /etc/postfix/master.cf \n")
    main_cf.close()
    instance.files.put("/root/update_main_cf.sh", open("simulation/workstations/"+instance.name+"/update_main_cf.sh").read())
    instance.execute(["chmod", "+x", "/root/update_main_cf.sh"])
    instance.execute(["./update_main_cf.sh"])
    instance.execute(["systemctl", "restart", "postfix"])
    if instance.files.delete_available():
        instance.files.delete("/root/update_main_cf.sh")
        if verbose:
            print(Fore.GREEN + "      Installation script has been deleted!" + Style.RESET_ALL)
    else:
        print(Fore.RED + "      Installation script can't be deleted!" + Style.RESET_ALL)

    main_cf = open("simulation/workstations/"+instance.name+"/main.cf", "w")
    main_cf.write("myorigin = /etc/mailname \n")
    main_cf.write("smtpd_banner = $myhostname ESMTP $mail_name (Debian/GNU) \n")
    main_cf.write("biff = no \n")
    main_cf.write("append_dot_mydomain = no \n")
    main_cf.write("delay_warning_time = 4h \n")
    main_cf.write("myhostname = "+instance.name+"."+arg["domain_name"]+"\n")
    main_cf.write("mailbox_maps = ldap:/etc/postfix/ldap-accounts.cf \n")
    main_cf.write("alias_maps = ldap:/etc/postfix/ldap-aliases.cf \n")
    main_cf.write("mydestination = "+arg["domain_name"]+", "+instance.name+"."+arg["domain_name"]+", localhost"+arg["domain_name"]+", localhost \n")
    main_cf.write("relayhost = \n")
    main_cf.write("mynetworks = 127.0.0.0/8 \n")
    main_cf.write("local_transport = cyrus \n")
    main_cf.write("recipient_delimiter = + \n")
    main_cf.write("smtpd_sasl_auth_enable = yes \n")
    main_cf.write("smtpd_relay_restrictions = reject_unauth_destination \n")
    main_cf.write("smtpd_sasl_security_options = noanonymous \n")
    main_cf.write("smtpd_sasl_local_domain = \n")
    main_cf.write("inet_protocols = ipv4 \n")
    main_cf.write("inet_interfaces = all \n")
    main_cf.close()
    instance.files.put("/etc/postfix/main.cf", open("simulation/workstations/"+instance.name+"/main.cf").read(), verbose=False)

    ldap_accounts_cf = open("simulation/workstations/"+instance.name+"/ldap_accounts.cf", "w")
    ldap_accounts_cf.write("server_host = "+arg["ldap_ip"]+" \n")
    ldap_accounts_cf.write("server_port = "+arg["ldap_port"]+ "\n")
    ldap_accounts_cf.write("search_base = "+arg["ldap_dn"]+" \n")
    ldap_accounts_cf.write("query_filter = (&(objectClass=InetOrgPerson)(mail=%s)) \n")
    ldap_accounts_cf.write("result_attribute = uid \n")
    ldap_accounts_cf.write("bind = yes \n")
    ldap_accounts_cf.write("bind_dn = "+arg["ldap_manager"]+ " \n")
    ldap_accounts_cf.write("bind_pw = "+arg["ldap_manager_password"]+" \n")
    ldap_accounts_cf.write("version = 3 \n")
    ldap_accounts_cf.close()
    instance.files.put("/etc/postfix/ldap-accounts.cf", open("simulation/workstations/"+instance.name+"/ldap_accounts.cf").read(), verbose=False)

    ldap_accounts_cf = open("simulation/workstations/"+instance.name+"/ldap-aliases.cf", "w")
    ldap_accounts_cf.write("server_host = "+arg["ldap_ip"]+" \n")
    ldap_accounts_cf.write("server_port = "+arg["ldap_port"]+ "\n")
    ldap_accounts_cf.write("search_base = "+arg["ldap_dn"]+" \n")
    ldap_accounts_cf.write("query_filter = (&(objectClass=InetOrgPerson)(mail=%s)) \n")
    ldap_accounts_cf.write("result_attribute = mail \n")
    ldap_accounts_cf.write("bind = yes \n")
    ldap_accounts_cf.write("bind_dn = "+arg["ldap_manager"]+ " \n")
    ldap_accounts_cf.write("bind_pw = "+arg["ldap_manager_password"]+" \n")
    ldap_accounts_cf.write("version = 3")
    ldap_accounts_cf.close()
    instance.files.put("/etc/postfix/ldap-aliases.cf", open("simulation/workstations/"+instance.name+"/ldap-aliases.cf").read(), verbose=False)

    smtpd_conf = open("simulation/workstations/"+instance.name+"/smtpd.conf", "w")
    smtpd_conf.write("pwcheck_method: saslauthd \n")
    smtpd_conf.write("mech_list: plain \n")
    smtpd_conf.close()
    instance.files.put("/etc/postfix/sasl/smtpd.conf", open("simulation/workstations/"+instance.name+"/smtpd.conf").read(), verbose=False)

def enable_ssl_imapd(instance, arg, verbose=True):
    """ Create certificate and encrypt imapd communication """
    list_ca = " ".join(arg["cas_path"])
    create_execute_command_remote_bash(instance, {"script_name":"launch_cyrus_imapd_ssl.sh", "commands":[
                                                                                                         "#### create ca bundle ###",
                                                                                                         "cat "+list_ca+" > "+arg["ca_dir"]+"ca.bundle",
                                                                                                         "#### imapd ###",
                                                                                                         "sed -i -e \'s|#tls_server_cert: /etc/ssl/certs/ssl-cert-snakeoil.pem|tls_server_cert: "+arg["cert_path"]+"|\' /etc/imapd.conf",
                                                                                                         "sed -i -e \'s|#tls_server_key: /etc/ssl/private/ssl-cert-snakeoil.key|tls_server_key: "+arg["key_path"]+"|\' /etc/imapd.conf",
                                                                                                         "sed -i -e \'s|tls_client_ca_dir: /etc/ssl/certs|tls_client_ca_dir: "+arg["ca_dir"]+"|\' /etc/imapd.conf",
                                                                                                         "sed -i -e \'s|#tls_client_ca_file: /etc/ssl/certs/cyrus-imapd-ca.pem|tls_client_ca_file: "+arg["ca_dir"]+"ca.bundle|\' /etc/imapd.conf",
                                                                                                         "### Cyrus ###",
                                                                                                         "sed -i -e \'s|imap|#imap|\' /etc/cyrus.conf",
                                                                                                         "sed -i \'s|# add or remove based on preferences|imaps         cmd=\"imapd -s -U 30\" listen=\"imaps\" prefork=0 maxchild=100|\' /etc/cyrus.conf"
                                                                                                        ], "delete":"false"}, verbose=False)

    if add_user2group(instance, {"username":"cyrus", "group_name":"ssl-cert"}, verbose=False) == 1:
        return 1
    if change_fileorfolder_group_owner(instance, {"new_group":"ssl-cert", "fileorfolder_path":"/certs"}, verbose=False) == 1:
        return 1
    if restart_service(instance, {"service":"cyrus-imapd"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN+ "      Imapd have been secured by certificate ["+arg["cert_path"]+"]" +Style.RESET_ALL)
    return 0

def enable_ssl_postfix(instance, arg, verbose=True):
    """ Create certificate and encrypt postfix communication """
    list_ca = " ".join(arg["cas_path"])
    create_execute_command_remote_bash(instance, {"script_name":"launch_postfix_ssl.sh", "commands":[
                                                                                                        "#### create ca bundle ###",
                                                                                                        "cat "+list_ca+" > "+arg["ca_dir"]+"ca.bundle"
                                                                                                    ], "delete":"false"}, verbose=False)

    main_cf = open("simulation/workstations/"+instance.name+"/main.cf", "a+")
    main_cf.write("smtpd_tls_cert_file="+arg["cert_path"]+" \n")
    main_cf.write("smtpd_tls_key_file="+arg["key_path"]+" \n")
    main_cf.write("smtpd_tls_CAfile="+arg["ca_dir"]+"ca.bundle \n")
    main_cf.write("smtpd_use_tls=yes \n")

    main_cf.write("smtp_tls_CAfile="+arg["ca_dir"]+"ca.bundle \n")
    main_cf.write("smtp_use_tls=yes \n")

    main_cf.write("smtpd_tls_session_cache_database = btree:${queue_directory}/smtpd_scache \n")
    main_cf.write("smtp_tls_session_cache_database = btree:${queue_directory}/smtp_scache \n")
    main_cf.close()
    if upload_file(instance, {"instance_path":"/etc/postfix/main.cf", "host_manager_path": "simulation/workstations/"+instance.name+"/main.cf"}) == 1:
        return 1
    if add_user2group(instance, {"username":"postfix", "group_name":"ssl-cert"}, verbose=False) == 1:
        return 1
    if change_fileorfolder_group_owner(instance, {"new_group":"ssl-cert", "fileorfolder_path":"/certs"}, verbose=False) == 1:
        return 1
    if restart_service(instance, {"service":"postfix"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN+"      Postfix have been secured by certificate ["+arg["cert_path"]+"]"+Style.RESET_ALL)
    return 0
