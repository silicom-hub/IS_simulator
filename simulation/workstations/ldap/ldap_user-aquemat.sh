#!/bin/bash 
ldapadd -x -w $(cat /root/.env/LDAP_PASSWORD) -D cn=admin,dc=boulangerie,dc=local -f /etc/ldap/schema/aquemat.ldif 
ldappasswd -s aquemat123 -w $(cat /root/.env/LDAP_PASSWORD) -D "cn=admin,dc=boulangerie,dc=local" -x uid=aquemat,dc=boulangerie,dc=local 
