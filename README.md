## Simple Active Measurements on Router-Connected HW

To run these tests, please:
* check out this repository
  ```
  git clone https://github.com/JamesSaxon/netrics.git
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
* install those tests in a reasonable schedule, via `crontab -e`.  See for instance [crontab](https://github.com/JamesSaxon/netrics/blob/master/crontab)
## Setup for Jetson

Enter your home directory: Run `cd ~` if necessary. 

Run `git clone https://github.com/kyle-macmillan/netrics.git`

Run `sudo ./netrics/setup.sh` to update system and install system dependencies. You
will need to enter "yes" or "y" several times while this runs.

Run `python3 -m venv env/netson && source env/netson/bin/activate` to create and activate 
the virtual environment.

You must create a `.netrc` file in your home directory. In `.netrc`, write:
```
machine influx
login influx_login
password influx_password
```
Replacing `influx_login` and `influx_password` with your username and password.

Run `chmod og-rw /home/your-name/.netrc`, replacing 'your-name' with the parent directory of 
the `.netrc` file. 

Run `./netrics/netson.sh deployment`, replacing 'deployment' with the name of your deployment.
This takes about 1.5hrs currently. 
