#!/bin/bash 
ldapadd -x -w $(cat /root/.env/LDAP_PASSWORD) -D cn=admin,dc=boulangerie,dc=local -f /etc/ldap/schema/tgourmelen.ldif 
ldappasswd -s tgourmelen123 -w $(cat /root/.env/LDAP_PASSWORD) -D "cn=admin,dc=boulangerie,dc=local" -x uid=tgourmelen,dc=boulangerie,dc=local 
