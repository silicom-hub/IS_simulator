""" This file contain functions about mail configuration """
from colorama import Fore, Style
from .logic_actions_utils import save_nameserver_ip, add_nameserver, clear_nameserver, create_execute_command_remote_bash, execute_command, upload_file, update, install, delete_file, restart_service, add_user2group, change_fileorfolder_group_owner, create_local_user, change_permission

def original_mail_installation(instance, arg, verbose=True):
    """ Install and configure dovecot and postfix and synchronize imapd and smtp with openldap

    args:
        domain_name (str): This value is the domain name.
                    Examples:
                    domain_name -> xxxx.xxxx.xxxx
        networks (list): This list contains all networks allowed to connect.
        relays (list): .
            relay (dict): This value refer to all smtp server who relay email.
                args {
                        domain (str): This value is the smtp server's domain name.
                        server (str): This value indicates the smtp server's ip or domain name.
                        port (str): This value correspond to the smtp server's port.
                     }
        ldap (dict, Optional): .
            args { 
                    ldap_ip (str): This value correspond to ldap server's ip.
                    ldap_domain (str): This value correspond to ldap server's domain name.
                    ldap_dn (str): This value correspond to ldap server's domain name.
                    ldap_manager (str): This value refer to the ldap admin's distinguished name.
                        Examples:
                        ldap_manager -> cn=admin,dc=mycompany,dc=com

                    ldap_manager_password (str): This value correspond to the admin's password.
                    ldap_port (str): This value indicates the ldap server's port:
                        Examples:
                        ldap_port [Tls version] -> 636 
                    domain_name (str): 
                    ssl (str): This value is a boolean who indicates if the protocol is encrypted.
                        Examples:
                        ssl [tls version] -> true 
                 }
        sql (dict, Optional): .
            users (list): 
                user (dict):
                args {
                        email (str): This value indicates the user's email.
                        password (str): This value indicates the user's password.
                     }   

        
    """
    create_execute_command_remote_bash(instance, {"script_name":"install_postfix.sh", "commands":[
                                                                                                    "debconf-set-selections <<< \"postfix postfix/mailname string "+instance.name+"."+arg["domain_name"]+"\"",
                                                                                                    "debconf-set-selections <<< \"postfix postfix/main_mailer_type string 'Internet Site'\"",
                                                                                                    "DEBIAN_FRONTEND=noninteractive apt-get install -y postfix",
                                                                                                ], "delete":"false"}, verbose=False)
    if arg["sql"] != {}:
        install(instance, {"module":"postfix-mysql"}, verbose=False)
        install(instance, {"module":"dovecot-mysql"}, verbose=False)
        install(instance, {"module":"mysql-server"}, verbose=False)
    if arg["ldap"] != {}:
        install(instance, {"module":"postfix-ldap"}, verbose=False)
        install(instance, {"module":"dovecot-ldap"}, verbose=False)
    clear_nameserver(instance, verbose=False)
    install(instance, {"module":"dovecot-imapd"}, verbose=False)
    install(instance, {"module":"dovecot-lmtpd"}, verbose=False)
    clear_nameserver(instance, verbose=False)
    change_permission(instance, {"owner":"7", "group":"0", "other":"0", "file_path":"/etc/postfix/dynamicmaps.cf"}, verbose=False)
    if arg["ssl"] != {}:
        list_ca = " ".join(arg["ssl"]["cas_path"])
        create_execute_command_remote_bash(instance, {"script_name":"create_ssl_bundle.sh", "commands":[
                                                                                                         "#### create ca bundle ###",
                                                                                                         "cat "+list_ca+" > "+arg["ssl"]["ca_dir"]+"ca.bundle"
                                                                                                         ], "delete":"false"}, verbose=False)

