""" This file contains function how configure ELK stack """
from colorama import Fore, Style
from .logic_actions_utils import save_nameserver_ip, clear_nameserver, add_nameserver, execute_command, upload_file, install, delete_file, restart_service, wget, create_execute_command_remote_bash, install_python_packages

def install_elk(instance, arg, verbose=True):
    """ Install ELK stack ans configure logstash to receive logs from simulation
        Args:
            instance (object): This argmument define the lxc instance.
            arg (dict of str: Optional): This argument list maps arguments and their value.
                {
                    logstash (str): This value is a boolean who indicates if the service will be installed.
                    elasticsearch (str): This value is a boolean who indicates if the service will be installed.
                    kibana (str): This value is a boolean who indicates if the service will be installed.
                    fqdn_host (str): This value represents the fully qualified domain name.
                    ip_fqdn (str): This value represents the fully qualified domain name's ip.
                    admin_name (str): This value is the kibana service's admin name.
                    admin_passwd (str): This value is the kibana service's admin password.
                }
            verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.

        Returns:
            int: Return 1 if the function works successfully, otherwise 0.
    """
    install(instance, {"module":"curl"}, verbose=False)
    install(instance, {"module":"gnupg"}, verbose=False)

    nameserver_ips = save_nameserver_ip(instance)
    clear_nameserver(instance, verbose=False)
    add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)

    elk_installation = open("simulation/workstations/"+instance.name+"/elk-launch.sh", "w")
    elk_installation.write("#!/bin/bash\n")
    elk_installation.write("curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add - \n")
    elk_installation.write("echo \"deb https://artifacts.elastic.co/packages/7.x/apt stable main\" | tee -a /etc/apt/sources.list.d/elastic-7.x.list \n")
    elk_installation.write("apt-get -y update \n")
#############################################
#### Install and configure elasticsearch ####
#############################################
    if arg["elasticsearch"] == "true":
        elk_installation.write("apt-get install -y elasticsearch=7.17.2 \n")
        elk_installation.write("systemctl enable elasticsearch \n")
        elk_installation.write("systemctl start elasticsearch \n")
        

######################################
#### Install and configure kibana ####
######################################
    if arg["kibana"] == "true":
        elk_installation.write("apt-get install -y nginx \n")
        elk_installation.write("apt-get install -y kibana=7.17.3 \n")
        elk_installation.write("systemctl start kibana\n")
        elk_installation.write("echo \""+arg["admin_name"]+":`openssl passwd "+arg["admin_passwd"]+"`\" | sudo tee -a /etc/nginx/htpasswd.users\n")
        elk_installation.write("ln -s /etc/nginx/sites-available/"+arg["fqdn_host"]+" /etc/nginx/sites-enabled/"+arg["fqdn_host"]+"\n")
        elk_installation.write("systemctl reload nginx\n")
        elk_installation.write("ufw allow 'Nginx Full'\n")
        elk_installation.write("systemctl restart kibana\n")

