from colorama import Fore, Style
from .logic_actions_utils import install, upload_file, delete_file, restart_service

def install_elk(client, instance, arg):
    elk_installation = open("simulation/workstations/"+instance.name+"/elk-launch.sh", "w")
    elk_installation.write("#!/bin/bash\n")
    elk_installation.write("curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add - \n")
    elk_installation.write("echo \"deb https://artifacts.elastic.co/packages/7.x/apt stable main\" | tee -a /etc/apt/sources.list.d/elastic-7.x.list \n")
    elk_installation.write("apt-get update \n")
#############################################
#### Install and configure elasticsearch ####
#############################################
    if arg["elasticsearch"] == "true":
        elk_installation.write("apt-get install -y elasticsearch \n")
        # elk_installation.write("sed -i -e \'s#network.host: 192.168.0.1#network.host: localhost#\' /etc/elasticsearch/elasticsearch.yml \n")
        elk_installation.write("systemctl enable elasticsearch \n")
        elk_installation.write("systemctl start elasticsearch \n")
        instance.execute(["systemctl","status","elasticsearch"]).stdout
    
######################################
#### Install and configure kibana ####
######################################
    if arg["kibana"] == "true":
        elk_installation.write("apt-get install -y nginx \n")
        elk_installation.write("apt-get install -y kibana \n")
        elk_installation.write("systemctl start kibana\n")
        elk_installation.write("echo \""+arg["admin_name"]+":`openssl passwd "+arg["admin_passwd"]+"`\" | sudo tee -a /etc/nginx/htpasswd.users\n")
        elk_installation.write("ln -s /etc/nginx/sites-available/"+arg["fqdn_host"]+" /etc/nginx/sites-enabled/"+arg["fqdn_host"]+"\n")
        elk_installation.write("systemctl reload nginx\n")
        elk_installation.write("ufw allow 'Nginx Full'\n")
        elk_installation.write("systemctl restart kibana\n")

    if arg["logstash"] == "true":
        elk_installation.write("apt-get install -y logstash\n")
        elk_installation.close()

    upload_file(client,instance,{"instance_path":"/root/elk-launch.sh","host_manager_path":"simulation/workstations/"+instance.name+"/elk-launch.sh"}, verbose=False)
    # instance.files.put("/root/elk-launch.sh", open("simulation/workstations/"+instance.name+"/elk-launch.sh").read())
    instance.execute(["chmod", "+x", "/root/elk-launch.sh"])
    instance.execute(["./elk-launch.sh"])
    delete_file(client,instance,{"instance_path":"/root/elk-launch.sh"}, verbose=False)

#########################
#### Configure Nginx ####
#########################
    if arg["kibana"] == "true":
        nginx_conf = open("simulation/workstations/"+instance.name+"/"+arg["fqdn_host"],"w")
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
        upload_file(client,instance,{"instance_path":"/etc/nginx/sites-available/"+arg["fqdn_host"],"host_manager_path":"simulation/workstations/"+instance.name+"/"+arg["fqdn_host"]}, verbose=False)
        # instance.files.put("/etc/nginx/sites-available/"+arg["fqdn_host"], open("simulation/workstations/"+instance.name+"/"+arg["fqdn_host"]).read())
        restart_service(client,instance,{"service":"nginx"})

############################
#### Configure Logstash ####
############################
    if arg["logstash"] == "true":
        logstash_conf = open("simulation/workstations/"+instance.name+"/logstash_input.conf","w")
        logstash_conf.write("input {\n")
        logstash_conf.write("  udp { \n")
        logstash_conf.write("    port => 5001\n")
        logstash_conf.write("  } \n")
        logstash_conf.write("} \n")
        logstash_conf.write("filter {\n")
        logstash_conf.write("} \n")
        logstash_conf.write("output {\n")
        logstash_conf.write("  stdout { codec => rubydebug }\n")
        logstash_conf.write("  file { \n")
        logstash_conf.write("    codec => \"json\"\n")
        logstash_conf.write("    path => \"/var/log/logstash/sisimulator.json\"\n")
        logstash_conf.write("  }\n")
        if arg["elasticsearch"] == "true":
            logstash_conf.write("  elasticsearch {\n")
            logstash_conf.write("    hosts => [\"localhost:9200\"]\n")
            logstash_conf.write("    index => \"si_simulator\"\n")
            logstash_conf.write("  }\n")
        logstash_conf.write("}\n")
        logstash_conf.close()
        upload_file(client,instance,{"instance_path":"/etc/logstash/conf.d/logstash_input.conf","host_manager_path":"simulation/workstations/"+instance.name+"/logstash_input.conf"})
        instance.execute(["chmod","-R","777","/etc/logstash/"])
        restart_service(client,instance,{"service":"logstash"},verbose=False)

        if arg["logstash"] == "true":
            result = instance.execute(["systemctl","status","logstash"])
            if "(running)" in result.stdout:
                print( Fore.GREEN+ "      Logstash is running!"+Style.RESET_ALL )
                result = instance.execute(["cat","/var/log/logstash/sisimulator.json"]).stdout
                if result:
                    print( Fore.GREEN+ "      Logstash configuration is applied!"+Style.RESET_ALL )
                else:
                    print( Fore.RED+ "      Logstash configuration is not applied!"+Style.RESET_ALL )
            else:
                print( Fore.RED+ "      Logstash is not running!"+Style.RESET_ALL )

        if arg["elasticsearch"] == "true":
            result = instance.execute(["systemctl","status","elasticsearch"]).stdout
            if "(running)" in result:
                print( Fore.GREEN+ "      Elasticsearch is running!"+Style.RESET_ALL )
            else:
                print( Fore.RED+ "      Elasticsearch is not running!"+Style.RESET_ALL )

        if arg["kibana"] == "true":
            result = instance.execute(["systemctl","status","kibana"]).stdout
            if "(running)" in result:
                print( Fore.GREEN+ "      Kibana is running!"+Style.RESET_ALL )
            else:
                print( Fore.RED+ "      Kibana is not running!"+Style.RESET_ALL )
            result = instance.execute(["systemctl","status","nginx"]).stdout
            if "(running)" in result:
                print( Fore.GREEN+ "      Nginx is running!"+Style.RESET_ALL )
            else:
                print( Fore.RED+ "      Nginx is not running!"+Style.RESET_ALL )

        
# {"name":"install_elk", "args": {"fqdn_host":"elk.boulngerie.local","ip_fqdn":"10.122.115.11","admin_name":"kadmin","admin_passwd":"kadmin"} }
