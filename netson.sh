#!/bin/bash

echo '--- Installing netson python dependencies ---'
pip3 install Cython
pip3 install numpy
pip3 install pandas -v
pip3 install speedtest-cli
pip3 install selenium
pip3 install influxdb_client
pip3 install influxdb

echo '--- Setting up automatic measurements ---'
crontab -l > mycron

echo "3-29,33-59  *   *   *   *     source ~/env/netson/bin/activate; python3 ~/netrics/src/netson -p -d -t -b -n -u tigerteam.io 9999 netrics $1" >> mycron

echo "0  */2   *   *   *     source ~/env/netson/bin/activate; python3 ~/netrics/src/netson -s -u tigerteam.io 9999 netrics $1" >> mycron

echo "30  */2   *   *   *     source ~/env/netson/bin/activate; python3 ~/netrics/src/netson -i tigerteam.io 33001 -u tigerteam.io 9999 netrics $1" >> mycron

crontab mycron
rm mycron


