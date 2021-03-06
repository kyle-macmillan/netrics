#!/bin/bash

echo '--- Updating system ---'
apt update -q && apt upgrade -q -y

echo '\n\n--- Installing Measurement Dependencies ---'
apt-get -q -y install speedtest-cli net-tools chromium-chromedriver nmap traceroute jq
apt-get -q -y install  dnsutils
wget https://downloads.es.net/pub/iperf/iperf-3.9.tar.gz
tar -xvf iperf-3.9.tar.gz
cd iperf-3.9
./configure
make
make install

apt -y remove libiperf0

echo '\n\n--- Installing pip3 ---'
apt-get -q -y install python3-pip

echo '\n\n--- Installing python dependecies ---'
pip3 install speedtest-cli
pip3 install selenium
pip3 install influxdb_client
pip3 install influxdb
pip3 install tinydb

