#!/bin/bash
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add - 
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-7.x.list 
apt-get update 
apt-get install -y elasticsearch 
systemctl enable elasticsearch 
systemctl start elasticsearch 
apt-get install -y nginx 
apt-get install -y kibana 
systemctl start kibana
echo "kadmin:`openssl passwd kadmin123`" | sudo tee -a /etc/nginx/htpasswd.users
ln -s /etc/nginx/sites-available/elk.boulangerie.local /etc/nginx/sites-enabled/elk.boulangerie.local
systemctl reload nginx
ufw allow 'Nginx Full'
systemctl restart kibana
apt-get install -y logstash
