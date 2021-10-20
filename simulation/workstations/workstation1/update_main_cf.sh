#!/bin/bash 
echo 'cyrus   unix    -       n       n       -       -       pipe
  flags=R user=cyrus argv=/usr/sbin/cyrdeliver -e -m
  ${extension} ${user}' >> /etc/postfix/master.cf 
