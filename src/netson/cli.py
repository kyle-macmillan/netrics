""" netson command-line interface entry-point """

import argparse
import re
import time
import netrc
from datetime import datetime

from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb import InfluxDBClient


from measure import Measurements

def execute():
    """ Execute the netson CLI command """
    try:
        parser = build_parser()

        args = parser.parse_args()

        test = Measurements(args)

        if args.sites is not None:
            test.update_sites(args.sites)

        """ Run ookla speed test """
        test.speed(args.ookla)

        """ Measure ping latency to list of websites """
        test.ping_latency(args.ping)

        """ Measure DNS latency """
        test.dns_latency(args.dns)

        """ Count hops to local backbone """
        test.hops_to_backbone(args.backbone)

        """ Count hops to target website """
        test.hops_to_target(args.target)

        """ Count number of devices on network """
        test.connected_devices_arp(args.ndev)

        """ Run iperf3 bandwidth test """
        test.iperf3_bandwidth(client=args.iperf[0], port=args.iperf[1])

        """ Upload data to influx server """
        if args.upload:
            upload(test.results, test.results)

    except KeyboardInterrupt:
        print("\n ******** KEYBOARD INTERRUPT ********** \n")




def build_parser():
    """ Construct parser to interpret command-line args """

    parser = argparse.ArgumentParser(
            description='measure network on jetson')

    parser.add_argument(
            '-u', '--upload',
            default=False,
            action='store_true',
            help=("Upload measurements to infux")
    )

    parser.add_argument(
            '-q', '--quiet',
            default=False,
            action='store_true',
            help="Suppress output"
    )

    parser.add_argument(
            '-p', '--ping',
            default=False,
            action='store_true',
            help='Measure ping latency'
    )

    parser.add_argument(
            '-d', '--dns',
            default=False,
            action='store_true',
            help='Measure DNS latency'
    )

    parser.add_argument(
            '-b', '--backbone',
            default=False,
            const='www.google.com',
            nargs='?',
            action='store',
            help='Count hops to Chicago backbone (ibone)'
    )

    parser.add_argument(
            '-t', '--target',
            default=False,
            const='www.google.com',
            nargs='?',
            action='store',
            help='Count hops to target website'
    )

    parser.add_argument(
            '-n', '--ndev',
            default=False,
            action='store_true',
            help='Count number of connected devies'
    )

    parser.add_argument(
            '-s', '--ookla',
            default=False,
            action='store_true',
            help='Measure up/down using Ookla'
    )

    parser.add_argument(
            '-i', '--iperf',
            default=[False, False],
            nargs = 2,
            action='store',
            help='Measure connection with remote server. Needs [client] [port]',
    )

    parser.add_argument(
            '-f', '--sites',
            default=None,
            action='store',
            help='Text file containing sites to visit during test'
    )

    return parser   


def upload(upload_results, measurements):

    if not upload_results:
        return

    
    netrc_file = netrc.netrc()
    authTokens = netrc_file.authenticators("influx")
     
    creds = InfluxDBClient(host='tigerteam.io', port='9999', username=authTokens[0],
                password=authTokens[2], database='netrics', ssl=True, verify_ssl=True)

    creds.write_points([{"measurement": "networks",
                         "tags"        : {"install": authTokens[1]},
                         "fields"      : measurements,
                         "time"        : datetime.utcnow()
                        }])

