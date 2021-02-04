""" Measurements

    Records selected network measurements

"""

from subprocess import Popen, PIPE
import time
import sys
import re
import os
import json
import pandas as pd

from speedtest import Speedtest
from tinydb import TinyDB, Query, where
from tinydb.operations import increment
from tinydb.operations import set as tdb_set

reference_site_dict = {
        "www.google.com"             : "google",
        "www.youtube.com"            : "youtube",
        "www.facebook.com"           : "facebook", 
        "www.amazon.com"             : "amazon", 
        "www.wikipedia.org"          : "wikipedia",
        "www.chicagotribune.com" : "tribune", 
        "chicago.suntimes.com"   : "suntimes",
        "cs.uchicago.edu"        : "uchicago"
}


reference_sites = list(reference_site_dict.keys())

class Measurements:
    """ Take network measurements """

    def __init__(self, args):
        self.results = {}
        self.quiet = args.quiet
        self.sites = reference_sites
        self.labels = reference_site_dict

        db = TinyDB('speedtest.json')
        if len(db.all()) == 0:
            db.insert({'download': 600, 'upload': 50, 'test': False})

        if not self.quiet:
            print("\n --- NETWORK MEASUREMENTS ---")

    def update_sites(self, sites):
        self.labels = {}

        with open(sites) as f:
            for line in f:
                (website, label) = line.split()
                self.labels[website] = label

        self.sites = list(self.labels.keys())

    def update_max_speed(self, measured_down, measured_up):
        db = TinyDB('speedtest.json')
        max_speed = db.all()
        max_down = max(measured_down, max_speed[0]['download'])
        max_up = max(measured_up, max_speed[0]['upload'])

        if max_speed[0]['test']:
            db.update({'download': max_down})
            db.update({'upload': max_up})
        else:
            db.update({'download': measured_down})
            db.update({'upload': measured_up})

        db.update({'test':True})

    def speed(self, run_test):
        
        if not run_test:
            return

        s = Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        test_results = s.results.dict()
        
        download_speed = test_results["download"] / 1e6
        upload_speed = test_results["upload"] / 1e6

        self.update_max_speed(float(download_speed), float(upload_speed)) 

        self.results["speedtest_download"] = download_speed
        self.results["speedtest_upload"] = upload_speed

        if not self.quiet:
            print('\n --- Ookla speed tests ---')
            print(f'Download: {download_speed} Mb/s')
            print(f'Upload:   {upload_speed} Mb/s')

    def ping_latency(self, run_test):

        if not run_test:
            return 

        for site in self.sites:
            ping_cmd = "ping -i {:.2f} -c {:d} -w {:d} {:s}".format(0.25, 10, 5, site)
            ping_res = Popen(ping_cmd, shell=True, stdout=PIPE).stdout.read().decode('utf-8')
 
            ping_pkt_loss = float(re.findall(', ([0-9.]*)% packet loss', 
                    ping_res, re.MULTILINE)[0])

            ping_rtt_ms = re.findall('rtt [a-z/]* = ([0-9.]*)/([0-9.]*)/([0-9.]*)/([0-9.]*) ms',
                    ping_res)[0]
            ping_rtt_ms = [float(v) for v in ping_rtt_ms]

            label = self.labels[site]

            self.results[label + "_packet_loss_pct"] = ping_pkt_loss
            self.results[label  + "_rtt_min_ms"]      = ping_rtt_ms[0]
            self.results[label  + "_rtt_max_ms"]      = ping_rtt_ms[2]
            self.results[label  + "_rtt_avg_ms"]      = ping_rtt_ms[1]
            self.results[label  + "_rtt_mdev_ms"]     = ping_rtt_ms[3]
            
            if not self.quiet:
                print(f'\n --- {label} ping latency ---')
                print(f'Packet Loss: {ping_pkt_loss}%')
                print(f'Average RTT: {ping_rtt_ms[0]} (ms)')
                print(f'Minimum RTT: {ping_rtt_ms[1]} (ms)')
                print(f'Maximum RTT: {ping_rtt_ms[2]} (ms)')
                print(f'RTT Std Dev: {ping_rtt_ms[3]} (ms)')
        
    def dns_latency(self, run_test):

        if not run_test:
            return
        
        dig_delays = []

        for site in self.sites:
            dig_cmd = f'dig @8.8.8.8 {site}'
            dig_res = Popen(dig_cmd, shell=True, stdout=PIPE).stdout.read().decode('utf-8')

            dig_res = re.findall('Query time: ([0-9]*) msec', dig_res, re.MULTILINE)[0]
            dig_delays.append(int(dig_res))

        self.results["dns_query_avg_ms"] = sum(dig_delays) / len(dig_delays)
        self.results["dns_query_max_ms"] = max(dig_delays)
        
        if not self.quiet:
            print(f'\n --- DNS Delays (n = {len(dig_delays)}) ---')
            print(f'Avg DNS Query Time: {self.results["dns_query_avg_ms"]} ms')
            print(f'Max DNS Query Time: {self.results["dns_query_max_ms"]} ms')


    def hops_to_backbone(self, run_test):
        
    
        if not run_test:
            return
    
        tr_cmd = f'traceroute -m 15 -N 32 -w3 google.com | grep -m 1 ibone'
        tr_res = Popen(tr_cmd, shell=True, stdout=PIPE).stdout.read().decode('utf-8')

        tr_res = tr_res.strip().split(" ")
        
        if len(tr_res):
            hops = int(tr_res[0])
        else:
            hops = -1

        self.results["hops_to_backbone"] = hops
        
        if not self.quiet:
            print(f'\n --- Hops to Backbone ---')
            print(f'Hops: {self.results["hops_to_backbone"]}')

    def hops_to_target(self, site):

        if not site:
            return

        tr_cmd = f'traceroute -m 20 -q 5 -w 2 {site} | tail -1 | awk "{{print $1}}"'
        tr_res = Popen(tr_cmd, shell=True, stdout=PIPE).stdout.read().decode('utf-8')

        tr_res = tr_res.strip().split(" ")

        hops = -1

        if len(tr_res):
            hops = int(tr_res[0])

        label = self.labels[site]

        self.results[f'hops_to_{label}'] = hops

        if not self.quiet:
            print(f'\n --- Hops to Target ---')
            print("Hops to {}: {}".format(site, self.results[f'hops_to_{label}']))

    def connected_devices_arp(self, run_test):

        if not run_test:
            return

        ts = int(time.time())

        route_cmd = "ip r | awk 'NR==2' | awk '{print $1;}'"
        subnet = Popen(route_cmd, shell=True, 
                stdout=PIPE).stdout.read().decode('utf-8')

        nmap_cmd = f'nmap -sn {subnet}'
        Popen(nmap_cmd, shell=True, stdout=PIPE)

        arp_cmd = ("arp -e -i eth0 | grep : | grep -v '_gateway' | tr -s ' ' | "
                "cut -f3 -d' ' | sort | uniq")
        arp_res = Popen(arp_cmd, shell=True, stdout=PIPE).stdout.read().decode('utf-8')

        devices = set(arp_res.strip().split("\n"))
        active_devices = [[dev, ts, 1] for dev in devices]

        db = TinyDB('seen_devices.json')
        for device in active_devices:
            mac = Query()
            if db.contains(where('mac_addr') == device[0]):
                db.update(increment("n"), where('mac_addr') == device[0])
                db.update(tdb_set('last_seen', device[1]), 
                        where('mac_addr') == device[0])
            else:
                db.insert({'mac_addr' : device[0], 
                           'last_seen': device[1],
                           'n'        : device[2]}) 

        Time = Query()
        ndev_past_day  = len(db.search(Time.last_seen > (ts - 86400)))
        ndev_past_week = len(db.search(Time.last_seen > (ts - 86400*7)))

        self.results["devices_active"] = len(active_devices)
        self.results["devices_total"] = db.count(where('n') >= 1)
        self.results["devices_1day"] = ndev_past_day
        self.results["devices_1week"] = ndev_past_week
        
        if not self.quiet:
            print(f'\n --- Number of Devices ---')
            print(f'Number of active devices:        {self.results["devices_active"]}')
            print(f'Number of total devices:         {self.results["devices_total"]}')
            print(f'Number of devices in last 1 day: {self.results["devices_1day"]}')
            print(f'Number of devices in last week:  {self.results["devices_1week"]}')

    def iperf3_bandwidth(self, client, port):
        
        if not client:
            return

        db = TinyDB('speedtest.json')
        speed = db.all()

        print('input_speed', speed)
        measured_bw = {'upload': 0, 'download': 0}
        measured_jitter = {'upload' : 0, 'download' :0}

        for direction, value in measured_bw.items():
            reverse = False
            bandwidth = speed[0][direction] + 10
            if direction == 'download':
                print('down bw', bandwidth)
                bandwidth += 40
                reverse = True
            
            iperf_cmd = "iperf3 -c {} -p {} -u -i 0 -b {}M {} | awk 'NR=={}'"\
                .format(client, port, bandwidth,'-R' if reverse else "", 
                        10 if reverse else 8) 
            iperf_res = Popen(iperf_cmd, shell=True, stdout=PIPE).stdout.read().decode('utf-8')

            measured_bw[direction]     = iperf_res.split()[6]
            measured_jitter[direction] = iperf_res.split()[8]

            self.results[f'iperf_udp_{direction}'] = measured_bw['download']
            self.results[f'iperf_udp_{direction}_jitter_ms'] = measured_jitter['download']

            if not self.quiet:
                if direction == 'upload' : print('\n --- iperf Bandwidth and Jitter ---')
                print(f'{direction} bandwidth: {measured_bw[direction]} Mb/s')
                print(f'{direction} jitter: {measured_jitter[direction]} ms')


        self.update_max_speed(float(measured_bw['download']), float(measured_bw['upload']))
