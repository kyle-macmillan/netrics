#!/bin/bash

wget https://people.cs.uchicago.edu/~macmillan/netrics.json

deployment=$(echo -n ${1} | md5sum | awk '{print $1}')

iperf_time=$(jq '.[][] | select(.deployment == "'$deployment'").times.iperf3' netrics.json)

crontab -r
crontab -l

crontab -l | { cat; echo "*/5 * * * * python3 ~/netrics/src/netson -p -n -d -t -b -u "; } | crontab -

crontab -l | { cat; echo "1 * * * * python3 ~/netrics/src/netson -s -u "; } | crontab -

crontab -l | { cat; echo "$iperf_time * * * * python3 ~/netrics/src/netson -i tigerteam.io 33001 -u"; } | crontab -

