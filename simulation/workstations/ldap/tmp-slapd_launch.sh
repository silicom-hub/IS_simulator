#!/bin/bash
echo "slapd slapd/no_configuration boolean false" | debconf-set-selections
echo "slapd slapd/domain string boulangerie.local" | debconf-set-selections
echo "slapd shared/organization string 'boulangerie'" | debconf-set-selections
echo "slapd slapd/password1 password my_password" | debconf-set-selections
echo "slapd slapd/password2 password my_password" | debconf-set-selections
echo "slapd slapd/backend select HDB" | debconf-set-selections
echo "slapd slapd/purge_database boolean true" | debconf-set-selections
echo "slapd slapd/allow_ldap_v2 boolean false" | debconf-set-selections
echo "slapd slapd/move_old_database boolean true" | debconf-set-selections
DEBIAN_FRONTEND=noninteractive apt-get install -y -q slapd
DEBIAN_FRONTEND=noninteractive apt-get install -y -q ldap-utils
echo 'my_password' > /root/.env/LDAP_PASSWORD 