########################################
#### Install and configure logstash ####
########################################
    if arg["logstash"] == "true":
        elk_installation.write("apt-get install -y logstash\n")
        ### Add custom grok pattern
        elk_installation.write("echo \"ETHTYPE (?:(?:[A-Fa-f0-9]{2}):(?:[A-Fa-f0-9]{2}))\" >> /etc/logstash/iptables.grok\n")

    elk_installation.close()
    if upload_file(instance, {"instance_path":"/root/elk-launch.sh", "host_manager_path":"simulation/workstations/"+instance.name+"/elk-launch.sh"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["chmod", "+x", "/root/elk-launch.sh"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["./elk-launch.sh"], "expected_exit_code":"0"}, verbose=False)
    if delete_file(instance, {"instance_path":"/root/elk-launch.sh"}, verbose=False) == 1:
        return 1

#########################
#### Configure Nginx ####
#########################
    if arg["kibana"] == "true":
        nginx_conf = open("simulation/workstations/"+instance.name+"/"+arg["fqdn_host"], "w")
        nginx_conf.write("server {\n")
        nginx_conf.write("  listen 80;\n")
        nginx_conf.write("  server_name "+arg["ip_fqdn"]+";\n")
        nginx_conf.write("  auth_basic 'Restricted Access';\n")
        nginx_conf.write("  auth_basic_user_file /etc/nginx/htpasswd.users;\n")
        nginx_conf.write("  location / {\n")
        nginx_conf.write("      proxy_pass http://localhost:5601;\n")
        nginx_conf.write("      proxy_http_version 1.1;\n")
        nginx_conf.write("      proxy_set_header Upgrade $http_upgrade;\n")
        nginx_conf.write("      proxy_set_header Connection 'upgrade';\n")
        nginx_conf.write("      proxy_set_header Host $host;\n")
        nginx_conf.write("      proxy_cache_bypass $http_upgrade;\n")
        nginx_conf.write("  }\n")
        nginx_conf.write("}\n")
        nginx_conf.close()
        if upload_file(instance, {"instance_path":"/etc/nginx/sites-available/"+arg["fqdn_host"], "host_manager_path":"simulation/workstations/"+instance.name+"/"+arg["fqdn_host"]}, verbose=False) == 1:
            return 1
        # instance.files.put("/etc/nginx/sites-available/"+arg["fqdn_host"], open("simulation/workstations/"+instance.name+"/"+arg["fqdn_host"]).read())
        if restart_service(instance, {"service":"nginx"}, verbose=False) == 1:
            return 1
        execute_command(instance, {"command":["systemctl", "stop", "nginx"], "expected_exit_code":"0"}, verbose=False)

#######################
#### Configure JVM ####
#######################
    create_execute_command_remote_bash(instance, {"script_name":"jvm.sh", "commands":["sed -i -e 's/## -Xms4g/-Xms12g/' /etc/elasticsearch/jvm.options",
                                                                                      "sed -i -e 's/## -Xmx4g/-Xmx12g/' /etc/elasticsearch/jvm.options"
                                                                                     ], "delete":"false"}, verbose=False)

############################
#### Configure Logstash ####
############################
    if arg["logstash"] == "true":
        logstash_conf = open("simulation/workstations/"+instance.name+"/logstash_input.conf", "w")

        ##### INPUT
        logstash_conf.write("input {\n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5001\n")
        logstash_conf.write("    type => authentication\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5002\n")
        logstash_conf.write("    type => mail\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5003\n")
        logstash_conf.write("    type => apache2_access\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5004\n")
        logstash_conf.write("    type => apache2_error\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5005\n")
        logstash_conf.write("    type => iptables\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5006\n")
        logstash_conf.write("    type => squid\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5007\n")
        logstash_conf.write("    type => snort\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5008\n")
        logstash_conf.write("    type => suricata\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5009\n")
        logstash_conf.write("    type => ldap\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5010\n")
        logstash_conf.write("    type => samba\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5011\n")
        logstash_conf.write("    type => motion\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5012\n")
        logstash_conf.write("    type => hacker\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("} \n")

        ##### FILTER
        logstash_conf.write("filter {\n")
        ### INITIAL_ACCESS
        logstash_conf.write("  if [type] == \"hacker\" {\n")
        logstash_conf.write("    json  {\n")
        logstash_conf.write("      source => \"message\"\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("  }\n")
        ### APACHE ACCESS
        logstash_conf.write("  if [type] == \"apache2_access\" {\n")
        logstash_conf.write("    grok  {\n")
        logstash_conf.write("      match => {\"message\" => \"%{COMBINEDAPACHELOG}\"}\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("  }\n")
        ### IPTABLES
        logstash_conf.write("  if [type] == \"iptables\" {\n")
        logstash_conf.write("    grok  {\n")
        logstash_conf.write("      patterns_dir => \"/etc/logstash/iptables.grok\"\n")
        logstash_conf.write("      match => {\"message\" => \".*IN=(%{USERNAME:in_interface})?.*OUT=(%{USERNAME:out_interface})?.*MAC=(%{COMMONMAC:mac_destination}):(%{COMMONMAC:mac_source}):(%{ETHTYPE}).*SRC=(%{IP:ip_source}).*DST=(%{IP:ip_destination}).*TTL=(%{NUMBER:ttl}).*PROTO=(%{WORD:protocole}).*SPT=(%{NUMBER:source_port}).*DPT=(%{NUMBER:destination_port}).*SEQ=(%{NUMBER:sequence})\"}\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("  } \n")
        ### SMB
        smb_grok = open("simulation/workstations/"+instance.name+"/smb.grok", "w")
        smb_grok.write("SMB_AUTHENTICATION samba.*%{DATA:workstation_name} \(%{DATA:protocol}:%{IP:client_ip}:%{NUMBER:client_port}\) %{WORD:state}.*user %{USER:username} \(uid=%{NUMBER:uid}, gid=%{NUMBER:gid}\) \(pid %{NUMBER:pid}\)\n")
        smb_grok.write("SMB_CLOSE samba %{DATA:workstation_name} \(%{DATA:protocol}:%{IP:client_ip}:%{NUMBER:port_client}\) %{WORD:state}\n")
        smb_grok.write("SMB_FILE_ACCESS samba %{WORD:username} %{WORD:state} file %{DATA:file} read=%{WORD:read} write=%{WORD:write} \(numopen=%{NUMBER:numopen}\)\n")
        smb_grok.write("SMB_FILE_CLOSE samba %{DATA:username} %{DATA:action} %{WORD:file} \(numopen=%{NUMBER:numopen}\)\n")
        smb_grok.write("SMB_NTLM_PASSWORD check_ntlm_password:.*%{WORD:action} for user \[%{WORD:username}\] -> \[%{WORD}\] -> \[%{WORD}\] %{WORD:state}\n")
        smb_grok.close()
        if upload_file(instance, {"instance_path":"/etc/logstash/smb.grok", "host_manager_path":"simulation/workstations/"+instance.name+"/smb.grok"}, verbose=False) == 1:
            return 1
        logstash_conf.write("  if [type] == \"samba\" {\n")
        logstash_conf.write("    grok  {\n")
        logstash_conf.write("      patterns_dir => \"/etc/logstash/smb.grok\"\n")
        logstash_conf.write("      match => {\"message\" => \"%{SMB_AUTHENTICATION}|%{SMB_CLOSE}%{SMB_FILE_ACCESS}|%{SMB_FILE_CLOSE}|%{SMB_NTLM_PASSWORD}\"}\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("  } \n")
        ### LDAP
        logstash_conf.write("  if [type] == \"ldap\" {\n")
        logstash_conf.write("    grok  {\n")
        logstash_conf.write("      match => {\"message\" => \".*conn=%{NUMBER:connection} ((op=%{NUMBER:op})|(fd=%{NUMBER:fd})) %{WORD:operation}(%{GREEDYDATA:data})?\"}\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("    if [operation] == \"RESULT\" or [operation] == \"SEARCH\"{\n")
        logstash_conf.write("      grok  {\n")
        logstash_conf.write("        match => {\"data\" => \".*tag=(%{NUMBER:result_tag})?.*err=(%{NUMBER:result_error})(?:(?: nentries=%{NUMBER:result_entries})|(?:)).*text=(%{GREEDYDATA:result_text})?\"}\n")
        logstash_conf.write("      }\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("    if [operation] == \"ACCEPT\" {\n")
        logstash_conf.write("      grok  {\n")
        logstash_conf.write("        match => {\"data\" => \".*IP=%{IP:accept_ip_client}:%{NUMBER:accept_port_client} \(IP=%{IP:accept_ip_server}:%{NUMBER:accept_port_server}\)\" }\n")
        logstash_conf.write("      }\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("    if [operation] == \"BIND\" {\n")
        logstash_conf.write("      grok  {\n")
        logstash_conf.write("        match => {\"data\" => \".*((dn=%{QUOTEDSTRING:bind_dn})|(%{WORD:bind_dn})) ((method=%{NUMBER:bind_method})|(mech=%{WORD:bind_mech}(?:(?: sasl_ssf=%{NUMBER:bind_sasl_ssf})|(?:)).*ssf=%{NUMBER:bind_ssf}))\" }\n")
        logstash_conf.write("      }\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("    if [operation] == \"MOD\" {\n")
        logstash_conf.write("      grok  {\n")
        logstash_conf.write("        match => {\"data\" => \"(?:(?:dn=%{QUOTEDSTRING:mod_dn})|(?:attr=%{WORD:mod_attr}))\" }\n")
        logstash_conf.write("      }\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("    if [operation] == \"SRCH\" {\n")
        logstash_conf.write("      grok  {\n")
        logstash_conf.write("        match => {\"data\" => \"(?:(?:base=%{QUOTEDSTRING:srch_base} scope=%{NUMBER:srch_scope} deref=%{NUMBER:srch_deref} filter=%{QUOTEDSTRING:srch_filter})|(?:attr=%{WORD:srch_attr}))\" }\n")
        logstash_conf.write("      }\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("    mutate  {\n")
        logstash_conf.write("      remove_field => [\"data\"]\n")
        logstash_conf.write("    } \n")
        logstash_conf.write("  } \n")
        ### MAIL
        wget(instance, {"url":"https://raw.githubusercontent.com/matejzero/logstash-grok-patterns/master/dovecot.grok", "local_path":"/etc/logstash/"}, verbose=False)
        wget(instance, {"url":"https://raw.githubusercontent.com/padusumilli/postfix-grok/master/postfix-grok-patterns", "local_path":"/etc/logstash/"}, verbose=False)
           ### path grok mail
        create_execute_command_remote_bash(instance, {"script_name":"mail_patch.sh", "commands":["sed -i -e 's#%{IP:relayip}#((%{IP:relayip})|(%{DATA}))#' /etc/logstash/postfix-grok-patterns",
                                                                                            #    "sed -i '/DOVECOT_LMTP/d' /etc/logstash/dovecot.grok",
                                                                                            #    "sed -i '77 a DOVECOT_LMTP %{WORD:proto}\(%{USERNAME:user}|%{NUMBER\): (%{WORD:session}: )?(msgid=<%{DATA:msgid}>: )?%{GREEDYDATA:status_message}' /etc/logstash/dovecot.grok",
                                                                                               "cat /etc/logstash/dovecot.grok /etc/logstash/postfix-grok-patterns >> /etc/logstash/mail.grok"
                                                                                          ], "delete":"false"}, verbose=False)
        logstash_conf.write("  if [type] == \"mail\" {\n")
        logstash_conf.write("    grok  {\n")
        logstash_conf.write("     patterns_dir => \"/etc/logstash/mail.grok\"\n")
        logstash_conf.write("      match => {\"message\" => \"%{DOVECOT}|%{PF}\"}\n")
        logstash_conf.write("    }\n")
        logstash_conf.write("  }\n")

        logstash_conf.write("  mutate  {\n")
        logstash_conf.write("    remove_field => [\"message\"]\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("} \n")
        logstash_conf.write("output {\n")
        logstash_conf.write("  stdout { codec => rubydebug }\n")
        logstash_conf.write("  file { \n")
        logstash_conf.write("    codec => \"json\"\n")
        logstash_conf.write("    path => \"/var/log/logstash/%{type}-%{host}.json\"\n")
        logstash_conf.write("  }\n")
        if arg["elasticsearch"] == "true":
            logstash_conf.write("  elasticsearch {\n")
            logstash_conf.write("    hosts => [\"localhost:9200\"]\n")
            logstash_conf.write("    index => \"%{type}-%{host}\"\n")
            logstash_conf.write("  }\n")
        logstash_conf.write("}\n")
        logstash_conf.close()

        if upload_file(instance, {"instance_path":"/etc/logstash/conf.d/logstash_input.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/logstash_input.conf"}, verbose=False) == 1:
            return 1
        execute_command(instance, {"command":["chmod", "-R", "777", "/etc/logstash/"], "expected_exit_code":"0"}, verbose=False)
        if restart_service(instance, {"service":"logstash"}, verbose=False) == 1:
            return 1

        if arg["logstash"] == "true":
            result = instance.execute(["systemctl", "status", "logstash"])
            if "(running)" in result.stdout:
                if verbose:
                    print(Fore.GREEN+ "      Logstash is running!"+Style.RESET_ALL)
                result = instance.execute(["cat", "/var/log/logstash/sisimulator.json"]).stdout
                if result:
                    if verbose:
                        print(Fore.GREEN+ "      Logstash configuration is applied!"+Style.RESET_ALL)
                    print(Fore.RED+ "      Logstash configuration is not applied!"+Style.RESET_ALL)
                print(Fore.RED+ "      Logstash is not running!"+Style.RESET_ALL)

    if arg["elasticsearch"] == "true":
        result = instance.execute(["systemctl", "status", "elasticsearch"]).stdout
        if "(running)" in result:
            print(Fore.GREEN+ "      Elasticsearch is running!"+Style.RESET_ALL)
        else:
            print(Fore.RED+ "      Elasticsearch is not running!"+Style.RESET_ALL)

    if arg["kibana"] == "true":
        result = instance.execute(["systemctl", "status", "kibana"]).stdout
        if "(running)" in result:
            print(Fore.GREEN+ "      Kibana is running!"+Style.RESET_ALL)
        else:
            print(Fore.RED+ "      Kibana is not running!"+Style.RESET_ALL)
        result = instance.execute(["systemctl", "status", "nginx"]).stdout
        if "(running)" in result:
            print(Fore.GREEN+ "      Nginx is running!"+Style.RESET_ALL)
        else:
            print(Fore.RED+ "      Nginx is not running!"+Style.RESET_ALL)

        instance.files.recursive_put("elk_gui_conf/", "/etc/kibana/elk_gui_conf/")
        if install_python_packages(instance, {"package":"requests"}, verbose=False) == 1:
            return 1

    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)
    print(Fore.GREEN+ "      ELK stack have been installed and configured successfully!"+Style.RESET_ALL)
    return 0
# {"name":"install_elk", "args": {"fqdn_host":"elk.boulngerie.local","ip_fqdn":"10.122.115.11","admin_name":"kadmin","admin_passwd":"kadmin"} }
