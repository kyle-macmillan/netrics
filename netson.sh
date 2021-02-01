#!/bin/bash

crontab -r
crontab -l


crontab -l | { cat; echo "0-14,18-44,48-59 * * * * python3 ~/netrics/src/netson -p -d -t -b -n -u "; } | crontab -

crontab -l | { cat; echo "15 */2 * * * python3 ~/netrics/src/netson -s -u "; } | crontab -