#####################################
#### Install and configure mysql ####
#####################################
    if arg["sql"] != {}:
        execute_command(instance, {"command":["mysql", "-e", "CREATE DATABASE mailserver;"], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-e", "CREATE USER 'mailuser'@'localhost' IDENTIFIED BY 'mailuser123';"], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-e", "grant all privileges on mailserver.* to mailuser@localhost;"], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-e", "FLUSH PRIVILEGES;"], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-u", "mailuser", "-pmailuser123", "-e", """ USE mailserver; CREATE TABLE virtual_domains (
                                                                                                    id int(11) NOT NULL auto_increment,
                                                                                                    name varchar(50) NOT NULL,
                                                                                                    PRIMARY KEY (id)
                                                                                                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8; """], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-u", "mailuser", "-pmailuser123", "-e", """ USE mailserver; CREATE TABLE `virtual_users` (
                                                                                                    id int(11) NOT NULL auto_increment,
                                                                                                    domain_id int(11) NOT NULL,
                                                                                                    password varchar(106) NOT NULL,
                                                                                                    email varchar(100) NOT NULL,
                                                                                                    PRIMARY KEY (id),
                                                                                                    UNIQUE KEY email (email),
                                                                                                    FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
                                                                                                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8; """], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-u", "mailuser", "-pmailuser123", "-e", """ USE mailserver; CREATE TABLE virtual_aliases (
                                                                                                    id int(11) NOT NULL auto_increment,
                                                                                                    domain_id int(11) NOT NULL,
                                                                                                    source varchar(100) NOT NULL,
                                                                                                    destination varchar(100) NOT NULL,
                                                                                                    PRIMARY KEY (id),
                                                                                                    FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
                                                                                                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8; """], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-u", "mailuser", "-pmailuser123", "-e", "INSERT INTO mailserver.virtual_domains (name) VALUES ('"+arg["domain_name"]+"');"], "expected_exit_code":"0"}, verbose=False)
        for user in arg["sql"]["users"]:
            execute_command(instance, {"command":["mysql", "-u", "mailuser", "-pmailuser123", "-e", "INSERT INTO mailserver.virtual_users (domain_id, password , email) VALUES ('1', TO_BASE64(UNHEX(SHA2('"+user["password"]+"',512))), '"+user["email"]+"');"], "expected_exit_code":"0"}, verbose=False)

#######################################
#### Install and configure postfix ####
#######################################
    if arg["ssl"] != {}:
        if add_user2group(instance, {"username":"postfix", "group_name":"ssl-cert"}, verbose=False) == 1:
            return 1
        if change_fileorfolder_group_owner(instance, {"new_group":"ssl-cert", "fileorfolder_path":"/certs"}, verbose=False) == 1:
            return 1

    main_cf = open("simulation/workstations/"+instance.name+"/main.cf", "w")
    main_cf.write("smtpd_banner = $myhostname ESMTP $mail_name\n")
    main_cf.write("biff = no \n")
    main_cf.write("append_dot_mydomain = no \n")
    main_cf.write("readme_directory = no \n")
    main_cf.write("compatibility_level=2 \n")

    ### SSL
    if arg["ssl"] != {}:
        main_cf.write("smtpd_tls_cert_file="+arg["ssl"]["cert_path"]+" \n")
        main_cf.write("smtpd_tls_key_file="+arg["ssl"]["key_path"]+" \n")
        main_cf.write("smtpd_tls_CAfile="+arg["ssl"]["ca_dir"]+"ca.bundle \n")
        main_cf.write("smtpd_use_tls=yes \n")
        main_cf.write("smtpd_tls_session_cache_database = btree:${queue_directory}/smtpd_scache \n")
        main_cf.write("smtp_tls_session_cache_database = btree:${queue_directory}/smtp_scache \n")

    ### Authentication
    main_cf.write("smtpd_sasl_type = dovecot \n")
    main_cf.write("smtpd_sasl_path = private/auth \n")
    main_cf.write("smtpd_sasl_auth_enable = yes \n")

    ### Restriction
    main_cf.write("smtpd_helo_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_invalid_helo_hostname, reject_non_fqdn_helo_hostname  \n")
    main_cf.write("smtpd_recipient_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_non_fqdn_recipient, reject_unauth_destination \n")
    main_cf.write("smtpd_sender_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_non_fqdn_sender \n")
    main_cf.write("smtpd_relay_restrictions = permit_mynetworks, permit_sasl_authenticated, defer_unauth_destination \n")

    ### MAIN
    main_cf.write("smtp_dns_support_level = enabled \n")
    main_cf.write("myhostname = "+instance.name+"."+arg["domain_name"]+" \n")
    main_cf.write("mydomain = "+arg["domain_name"]+" \n")
    main_cf.write("myorigin = $mydomain \n")
    main_cf.write("mydestination = localhost \n")
    main_cf.write("relayhost = \n")
    main_cf.write("relay_domains = hash:/etc/postfix/relaydomains \n")
    main_cf.write("mynetworks = 127.0.0.0/8")
    for network in arg["networks"]:
        main_cf.write(", "+network)
    main_cf.write("\n")
    main_cf.write("mailbox_size_limit = 0 \n")
    main_cf.write("recipient_delimiter = + \n")
    main_cf.write("inet_protocols = ipv4 \n")
    main_cf.write("inet_interfaces = all \n")
    main_cf.write("virtual_transport = lmtp:unix:private/dovecot-lmtp \n")
    if arg["ldap"] != {}:
        main_cf.write("virtual_mailbox_domains = "+arg["domain_name"]+" \n")
        main_cf.write("virtual_mailbox_maps = ldap:/etc/postfix/ldap-accounts.cf \n")
    if arg["sql"] != {}:
        main_cf.write("virtual_mailbox_domains = mysql:/etc/postfix/mysql-virtual-mailbox-domains.cf \n")
        main_cf.write("virtual_mailbox_maps = mysql:/etc/postfix/mysql-virtual-mailbox-maps.cf \n")
        main_cf.write("virtual_alias_maps = mysql:/etc/postfix/mysql-virtual-alias-maps.cf, mysql:/etc/postfix/mysql-virtual-email2email.cf \n")
    main_cf.close()
    if upload_file(instance, {"instance_path":"/etc/postfix/main.cf", "host_manager_path":"simulation/workstations/"+instance.name+"/main.cf"}, verbose=False) == 1:
        return 1

    relaydomains = open("simulation/workstations/"+instance.name+"/relaydomains", "w")
    for relay in arg["relays"]:
        relaydomains.write(relay["domain"]+" #domain\n")
    relaydomains.close()
    if upload_file(instance, {"instance_path":"/etc/postfix/relaydomains", "host_manager_path":"simulation/workstations/"+instance.name+"/relaydomains"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["postmap", "/etc/postfix/relaydomains"], "expected_exit_code":"0"}, verbose=False)

    transport = open("simulation/workstations/"+instance.name+"/transport", "w")
    for relay in arg["relays"]:
        transport.write(relay["domain"]+" smtp:["+relay["server"]+"]\n")
    transport.close()
    if upload_file(instance, {"instance_path":"/etc/postfix/transport", "host_manager_path":"simulation/workstations/"+instance.name+"/transport"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["postmap", "/etc/postfix/transport"], "expected_exit_code":"0"}, verbose=False)

    if arg["sql"] != {}:
        mysql_virtual_mailbox_domains = open("simulation/workstations/"+instance.name+"/mysql-virtual-mailbox-domains.cf", "w")
        mysql_virtual_mailbox_domains.write("user = mailuser \n")
        mysql_virtual_mailbox_domains.write("password = mailuser123 \n")
        mysql_virtual_mailbox_domains.write("hosts = 127.0.0.1 \n")
        mysql_virtual_mailbox_domains.write("dbname = mailserver \n")
        mysql_virtual_mailbox_domains.write("query = SELECT 1 FROM virtual_domains WHERE name='%s' ")
        mysql_virtual_mailbox_domains.close()
        if upload_file(instance, {"instance_path":"/etc/postfix/mysql-virtual-mailbox-domains.cf", "host_manager_path":"simulation/workstations/"+instance.name+"/mysql-virtual-mailbox-domains.cf"}, verbose=False) == 1:
            return 1   
        mysql_virtual_mailbox_maps = open("simulation/workstations/"+instance.name+"/mysql-virtual-mailbox-maps.cf", "w")
        mysql_virtual_mailbox_maps.write("user = mailuser")
        mysql_virtual_mailbox_maps.write("password = mailuser123 \n")
        mysql_virtual_mailbox_maps.write(" hosts = 127.0.0.1 \n")
        mysql_virtual_mailbox_maps.write("dbname = mailserver \n")
        mysql_virtual_mailbox_maps.write("query = SELECT 1 FROM virtual_users WHERE email='%s'")
        mysql_virtual_mailbox_maps.close()
        if upload_file(instance, {"instance_path":"/etc/postfix/mysql-virtual-mailbox-maps.cf", "host_manager_path":"simulation/workstations/"+instance.name+"/mysql-virtual-mailbox-maps.cf"}, verbose=False) == 1:
            return 1
        mysql_virtual_alias_maps = open("simulation/workstations/"+instance.name+"/mysql-virtual-alias-maps.cf", "w")
        mysql_virtual_alias_maps.write("user = mailuser \n")
        mysql_virtual_alias_maps.write("password = mailuser123 \n")
        mysql_virtual_alias_maps.write("hosts = 127.0.0.1 \n")
        mysql_virtual_alias_maps.write("dbname = mailserver \n")
        mysql_virtual_alias_maps.write("query = SELECT destination FROM virtual_aliases WHERE source='%s'")
        mysql_virtual_alias_maps.close()
        if upload_file(instance, {"instance_path":"/etc/postfix/mysql-virtual-alias-maps.cf", "host_manager_path":"simulation/workstations/"+instance.name+"/mysql-virtual-alias-maps.cf"}, verbose=False) == 1:
            return 1
        mysql_virtual_email2email = open("simulation/workstations/"+instance.name+"/mysql-virtual-email2email.cf", "w")
        mysql_virtual_email2email.write("user = mailuser \n")
        mysql_virtual_email2email.write("password = mailuser123 \n")
        mysql_virtual_email2email.write("hosts = 127.0.0.1 \n")
        mysql_virtual_email2email.write("dbname = mailserver \n")
        mysql_virtual_email2email.write("query = SELECT email FROM virtual_users WHERE email='%s' \n")
        mysql_virtual_email2email.close()
        if upload_file(instance, {"instance_path":"/etc/postfix/mysql-virtual-email2email.cf", "host_manager_path":"simulation/workstations/"+instance.name+"/mysql-virtual-email2email.cf"}, verbose=False) == 1:
            return 1

    if arg["ldap"] != {}:
        ldap_accounts_cf = open("simulation/workstations/"+instance.name+"/ldap_accounts.cf", "w")
        if arg["ldap"]["ssl"] == "true":
            ldap_accounts_cf.write("server_host = ldaps://"+arg["ldap"]["ldap_ip"]+"\n")
        else:
            ldap_accounts_cf.write("server_host = ldap://"+arg["ldap"]["ldap_ip"]+"\n")
        ldap_accounts_cf.write("server_port = "+arg["ldap"]["ldap_port"]+ "\n")
        ldap_accounts_cf.write("search_base = "+arg["ldap"]["ldap_dn"]+" \n")
        ldap_accounts_cf.write("query_filter = (&(objectClass=InetOrgPerson)(mail=%s)) \n")
        ldap_accounts_cf.write("result_attribute = uid \n")
        ldap_accounts_cf.write("bind = yes \n")
        ldap_accounts_cf.write("bind_dn = "+arg["ldap"]["ldap_manager"]+ " \n")
        ldap_accounts_cf.write("bind_pw = "+arg["ldap"]["ldap_manager_password"]+" \n")
        ldap_accounts_cf.write("version = 3 \n")
        ldap_accounts_cf.close()
        if upload_file(instance, {"instance_path":"/etc/postfix/ldap-accounts.cf", "host_manager_path":"simulation/workstations/"+instance.name+"/ldap_accounts.cf"}, verbose=False) == 1:
            return 1

    change_permission(instance, {"owner":"7", "group":"0", "other":"0", "file_path":"/etc/postfix/"}, verbose=False)
    execute_command(instance, {"command":["postfix", "reload"], "expected_exit_code":"0"}, verbose=False)
    if restart_service(instance, {"service":"postfix"}, verbose=False) == 1:
        return 1
    print(Fore.GREEN + "      Mail service have been intalled and configured successfully!" + Style.RESET_ALL)

#######################################
#### Install and configure dovecot ####
#######################################
    dovecot_conf = open("simulation/workstations/"+instance.name+"/dovecot.conf", "w")
    dovecot_conf.write("!include_try /usr/share/dovecot/protocols.d/*.protocol \n")
    dovecot_conf.write("protocols = imap lmtp \n")
    dovecot_conf.write("dict { \n")
    dovecot_conf.write("} \n")
    dovecot_conf.write("!include conf.d/*.conf \n")
    dovecot_conf.write("!include_try local.conf \n")
    dovecot_conf.close()
    if upload_file(instance, {"instance_path":"/etc/dovecot/dovecot.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/dovecot.conf"}, verbose=False) == 1:
        return 1

    mail_conf = open("simulation/workstations/"+instance.name+"/10-mail.conf", "w")
    mail_conf.write("mail_location = maildir:/var/mail/vhosts/%d/%u \n")
    mail_conf.write("namespace inbox { \n")
    mail_conf.write("  inbox = yes \n")
    mail_conf.write("} \n")
    mail_conf.write("mail_privileged_group = mail \n")
    mail_conf.write("protocol !indexer-worker { \n")
    mail_conf.write("}\n")
    mail_conf.close()
    if upload_file(instance, {"instance_path":"/etc/dovecot/conf.d/10-mail.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/10-mail.conf"}, verbose=False) == 1:
        return 1

    execute_command(instance, {"command":["mkdir", "-p", "/var/mail/vhosts/"+arg["domain_name"]], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["groupadd", "-g", "5000","vmail"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["useradd", "-g", "vmail","-u","5000","vmail","-d","/var/mail"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["chown", "-R", "vmail:vmail","/var/mail"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["chmod", "777","-R","/var/mail"], "expected_exit_code":"0"}, verbose=False)

    auth_conf = open("simulation/workstations/"+instance.name+"/10-auth.conf", "w")
    if arg["ssl"] != {}:
        auth_conf.write("disable_plaintext_auth = yes \n")
    else:
        auth_conf.write("disable_plaintext_auth = no \n")
    auth_conf.write("auth_mechanisms = plain login \n")
    if arg["sql"] != {}:
        auth_conf.write("!include auth-system.conf.ext \n")
        auth_conf.write("!include auth-sql.conf.ext \n")
    elif arg["ldap"] != {}:
        auth_conf.write("!include auth-ldap.conf.ext \n")
    auth_conf.close()
    if upload_file(instance, {"instance_path":"/etc/dovecot/conf.d/10-auth.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/10-auth.conf"}, verbose=False) == 1:
        return 1

    if arg["sql"] != {}:
        auth_sql_conf = open("simulation/workstations/"+instance.name+"/auth-sql.conf.ext", "w")
        auth_sql_conf.write("passdb { \n")
        auth_sql_conf.write("   driver = sql \n")
        auth_sql_conf.write("   args = /etc/dovecot/dovecot-sql.conf.ext \n")
        auth_sql_conf.write("} \n")
        auth_sql_conf.write("userdb { \n")
        auth_sql_conf.write("   driver = static \n")
        auth_sql_conf.write("   args = uid=vmail gid=vmail home=/var/mail/vhosts/%d/%n \n")
        auth_sql_conf.write("} \n")
        auth_sql_conf.close()
        if upload_file(instance, {"instance_path":"/etc/dovecot/conf.d/auth-sql.conf.ext", "host_manager_path":"simulation/workstations/"+instance.name+"/auth-sql.conf.ext"}, verbose=False) == 1:
            return 1

        dovecot_sql_conf = open("simulation/workstations/"+instance.name+"/dovecot-sql.conf.ext", "w")
        dovecot_sql_conf.write("driver = mysql \n")
        dovecot_sql_conf.write("connect = host=127.0.0.1 dbname=mailserver user=mailuser password=mailuser123 \n")
        dovecot_sql_conf.write("default_pass_scheme = SHA512 \n")
        dovecot_sql_conf.write("password_query = SELECT email as user, password FROM virtual_users WHERE email='%u';\n")
        dovecot_sql_conf.close()
        if upload_file(instance, {"instance_path":"/etc/dovecot/dovecot-sql.conf.ext", "host_manager_path":"simulation/workstations/"+instance.name+"/dovecot-sql.conf.ext"}, verbose=False) == 1:
            return 1

    elif arg["ldap"] != {}:
        auth_ldap_conf = open("simulation/workstations/"+instance.name+"/auth-ldap.conf.ext", "w")
        auth_ldap_conf.write("passdb { \n")
        auth_ldap_conf.write("   driver = ldap \n")
        auth_ldap_conf.write("   args = /etc/dovecot/dovecot-ldap.conf.ext \n")
        auth_ldap_conf.write("} \n")
        auth_ldap_conf.write("userdb { \n")
        auth_ldap_conf.write("   driver = ldap \n")
        auth_ldap_conf.write("   args = /etc/dovecot/dovecot-ldap.conf.ext \n")
        auth_ldap_conf.write("} \n")
        auth_ldap_conf.close()
        if upload_file(instance, {"instance_path":"/etc/dovecot/conf.d/auth-ldap.conf.ext", "host_manager_path":"simulation/workstations/"+instance.name+"/auth-ldap.conf.ext"}, verbose=False) == 1:
            return 1

        dovecot_ldap_conf = open("simulation/workstations/"+instance.name+"/dovecot-ldap.conf.ext", "w")
        if arg["ldap"]["ssl"] == "true":
            dovecot_ldap_conf.write("uris = ldaps://"+arg["ldap"]["ldap_ip"]+":"+arg["ldap"]["ldap_port"]+" \n")
            dovecot_ldap_conf.write("tls_require_cert = allow \n")
        else:
            dovecot_ldap_conf.write("uris = ldap://"+arg["ldap"]["ldap_ip"]+":"+arg["ldap"]["ldap_port"]+" \n")
        dovecot_ldap_conf.write("dn = "+arg["ldap"]["ldap_manager"]+" \n")
        dovecot_ldap_conf.write("dnpass = "+arg["ldap"]["ldap_manager_password"]+" \n")
        dovecot_ldap_conf.write("base = "+arg["ldap"]["ldap_dn"]+"\n")
        dovecot_ldap_conf.write("auth_bind = yes \n")
        dovecot_ldap_conf.write("user_filter = (&(objectClass=posixAccount)(uid=%n)) \n")
        dovecot_ldap_conf.write("user_attrs = =uid=vmail, =gid=vmail, =mail=maildir:/var/mail/vhosts/"+arg["domain_name"]+"/%n\n")
        dovecot_ldap_conf.write("pass_filter = (&(objectClass=posixAccount)(mail=%u)) \n")
        dovecot_ldap_conf.close()
        if upload_file(instance, {"instance_path":"/etc/dovecot/dovecot-ldap.conf.ext", "host_manager_path":"simulation/workstations/"+instance.name+"/dovecot-ldap.conf.ext"}, verbose=False) == 1:
            return 1

    execute_command(instance, {"command":["chown", "-R", "vmail:dovecot","/etc/dovecot"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["chmod", "-R", "o-rwx","/etc/dovecot"], "expected_exit_code":"0"}, verbose=False)

    master_conf = open("simulation/workstations/"+instance.name+"/10-master.conf", "w")
    if arg["ssl"] == {}:
        master_conf.write("service imap-login { \n")
        master_conf.write("  inet_listener imap { \n")
        master_conf.write("    port = 143 \n")
        master_conf.write("  } \n")
        master_conf.write("} \n")
        master_conf.write("service imap { \n")
        master_conf.write("} \n")
        master_conf.write("service auth { \n")
        master_conf.write("  unix_listener auth-userdb { \n")
        master_conf.write("  } \n")
        master_conf.write("} \n")

        ssl_conf = open("simulation/workstations/"+instance.name+"/10-ssl.conf", "w")
        ssl_conf.write("ssl = no \n")
        ssl_conf.close()

    else:
        master_conf.write("service imap-login { \n")
        master_conf.write("  inet_listener imap { \n")
        master_conf.write("    port = 0 \n")
        master_conf.write("  } \n")
        master_conf.write("  inet_listener imaps { \n")
        master_conf.write("    port = 993 \n")
        master_conf.write("    ssl = yes \n")
        master_conf.write("  } \n")
        master_conf.write("} \n")
        master_conf.write("service imap { \n")
        master_conf.write("} \n")
        master_conf.write("service auth { \n")
        master_conf.write("  unix_listener auth-userdb { \n")
        master_conf.write("  } \n")
        master_conf.write("} \n")

        ssl_conf = open("simulation/workstations/"+instance.name+"/10-ssl.conf", "w")
        ssl_conf.write("ssl = required \n")
        ssl_conf.write("ssl_cert = <"+arg["ssl"]["cert_path"]+" \n")
        ssl_conf.write("ssl_key = <"+arg["ssl"]["key_path"]+" \n")
        ssl_conf.write("ssl_ca = <"+arg["ssl"]["key_path"]+" \n")
        ssl_conf.close()

    if upload_file(instance, {"instance_path":"/etc/dovecot/conf.d/10-ssl.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/10-ssl.conf"}, verbose=False) == 1:
            return 1

    master_conf.write("service lmtp { \n")
    master_conf.write("  unix_listener /var/spool/postfix/private/dovecot-lmtp { \n")
    master_conf.write("    mode = 0600 \n")
    master_conf.write("    user = postfix \n")
    master_conf.write("    group = postfix \n")
    master_conf.write("  } \n")
    master_conf.write("} \n")
    master_conf.write("service auth { \n")
    master_conf.write("  unix_listener /var/spool/postfix/private/auth { \n")
    master_conf.write("    mode = 0660 \n")
    master_conf.write("    user = postfix \n")
    master_conf.write("    group = postfix \n")
    master_conf.write("  } \n")
    master_conf.write("  unix_listener auth-userdb { \n")
    master_conf.write("    mode = 0600 \n")
    master_conf.write("    user = vmail \n")
    master_conf.write("  } \n")
    master_conf.write("  user = dovecot \n")
    master_conf.write("} \n")
    master_conf.write("service auth-worker { \n")
    master_conf.write("  user = mail \n")
    master_conf.write("} \n")
    master_conf.close()
    if upload_file(instance, {"instance_path":"/etc/dovecot/conf.d/10-master.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/10-master.conf"}, verbose=False) == 1:
        return 1
    if restart_service(instance, {"service":"dovecot"}, verbose=False) == 1:
        return 1

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

