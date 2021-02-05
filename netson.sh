#!/bin/bash

crontab -r
crontab -l


crontab -l | { cat; echo "0-14,18-44,48-59 * * * * python3 ~/netrics/src/netson -p -d -t -b -u "; } | crontab -

crontab -l | { cat; echo "0-14,18-44,48-59 * * * * python3 ~/netrics/src/netson -n -u "; } | crontab -
crontab -l | { cat; echo "0 * * * * python3 ~/netrics/src/netson -s -u "; } | crontab -

crontab -l | { cat; echo "30 * * * * python3 ~/netrics/src/netson -i tigerteam.io 33001 -u"; } | crontab -

