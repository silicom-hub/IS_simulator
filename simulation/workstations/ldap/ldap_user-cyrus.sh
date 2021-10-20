#!/bin/bash 
ldapadd -x -w $(cat /root/.env/LDAP_PASSWORD) -D cn=admin,dc=boulangerie,dc=local -f /etc/ldap/schema/cyrus.ldif 
ldappasswd -s cyrus123 -w $(cat /root/.env/LDAP_PASSWORD) -D "cn=admin,dc=boulangerie,dc=local" -x uid=cyrus,dc=boulangerie,dc=local 
