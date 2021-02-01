#!/bin/bash

echo '--- Updating system ---'
apt update -q && apt upgrade -q -y

echo '\n\n--- Installing Measurement Dependencies ---'
apt-get -q -y install speedtest-cli net-tools iperf3 chromium-chromedriver nmap traceroute
apt-get -q -y install  dnsutils

echo '\n\n--- Installing pip3 ---'
apt-get -q -y install python3-pip

echo '\n\n--- Installing python dependecies ---'
pip3 install speedtest-cli
pip3 install selenium
pip3 install influxdb_client
pip3 install influxdb

echo '\n\n --- Adding permissions ---'
chmod a+rwx seen_devices.csv

echo '\n\n--- Automating Measurements ---'

crontab -l > mycron

echo "0-14, 18-44, 48-59  *   *   *   *  python3 ~/netrics/src/netson -p -d -t -b -n -u " >> mycron

echo "15 */2 * * *  python3 ~/netrics/src/netson -s -u" >> mycron

crontab mycron
rm mycron

