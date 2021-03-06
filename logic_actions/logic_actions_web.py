""" This file contain function who configures web services """
import os
import time
from colorama import Fore, Style
from .logic_actions_utils import wget, clear_nameserver, create_execute_command_remote_bash, change_permission, change_fileorfolder_user_owner, change_fileorfolder_group_owner, update, install, upload_file, restart_service, delete_file, git_clone, execute_command, install_python_packages

def install_web_server(instance: object, arg: dict, verbose: bool=True):
    """ Install apache2 and copy web site project in /var/www/html in remote instance 
    instance (object): This argmument define the lxc instance.
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                website_project_name (str): directory path where is the main web project put in /var/www/html.
            }
    
    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    """
    if install(instance, {"module":"apache2"}, verbose=False):
        return 1
    instance.files.recursive_put("templates/"+arg["website_project_name"], "/var/www/html")
    if restart_service(instance, {"service":"apache2"}, verbose=False):
        return 1
    if verbose:
        print(Fore.GREEN + "      Web server have been installed successfully!" + Style.RESET_ALL)
    return 0

def install_dvwa(instance, verbose: bool=True):
    """ Install and configure DVWA web server 
    instance (object): This argmument define the lxc instance.
    verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.
    """
    if update(instance, verbose=False):
        return 1
    if install(instance, {"module":"nmap"}, verbose=False):
        return 1
    if install(instance, {"module":"apache2"}, verbose=False):
        return 1
    if install(instance, {"module":"mysql-server"}, verbose=False):
        return 1
    if install(instance, {"module":"php"}, verbose=False):
        return 1
    if install(instance, {"module":"php7.2-mysql"}, verbose=False):
        return 1
    if install(instance, {"module":"php-gd"}, verbose=False):
        return 1
    if install(instance, {"module":"libapache2-mod-php"}, verbose=False):
        return 1
    if install(instance, {"module":"git"}, verbose=False):
        return 1

    if delete_file(instance, {"instance_path":"/var/www/html/index.html"}, verbose=False):
        return 1

    git_clone(instance, {"branch":"","repository":"https://github.com/ethicalhack3r/DVWA","instance_path":"/var/www/html/"}, verbose=False)
    result = execute_command(instance, {"command":["cp", "/var/www/html/config/config.inc.php.dist", "/var/www/html/config/config.inc.php"], "expected_exit_code":"0"}, verbose=False)

    if result.exit_code == 0:
        execute_command(instance, {"command":["mysql", "-e", "create database dvwa;"], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-e", "create user dvwa@localhost identified by 'p@ssw0rd';"], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-e", "grant all on dvwa.* to dvwa@localhost;"], "expected_exit_code":"0"}, verbose=False)
        execute_command(instance, {"command":["mysql", "-e", "flush privileges;"], "expected_exit_code":"0"}, verbose=False)
        if result.exit_code == 0:
            result = execute_command(instance, {"command":["chmod", "a+w", "/var/www/html/hackable/uploads/"], "expected_exit_code":"0"}, verbose=False)
            if restart_service(instance, {"service":"apache2"}, verbose=False):
                return 1
            if restart_service(instance, {"service":"mysql"}, verbose=False):
                return 1
            if result.exit_code == 0:
                if verbose:
                    print(Fore.GREEN + "      Config file for dvwa is up" + Style.RESET_ALL)
                return 0
            print(Fore.RED + "      Error while changing folder rights in dvwa "+" ["+result.stderr+"]" + Style.RESET_ALL)
            return 1
        print(Fore.RED + "      Error during configuration of SQL in dvwa "+" ["+result.stderr+"]" + Style.RESET_ALL)
        return 1
    print(Fore.RED + "      Error while copying config file of dvwa "+" ["+result.stderr+"]" + Style.RESET_ALL)
    return 1

