from colorama import Fore, Style
from .logic_actions_utils import update,install, upload_file, restart_service, delete_file

def install_web_server(client, instance, arg, verbose=True):
    install(client,instance,{"module":"apache2"}, verbose=False)
    instance.files.recursive_put("templates/"+arg["website_project_name"],"/var/www/html")
    restart_service(client,instance,{"service":"apache2"}, verbose=False)

def install_dvwa(client, instance, arg, verbose=True):
    update(client,instance,{"":""}, verbose=False)
    install(client,instance,{"module":"apache2"}, verbose=False)
    install(client,instance,{"module":"mysql-server"}, verbose=False)
    install(client,instance,{"module":"php"}, verbose=False)
    install(client,instance,{"module":"php7.2-mysql"}, verbose=False)
    install(client,instance,{"module":"php-gd"}, verbose=False)
    install(client,instance,{"module":"libapache2-mod-php"}, verbose=False)
    install(client,instance,{"module":"git"}, verbose=False)

    result = instance.execute(["git","clone","https://github.com/ethicalhack3r/DVWA","/tmp/DVWA"])
    delete_file(client,instance,{"instance_path":"/var/www/html/index.html"}, verbose=False)
    instance.execute(["rsync","-avP","/tmp/DVWA/","/var/www/html/"])
    instance.execute(["cp","/var/www/html/config/config.inc.php.dist","/var/www/html/config/config.inc.php"])

    if result.exit_code == 0:
        instance.execute(["mysql","-e","create database dvwa;"])
        instance.execute(["mysql","-e","create user dvwa@localhost identified by 'p@ssw0rd';"])
        instance.execute(["mysql","-e","grant all on dvwa.* to dvwa@localhost;"])
        result = instance.execute(["mysql","-e","flush privileges;"])
        if result.exit_code == 0:
            result = instance.execute(["chmod","a+w","/var/www/html/hackable/uploads/"])
            # result = instance.execute(["chmod","a+w","/var/www/html/dvwa/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt"])
            restart_service(client,instance,{"service":"apache2"}, verbose=False)
            restart_service(client,instance,{"service":"mysql"}, verbose=False)
            if result.exit_code == 0:
                if verbose:
                    print( Fore.GREEN + "      Config file for dvwa is up" + Style.RESET_ALL )
            else:
                print( Fore.RED + "      Error while changing folder rights in dvwa "+" ["+result.stderr+"]" + Style.RESET_ALL )
        else:
            print( Fore.RED + "      Error during configuration of SQL in dvwa "+" ["+result.stderr+"]" + Style.RESET_ALL )
    else:
        print( Fore.RED + "      Error while copying config file of dvwa "+" ["+result.stderr+"]" + Style.RESET_ALL )

def enable_ssl(client, instance, arg, verbose=True):
    instance.execute(["a2enmod","ssl"])
    restart_service(client,instance,{"service":"apache2"}, verbose=False)
    result = instance.execute(["a2enmod","ssl"])
    if "Module ssl already enabled" in result.stdout:
        print (Fore.GREEN + "      SSL mod activated!" + Style.RESET_ALL)
    else:
        print (Fore.RED + "      SSL mod failed!" + Style.RESET_ALL)

    instance.execute(["a2dissite","default"])

    instance.execute(["a2ensite","default-ssl"])
    restart_service(client, instance, {"service":"apache2"}, verbose=False)
    result = instance.execute(["a2ensite","default-ssl"])
    if "Site default-ssl already enabled" in result.stdout:
        print (Fore.GREEN + "      Switch to default-ssl conf file!" + Style.RESET_ALL)
    else:
        print (Fore.RED + "       Fail during switch to default-ssl conf file!" + Style.RESET_ALL)

    list_ca = " ".join(arg["cas_path"])
    launch_apache2_ssl = open("simulation/workstations/"+instance.name+"/launch_apache2_ssl.sh", "w")
    launch_apache2_ssl.write("#!/bin/bash\n")
    launch_apache2_ssl.write("sed -i -e 's|Listen 80|#Listen 80|' /etc/apache2/ports.conf\n")
    launch_apache2_ssl.write("#### create ca bundle ###\n")
    launch_apache2_ssl.write("cat "+list_ca+" > "+arg["ca_dir"]+"ca.bundle\n")
    launch_apache2_ssl.close()
    upload_file(client, instance, {"instance_path":"/root/launch_apache2_ssl.sh", "host_manager_path": "simulation/workstations/"+instance.name+"/launch_apache2_ssl.sh"}, verbose=False)
    instance.execute(["chmod","+x","/root/launch_apache2_ssl.sh"])
    instance.execute(["./launch_apache2_ssl.sh"])
    delete_file(client,instance,{"instance_path":"/root/launch_apache2_ssl.sh"}, verbose=False)

    ssl_conf = open("simulation/workstations/"+instance.name+"/ssl_conf.sh", "w")
    ssl_conf.write("sed -i -e 's|SSLCertificateFile|#SSLCertificateFile|' /etc/apache2/sites-enabled/default-ssl.conf\n")
    ssl_conf.write("sed -i -e 's|SSLCertificateKeyFile|#SSLCertificateKeyFile|' /etc/apache2/sites-enabled/default-ssl.conf\n")
    ssl_conf.write("sed -i -e '31 a \                 SSLCertificateFile \""+arg["cert_path"]+"\"' /etc/apache2/sites-enabled/default-ssl.conf\n")
    ssl_conf.write("sed -i -e '33 a \                 SSLCertificateKeyFile \""+arg["key_path"]+"\"' /etc/apache2/sites-enabled/default-ssl.conf\n")
    ssl_conf.write("sed -i -e '51 a \                 SSLCACertificatePath \""+arg["ca_dir"]+"\"' /etc/apache2/sites-enabled/default-ssl.conf\n")
    ssl_conf.write("sed -i -e '52 a \                 SSLCACertificateFile \""+arg["ca_dir"]+"ca.bundle"+"\"' /etc/apache2/sites-enabled/default-ssl.conf\n")
    ssl_conf.close()

    upload_file(client, instance, {"instance_path":"/root/ssl_conf.sh", "host_manager_path": "simulation/workstations/"+instance.name+"/ssl_conf.sh"}, verbose=False)
    instance.execute(["chmod","+x","/root/ssl_conf.sh"])
    instance.execute(["./ssl_conf.sh"])
    delete_file(client,instance,{"instance_path":"/root/ssl_conf.sh"}, verbose=False)
    restart_service(client,instance,{"service":"apache2"}, verbose=False)

    # {"name":"enable_ssl", "args": {"cert_path":"/certs/dvwa.silicom.com/dvwa.silicom.com.cert","key_path":"/certs/dvwa.silicom.com/dvwa.silicom.com.key","ca_dir":"/certs/dvwa.silicom.com/","cas_path":["/certs/dvwa.silicom.com/caroot.com.cert","/certs/dvwa.silicom.com/silicom.com.cert"]} },

