#!/bin/bash

echo '--- Updating system ---'
apt update && apt upgrade -y

echo '--- Installing Measurement Dependencies ---'
apt-get -y install speedtest-cli net-tools iperf3 chromium-chromedriver nmap traceroute
apt-get -y install  dnsutils

echo '--- Installing pip3 ---'
apt-get -y install python3-pip

echo '--- Installing virtualenv ---'
python3 -m pip install --user virtualenv
apt-get -y install  python3-venv


