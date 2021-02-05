#!/bin/bash

crontab -r
crontab -l


crontab -l | { cat; echo "*/5 * * * * python3 ~/netrics/src/netson -p -n -d -t -b -u "; } | crontab -

crontab -l | { cat; echo "1 * * * * python3 ~/netrics/src/netson -s -u "; } | crontab -

crontab -l | { cat; echo "6 * * * * python3 ~/netrics/src/netson -i tigerteam.io 33001 -u"; } | crontab -