def install_chat_application(client, instance, arg, verbose=True):
    install(client,instance,{"module":"apache2"}, verbose=False)
    install(client,instance,{"module":"php"}, verbose=False)
    install(client,instance,{"module":"php-mysql"}, verbose=False)
    install(client,instance,{"module":"mysql-server"}, verbose=False)

    instance.execute(["rm","-R","/var/www/html"])
    instance.execute(["git","clone","https://github.com/yogeeswar2001/chat-application.git","/var/www/html/"])

    instance.execute(["mysql","-e","create database chat_app;"])
    instance.execute(["mysql","-e","create user chatuser@localhost identified by 'chat123';"])
    instance.execute(["mysql","-e","grant all privileges on chat_app.* to chatuser@localhost;"])

    chat_installation_file = open("simulation/workstations/"+instance.name+"/chat_installation_file.sh", "w")
    chat_installation_file.write("#!/bin/bash\n")
    chat_installation_file.write("sed -i -e \'s#username = \"root\"#username = \"chatuser\"#\' /var/www/html//db/db_conn.php \n")
    chat_installation_file.write("sed -i -e \'s#pwd = \"yogeeswar\"#pwd = \"chat123\"#\' /var/www/html/db/db_conn.php \n")
    chat_installation_file.write("sed -i -e \"s#username = \'root\'#username = \'chatuser\'#\" /var/www/html/db/db_conn_pdo.php \n")
    chat_installation_file.write("sed -i -e \"s#pwd = \'yogeeswar\'#pwd = \'chat123\'#\" /var/www/html/db/db_conn_pdo.php \n")
    chat_installation_file.write("sed -i -e \'s#COLLATE=utf8mb4_0900_ai_ci# #\' /var/www/html/db/chat_app.sql \n")
    chat_installation_file.close()
    upload_file(client,instance,{"instance_path":"/root/chat_installation_file.sh","host_manager_path":"simulation/workstations/"+instance.name+"/chat_installation_file.sh"}, verbose=False)
    instance.execute(["chmod", "+x", "/root/chat_installation_file.sh"])
    instance.execute(["./chat_installation_file.sh"])

    instance.execute(["mysql","-e","use chat_app; source /var/www/html/db/chat_app.sql;"])

    restart_service(client,instance,{"service":"mysql"}, verbose=False)
    restart_service(client,instance,{"service":"apache2"}, verbose=False)


# {"name":"enable_ssl", "args": {"cert_path":"/certs/dvwa.silicom.com/dvwa.silicom.com.cert","key_path":"/certs/dvwa.silicom.com/dvwa.silicom.com.key","ca_dir":"/certs/dvwa.silicom.com/","cas_path":["/certs/dvwa.silicom.com/caroot.com.cert","/certs/dvwa.silicom.com/silicom.com.cert"]} },