def enable_ssl(instance, arg: dict, verbose: bool=True):
    """ Create certificate and encrypt web communication. 
    instance (object): This argmument define the lxc instance.
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                cert_path (str): Path to certficate file.
                key_path (str): Path to private key file.
                ca_dir (str): Directory path where private key and path are stored.
                cas_path (list): List of public key who signed the certificate.
            }
    verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.

    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    """
    execute_command(instance, {"command":["a2enmod", "ssl"], "expected_exit_code":"0"}, verbose=False)
    if restart_service(instance, {"service":"apache2"}, verbose=False):
        return 1
    result = execute_command(instance, {"command":["a2enmod", "ssl"], "expected_exit_code":"0"}, verbose=False)
    if "Module ssl already enabled" in result.stdout:
        if verbose:
            print(Fore.GREEN + "      SSL mod activated!" + Style.RESET_ALL)
    else:
        print(Fore.RED + "      SSL mod failed!" + Style.RESET_ALL)
        return 1

    execute_command(instance, {"command":["a2ensite", "default-ssl"], "expected_exit_code":"0"}, verbose=False)
    result = restart_service(instance, {"service":"apache2"}, verbose=False)
    result = execute_command(instance, {"command":["a2ensite", "default-ssl"], "expected_exit_code":"0"}, verbose=False)
    if "Site default-ssl already enabled" in result.stdout:
        print(Fore.GREEN + "      Switch to default-ssl conf file!" + Style.RESET_ALL)
    else:
        print(Fore.RED + "       Fail during switch to default-ssl conf file!" + Style.RESET_ALL)

    list_ca = " ".join(arg["cas_path"])

    create_execute_command_remote_bash(instance, {"script_name":"launch_apache2_ssl.sh", "commands":["sed -i -e 's|Listen 80|#Listen 80|' /etc/apache2/ports.conf",
                                                                                                     "#### create ca bundle ###",
                                                                                                     "cat "+list_ca+" > "+arg["ca_dir"]+"ca.bundle"
                                                                                                    ], "delete":"false"}, verbose=False)

    create_execute_command_remote_bash(instance, {"script_name":"ssl_conf.sh", "commands":["sed -i -e 's|SSLCertificateFile|#SSLCertificateFile|' /etc/apache2/sites-enabled/default-ssl.conf",
                                                                                           "sed -i -e 's|SSLCertificateKeyFile|#SSLCertificateKeyFile|' /etc/apache2/sites-enabled/default-ssl.conf",
                                                                                           "sed -i -e '31 a \                 SSLCertificateFile \""+arg["cert_path"]+"\"' /etc/apache2/sites-enabled/default-ssl.conf\n",
                                                                                           "sed -i -e '33 a \                 SSLCertificateKeyFile \""+arg["key_path"]+"\"' /etc/apache2/sites-enabled/default-ssl.conf\n",
                                                                                           "sed -i -e '51 a \                 SSLCACertificatePath \""+arg["ca_dir"]+"\"' /etc/apache2/sites-enabled/default-ssl.conf\n",
                                                                                           "sed -i -e '52 a \                 SSLCACertificateFile \""+arg["ca_dir"]+"ca.bundle"+"\"' /etc/apache2/sites-enabled/default-ssl.conf\n"
                                                                                          ], "delete":"false"}, verbose=False)

    if restart_service(instance, {"service":"apache2"}, verbose=False):
        return 1
    if verbose:
        print(Fore.GREEN + "      Website has been secure by certificate: "+arg["cert_path"]+ Style.RESET_ALL)
    return 0

# {"name":"enable_ssl", "args": {"cert_path":"/certs/dvwa.silicom.com/dvwa.silicom.com.cert","key_path":"/certs/dvwa.silicom.com/dvwa.silicom.com.key","ca_dir":"/certs/dvwa.silicom.com/","cas_path":["/certs/dvwa.silicom.com/caroot.com.cert","/certs/dvwa.silicom.com/silicom.com.cert"]} },

