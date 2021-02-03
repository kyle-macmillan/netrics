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

        if not self.quiet:
            print("\n --- NETWORK MEASUREMENTS ---")

    def update_sites(self, sites):
        self.labels = {}

        with open(sites) as f:
            for line in f:
                (website, label) = line.split()
                self.labels[website] = label

        self.sites = list(self.labels.keys())

    def speed(self, run_test):
        
        if not run_test:
            return

        s = Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        test_results = s.results.dict()

        self.results["speedtest_download"] = test_results["download"] / 1e6
        self.results["speedtest_upload"] = test_results["upload"] / 1e6

        if not self.quiet:
            print('\n --- Ookla speed tests ---')
            print(f'Download: {self.results["speedtest_download"]} Mb/s')
            print(f'Upload:   {self.results["speedtest_upload"]} Mb/s')

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



    def iperf3_bandwidth(self, client, port, reverse=False):
         
        if not client:
            return
    
        bandwidth = self.results["speedtest_upload"]
        if reverse:
            bandwidth = self.results["speedtest_download"]
        error = 100

        while error > 1:

            iperf_cmd = "iperf3 -c {} -p {} -i 0 -b {}M -u -J {}"\
                       .format(client, port, bandwidth,'-R' if reverse else "") 

            iperf_res = Popen(iperf_cmd, shell=True, stdout=PIPE)
            output, _ = iperf_res.communicate()
            results = json.loads(output)

            iperf_rate = results['end']['streams'][0]['udp']['bits_per_second'] / 10**6
            iperf_jitter = results['end']['streams'][0]['udp']['jitter_ms']
            error = results['end']['streams'][0]['udp']['lost_percent']

            
            bandwidth -= 0.5*error
            if reverse:
                bandwidth -= 7*error
            print(bandwidth)

        ul_dl = "download" if reverse else "upload"

        self.results[f'iperf_udp_{ul_dl}'] = iperf_rate
        self.results[f'iperf_udp_{ul_dl}_jitter_ms'] = iperf_jitter

        if not self.quiet:
            if not reverse: print('\n --- iperf Bandwidth and Jitter ---')
            print(f'{ul_dl} bandwidth: {iperf_rate} Mb/s')
            print(f'{ul_dl} jitter: {iperf_jitter} ms')
