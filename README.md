## Simple Active Measurements on Router-Connected HW

To run these tests, please:
* check out this repository
  ```
  git@github.com:JamesSaxon/netrics.git
  ```
* consult the requirements file, and make sure these are installed.
  You may also need a variety of tools.  This worked for me
  ```
  sudo apt install speedtest-cli net-tools iperf3 chromium-chromedriver nmap traceroute 
  pip3 install pandas speedtest-cli influxdb_client selenium 
  ```
* get the influx credentials from Jamie or Guilherme and install them in [influx_credentials](influx_credentials.py)
* if you do not want to run the InfluxCloud instance, remove that call, [here](https://github.com/JamesSaxon/netrics/blob/master/net_measures.py#L317)
* take a look at `./net_measures.py -h`, and try all of the tests you might run.
  The available software varies from machine to machine, so this is not super robust.
* install those tests in a reasonable schedule, via `crontab -e`.  See for instance [crontab](https://github.com/JamesSaxon/netrics/blob/master/z_crontab)