def install_pip_server(instance, arg: dict, verbose: bool=True):
    """ Install and configure python repository with apache2.
    instance (object): This argmument define the lxc instance.
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                cert_path (str): Path to certficate file.
                key_path (str): Path to private key file.
                ca_dir (str): Directory path where private key and path are stored.
                cas_path (list): List of public key who signed the certificate.
            }
    verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.
    
    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    
    """
    if install_python_packages(instance, {"package":"virtualenv"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["mkdir","-p",arg["package_directory"]], "expected_exit_code":"0"}, verbose=False)

    execute_command(instance, {"command":["virtualenv", arg["package_directory"]+"venv"], "expected_exit_code":"0"}, verbose=False)
    if install_python_packages(instance, {"package":"pypiserver"}, verbose=False) == 1:
        return 1
    if install(instance, {"module":"apache2"}, verbose=False):
        return 1
    if install(instance, {"module":"libapache2-mod-wsgi-py3"}, verbose=False):
        return 1
    execute_command(instance, {"command":["a2enmod", "wsgi"], "expected_exit_code":"0"}, verbose=False)

    pypiserver_wsgi = open("simulation/workstations/"+instance.name+"/pypiserver.wsgi", "w")
    pypiserver_wsgi.write("import pypiserver \n")
    pypiserver_wsgi.write("PACKAGES = '"+arg["package_directory"]+"' \n")
    pypiserver_wsgi.write("application = pypiserver.app(root=PACKAGES, redirect_to_fallback=True) \n")
    pypiserver_wsgi.close()
    if upload_file(instance, {"instance_path":arg["package_directory"]+"pypiserver.wsgi", "host_manager_path":"simulation/workstations/"+instance.name+"/pypiserver.wsgi"}, verbose=False) == 1:
        return 1

    change_fileorfolder_user_owner(instance, {"new_owner":"www-data", "file_path":arg["package_directory"]}, verbose=False)
    change_fileorfolder_group_owner(instance, {"new_group":"www-data", "fileorfolder_path":arg["package_directory"]}, verbose=False)

    default_apache2_conf = open("simulation/workstations/"+instance.name+"/000-default.conf", "w")
    if arg["ssl"] == "true":
        default_apache2_conf.write("<VirtualHost *:443> \n")
        default_apache2_conf.write("<IfModule mod_ssl.c> \n")
        default_apache2_conf.write("    SSLEngine on\n")
        default_apache2_conf.write("    SSLCertificateFile      /etc/ssl/certs/ssl-cert-snakeoil.pem\n")
        default_apache2_conf.write("    SSLCertificateKeyFile   /etc/ssl/private/ssl-cert-snakeoil.key\n")
        default_apache2_conf.write("</IfModule> \n")
    else:
        default_apache2_conf.write("<VirtualHost *:80> \n")
    default_apache2_conf.write("     WSGIPassAuthorization On \n")
    default_apache2_conf.write("     WSGIScriptAlias / "+arg["package_directory"]+"pypiserver.wsgi \n")
    default_apache2_conf.write("     WSGIDaemonProcess pypiserver python-path="+arg["package_directory"]+":/root/venv/lib/python3.6/site-packages/ \n")
    default_apache2_conf.write("     <Directory "+arg["package_directory"]+"> \n")
    default_apache2_conf.write("         WSGIProcessGroup pypiserver \n")
    default_apache2_conf.write("         Require all granted \n")
    default_apache2_conf.write("     </Directory> \n")
    default_apache2_conf.write("     ErrorLog ${APACHE_LOG_DIR}/error.log \n")
    default_apache2_conf.write("     CustomLog ${APACHE_LOG_DIR}/access.log combined \n")
    default_apache2_conf.write("</VirtualHost> \n")
    default_apache2_conf.close()
    if upload_file(instance, {"instance_path":"/etc/apache2/sites-available/000-default.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/000-default.conf"}, verbose=False) == 1:
        return 1
    restart_service(instance, {"service":"apache2"}, verbose=False)
    result = execute_command(instance, {"command":["a2enmod", "ssl"], "expected_exit_code":"0"}, verbose=False)
    restart_service(instance, {"service":"apache2"}, verbose=False)

def upload_pip_lib(instance, arg: dict, verbose: bool=True):
    """ Upload and compress python project on pip repository.
    instance (object): This argmument define the lxc instance.
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                pip_libs (list): List all packages uploads on the repository stored in the host manager in folder path 'pip_lib/'
            }
    verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.
    
    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    
    """

    for pip_lib in arg["pip_libs"]:
        instance.execute(["mkdir", "/pypiserver/packages/"+pip_lib+"/"])
        instance.execute(["mkdir", "/pypiserver/packages/"+pip_lib+"/"+pip_lib+"/"])
        upload_file(instance, {"instance_path":"/pypiserver/packages/"+pip_lib+"/setup.py","host_manager_path":"pip_lib/"+pip_lib+"/setup.py"}, verbose=False)
        upload_file(instance, {"instance_path":"/pypiserver/packages/"+pip_lib+"/setup.cfg","host_manager_path":"pip_lib/"+pip_lib+"/setup.cfg"}, verbose=False)
        upload_file(instance, {"instance_path":"/pypiserver/packages/"+pip_lib+"/README.md","host_manager_path":"pip_lib/"+pip_lib+"/README.md"}, verbose=False)
        for file in os.listdir("pip_lib/"+pip_lib+"/"+pip_lib+"/"):
            upload_file(instance, {"instance_path":"/pypiserver/packages/"+pip_lib+"/"+pip_lib+"/"+file,"host_manager_path":"pip_lib/"+pip_lib+"/"+pip_lib+"/"+file}, verbose=False)
        create_execute_command_remote_bash(instance, {"script_name":"update_main_cf.sh", "commands":[
                                                                                                "cd /pypiserver/packages/"+pip_lib+" && python3 setup.py sdist"
                                                                                                # "cp /pypiserver/packages/"+pip_lib+"/dist/* /pypiserver/packages/"
                                                                                                    ], "delete":"false"}, verbose=False)

def install_chat_application(instance, verbose: bool=True):
    """ Install and configure chat web application 
    instance (object): This argmument define the lxc instance.
    verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.
    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    
    """
    if install(instance, {"module":"git"}, verbose=False):
        return 1
    if install(instance, {"module":"apache2"}, verbose=False):
        return 1
    if install(instance, {"module":"php"}, verbose=False):
        return 1
    if install(instance, {"module":"php-mysql"}, verbose=False):
        return 1
    if install(instance, {"module":"mysql-server"}, verbose=False):
        return 1

    execute_command(instance, {"command":["rm", "-R", "/var/www/html/"], "expected_exit_code":"0"}, verbose=False)
    git_clone(instance, {"branch":"main", "repository":"https://github.com/yogeeswar2001/chat-application.git", "instance_path":"/var/www/html/"}, verbose=False)

    execute_command(instance, {"command":["mysql", "-e", "create database chat_app;"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["mysql", "-e", "create user chatuser@localhost identified by 'chat123';"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["mysql", "-e", "grant all privileges on chat_app.* to chatuser@localhost;"], "expected_exit_code":"0"}, verbose=False)

    create_execute_command_remote_bash(instance, {"script_name":"chat_installation_file.sh", "commands":["sed -i -e \'s#username = \"root\"#username = \"chatuser\"#\' /var/www/html//db/db_conn.php \n",
                                                                                                         "sed -i -e \'s#pwd = \"yogeeswar\"#pwd = \"chat123\"#\' /var/www/html/db/db_conn.php \n",
                                                                                                         "sed -i -e \"s#username = \'root\'#username = \'chatuser\'#\" /var/www/html/db/db_conn_pdo.php \n",
                                                                                                         "sed -i -e \"s#pwd = \'yogeeswar\'#pwd = \'chat123\'#\" /var/www/html/db/db_conn_pdo.php \n",
                                                                                                         "sed -i -e \'s#COLLATE=utf8mb4_0900_ai_ci# #\' /var/www/html/db/chat_app.sql \n"
                                                                                                        ], "delete":"false"}, verbose=False)

    execute_command(instance, {"command":["mysql", "-e", "use chat_app; source /var/www/html/db/chat_app.sql;"], "expected_exit_code":"0"}, verbose=False)
    if restart_service(instance, {"service":"mysql"}, verbose=False):
        return 1
    if restart_service(instance, {"service":"apache2"}, verbose=False):
        return 1
    if verbose:
        print(Fore.GREEN + "      Chat application has been installed and configured successfully!" + Style.RESET_ALL)

def install_gnu_social_network(instance, arg: dict, verbose: bool=True):
    """ Install and configure gnu social web application 
    instance (object): This argmument define the lxc instance.
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                server_ip (str): Define the website public ip in the config file config.php.
                domain_name (str): Define the website domain name in the config file config.php.
            }
    verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.
    
    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    
    """
    install(instance, {"module":"curl"}, verbose=False)
    install(instance, {"module":"wget"}, verbose=False)
    install(instance, {"module":"git"}, verbose=False)
    install(instance, {"module":"apache2"}, verbose=False)
    install(instance, {"module":"mysql-server"}, verbose=False)
    install(instance, {"module":"php"}, verbose=False)
    install(instance, {"module":"php-curl"}, verbose=False)
    install(instance, {"module":"php-gd"}, verbose=False)
    install(instance, {"module":"php-gmp"}, verbose=False)
    install(instance, {"module":"php-intl"}, verbose=False)
    install(instance, {"module":"php-json"}, verbose=False)
    install(instance, {"module":"php-mysql"}, verbose=False)
    install(instance, {"module":"php-xml"}, verbose=False)
    install(instance, {"module":"php-simplexml"}, verbose=False)
    install(instance, {"module":"php-xmlwriter"}, verbose=False)
    install(instance, {"module":"php-dom"}, verbose=False)
    install(instance, {"module":"php-mbstring"}, verbose=False)

    execute_command(instance, {"command":["rm", "-R", "/var/www/html/"], "expected_exit_code":"0"}, verbose=False)
    # git_clone(instance, {"branch":"1.2.x", "repository":"https://notabug.org/diogo/gnu-social.git", "instance_path":"/var/www/html/"}, verbose=False)
    wget(instance, {"url":"https://notabug.org/diogo/gnu-social/archive/1.2.x.tar.gz", "local_path":"/var/www/"}, verbose=False)
    execute_command(instance, {"command":["tar", "-xf", "/var/www/1.2.x.tar.gz", "-C", "/var/www/"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["mv", "/var/www/gnu-social", "/var/www/html/"], "expected_exit_code":"0"}, verbose=False)

    change_fileorfolder_user_owner(instance, {"new_owner":"www-data", "file_path":"/var/www/html/"}, verbose=False)
    change_fileorfolder_group_owner(instance, {"new_group":"www-data", "fileorfolder_path":"/var/www/html/"}, verbose=False)
    change_permission(instance, {"owner":"7", "group":"5", "other":"5", "file_path":"/var/www/html/"}, verbose=False)

    create_execute_command_remote_bash(instance, {"script_name":"gnu_social_installation_file.sh", "commands":["echo 'sql_mode = ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' >> /etc/mysql/mysql.conf.d/mysqld.cnf"], "delete":"false"}, verbose=False)

    execute_command(instance, {"command":["mysql", "-e", "create database social_app;"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["mysql", "-e", "create user socialuser@localhost identified by 'social123';"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["mysql", "-e", "grant all privileges on social_app.* to socialuser@localhost;"], "expected_exit_code":"0"}, verbose=False)

    restart_service(instance, {"service":"apache2"}, verbose=False)
    restart_service(instance, {"service":"mysql"}, verbose=False)

    create_execute_command_remote_bash(instance, {"script_name":"gnu_social_configuration_file.sh", "commands":["curl -X POST -H 'Content-Type: application/x-www-form-urlencoded' -d 'sitename="+arg["domain_name"]+"' -d 'ssl=never' -d 'host=127.0.0.1' -d 'dbtype=mysql' -d 'database=social_app' -d 'dbusername=socialuser' -d 'dbpassword=social123' -d 'admin_nickname=admin' -d 'admin_password=admin123' -d 'admin_password2=admin123' -d 'admin_email=admin@yourdomain.com' -d 'site_profile=public' -d 'submit=Submit' http://127.0.0.1/install.php \n"], "delete":"false"}, verbose=False)
    config_php = open("simulation/workstations/"+instance.name+"/config.php", "w")
    config_php.write("<?php \n")
    config_php.write("if (!defined('GNUSOCIAL')) { exit(1); } \n")
    config_php.write("$config['site']['name'] = '"+arg["domain_name"]+"'; \n")
    config_php.write("$config['site']['path'] = ''; \n")
    config_php.write("$config['site']['server'] = '"+arg["server_ip"]+"'; \n")
    config_php.write("$config['site']['ssl'] = 'never'; \n")
    config_php.write("$config['db']['database'] = 'mysqli://socialuser:social123@127.0.0.1/social_app'; \n")
    config_php.write("$config['db']['type'] = 'mysql'; \n")
    config_php.write("$config['site']['profile'] = 'public'; \n")
    config_php.close()
    if upload_file(instance, {"instance_path":"/var/www/html/config.php", "host_manager_path":"simulation/workstations/"+instance.name+"/config.php"}, verbose=False) == 1:
        return 1

def install_food_delivery_application(instance, arg: dict, verbose: bool=True):
    """ Install and configure gnu social web application 
    instance (object): This argmument define the lxc instance.
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                server_ip (str): Define the website public ip in the config file config.php.
                port_server (str): Define the website domain name in the config file config.php.
                domain_name (str): 
            }
    verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.
    
    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    
    """
    install(instance, {"module":"python3-pip"}, verbose=False)
    git_clone(instance, {"branch":"master", "repository":"https://github.com/ChanduArepalli/Django-Online-Food-Delivery.git", "instance_path":"/root/delivery"}, verbose=False)
    execute_command(instance, {"command":["sed", "-i", "6iimport six", "/root/delivery/manage.py"], "expected_exit_code":"0"}, verbose=False)
    requirement = open("simulation/workstations/"+instance.name+"/requirements.txt", "w")
    requirement.write("Django\ndjango-crispy-forms\ndjango-currentuser\ndjango-extensions\nPillow\npytz\nsix\nsqlparse\n")
    requirement.close()
    if upload_file(instance, {"instance_path":"/root/delivery/requirements.txt", "host_manager_path":"simulation/workstations/"+instance.name+"/requirements.txt"}, verbose=False) == 1:
        return 1

    install_python_packages(instance, {"package":"/root/delivery/requirements.txt"}, verbose=False)
    create_execute_command_remote_bash(instance, {"script_name":"food_delivery.sh", "commands":[
                                                                                                   "sed -i -e \'s|ALLOWED_HOSTS = \[\]|ALLOWED_HOSTS = \[\"*\"\]|\' /root/delivery/Online_Food_Delivery/settings.py",
                                                                                                ], "delete":"false"}, verbose=False)
    clear_nameserver(instance, verbose=False)

    service = open("simulation/workstations/"+instance.name+"/delivery_food.service", "w")
    service.write("[Unit]\n")
    service.write("Description=Delivery food service\n")
    service.write("[Service]\n")
    service.write("Type=simple\n")
    service.write("ExecStart=/usr/bin/python3 /root/delivery/manage.py runserver "+arg["ip_server"]+":"+arg["port_server"]+"\n")
    service.write("[Install]\n")
    service.write("WantedBy=multi-user.target\n")
    service.close()
    if upload_file(instance, {"instance_path":"/lib/systemd/system/delivery_food.service", "host_manager_path":"simulation/workstations/"+instance.name+"/delivery_food.service"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["systemctl", "daemon-reload"], "expected_exit_code":"0"}, verbose=False)
    if restart_service(instance, {"service":"delivery_food"}, verbose=False):
        return 1

# {"name":"install_gnu_social_network", "args": {"username":"user1","password":"user123"} },
# {"name":"enable_ssl", "args": {"cert_path":"/certs/dvwa.silicom.com/dvwa.silicom.com.cert","key_path":"/certs/dvwa.silicom.com/dvwa.silicom.com.key","ca_dir":"/certs/dvwa.silicom.com/","cas_path":["/certs/dvwa.silicom.com/caroot.com.cert","/certs/dvwa.silicom.com/silicom.com.cert"]} },

#{"name":"enable_ssl", "args": {"cert_path":"/certs/pypi.org/pypi.org.cert","key_path":"/certs/pypi.org/pypi.org.key","ca_dir":"/certs/pypi.org/","cas_path":["/certs/pypi.org/caroot.com.cert","/certs/pypi.org/mediacorp.com.cert"]} },
