#!/usr/bin/python3
import argparse
import psutil
from datetime import datetime, timedelta
import pandas as pd
import os
import sys
import threading
import pyshark
import re
import cursor
from ping3 import ping

import matplotlib.pyplot as plt

cpu_usage = -1
mem_usage = -1
average_packet_length = -1
packet_count = 0
bandwidth = -1


def _monitor(end_time: datetime) -> None:
    cursor.hide()
    print('cpu_usage', '\t', 'mem_usage', '\t\t', 'Packet_count', '\t', 'Avg_packet_length', '\t', 'Bandwidth')

    while end_time >= datetime.now():
        sys.stdout.write(
            '\r ' + str(cpu_usage) + '\t\t' + str(mem_usage) + '\t\t' + str(average_packet_length) + '\t\t' + str(packet_count) + '\t\t' + str(bandwidth) + '\t')
        sys.stdout.flush()


def _ping(end_time: datetime, ips: list) -> None:
    data = []
    cols = ['time'] + ips
    while end_time >= datetime.now():
        tmp = [str(ping(ip)) for ip in ips]
        tmp = [str(datetime.now())] + tmp
        data.append(tmp)
    df = pd.DataFrame(data, columns=cols)

    df.to_csv(f'results/ping/{datetime.today().strftime("%H:%M")}-ping-metrics.csv')


def _track_metrics(pid: int, display_filter: str, sample: int, end_time: datetime, interface: str, bandwidth_change_in: int, cpu_change_in: int) -> None:
    global average_packet_length, cpu_usage, mem_usage, packet_count, bandwidth
    _process = psutil.Process(pid)
    sample_time = datetime.now() + timedelta(seconds=sample)
    capture = pyshark.LiveCapture(interface=interface,
                                  display_filter=display_filter)
    
    data = []
    packet_length = []
    
    # Parameters for bandwidth throttling.
    bw_start = 500
    bw_run = False
    bw_throttle = 0
    bw_change = timedelta(minutes=bandwidth_change_in)
    bw_time = datetime.now()
    
    # Parameters for cpu throttling.
    cpu_start = 20
    cpu_run = False
    cpu_throttle = 0
    cpu_change = timedelta(minutes=cpu_change_in)
    cpu_time = datetime.now()
    
    # Parameter for bandwidth
    net_io_counter = psutil.net_io_counters()

    try:
        for packet in capture.sniff_continuously():
            
            packet_length.append(int(packet[1].get('len')))
            packet_count += 1

            if sample_time < datetime.now():
                sample_time = datetime.now() + timedelta(seconds=sample)

                average_packet_length = round(sum(packet_length) / len(packet_length)) if len(packet_length) != 0 else 0
                
                cpu_usage = _process.cpu_percent()
                mem_usage = _process.memory_percent()
                
                net_io_counter_t = psutil.net_io_counters()
                bandwidth = net_io_counter_t.bytes_recv - net_io_counter.bytes_recv 
                net_io_counter = net_io_counter_t
                
                data.append([
                    datetime.now(),
                    average_packet_length,
                    packet_count,
                    cpu_usage,
                    mem_usage,
                    packet_count * average_packet_length,
                    bandwidth,
                    bw_throttle * 1000,
                    cpu_throttle      
                ])

                packet_length.clear()
                packet_count = 0
            
                # Adjust bandwidth throttling.
                if bandwidth_change_in > 0 and datetime.now() > bw_time + bw_change:
                    if bw_throttle == 0:
                        bw_run = True
                        bw_throttle = bw_start
                    else:
                        bw_throttle = bw_throttle - 50
                    _start_throttle_bandwidth(bw_throttle)
                    bw_time = datetime.now()
                
                # Adjust cpu throttling.
                if cpu_change_in > 0 and datetime.now() > cpu_time + cpu_change:
                    if cpu_throttle == 0:
                        cpu_run = True
                        cpu_throttle = cpu_start
                    else:
                        cpu_throttle = cpu_throttle - 1
                    _start_throttle_cpu(cpu_throttle)
                    cpu_time = datetime.now()               
            
            
            if end_time < datetime.now() or (cpu_throttle < 1 and cpu_run) or (bw_throttle < 50 and bw_run):
                break
            
    except Exception as e:
        print(e)
            
    if int(bandwidth_change_in) > 0:
        _stop_throttle_bandwidth()

    df = pd.DataFrame(data, columns=['time',
                                     'avg_packet_len',
                                     'packet_count',
                                     'cpu_usage',
                                     'mem_usage',
                                     'bandwidth_calc',
                                     'bandwidth',
                                     'bandwidth_limit',
                                     'cpu_limit'])                          
    df.to_csv(f'results/system/{datetime.today().strftime("%H:%M")}-system-metrics.csv')


def _get_ip_addresses(pid: int) -> list:
    ips = []
    for entry in os.popen(
            f"echo $(lsof -e /run/user/1000/gvfs -e /run/user/1000/doc -p {pid} | grep TCP | grep ESTABLISHED | awk '{{print $9}}')").read().split():
        if "ec2" in entry:
            raw_ip = re.search("ec2-(.+?)\\.", entry).group(1)
            ips.append(raw_ip.replace("-", "."))
        else:
            ips.append(re.search("->(.*?):https", entry).group(1))
    return ips


def _get_display_filter(pid: int) -> str:
    return 'ip.addr == ' + ' || ip.addr == '.join(_get_ip_addresses(pid))


def _setup(args) -> tuple:
    if not os.path.exists("results"):
        os.makedirs("results")
    if not os.path.exists("results/system"):
        os.makedirs("results/system")
    if not os.path.exists("results/ping"):
        os.makedirs("results/ping")

    pid = [p.pid for p in psutil.process_iter() if args.process in p.name()][0]

    end_time = datetime.now() + timedelta(minutes=int(args.duration))
    
    return pid, end_time


def _start_throttle_cpu(limit: int):
    os.system(f'cpulimit -b -p {pid} -l {limit}')

def _start_throttle_bandwidth(limit: int):
    os.system(f'wondershaper eno1 {limit} {limit}')

def _stop_throttle_bandwidth():
    print('Restore bandwidth...')
    os.system(f'wondershaper clear eno1')

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--process', help='Process you want to measure', default="zoom")
    parser.add_argument('-i', '--interface', help='Network interface', default="eth0")
    parser.add_argument('-d', '--duration', help='Duration you want to measure the system for in minutes', default=1)
    parser.add_argument('-b', '--bandwidth', help='Test with bandwith', default=0)
    parser.add_argument('-c', '--cpu', help='Test with CPU', default=0)
    args = parser.parse_args()

    print('Initialize...')
    pid, end_time = _setup(args)

    print('Tracking metrics...')
    threading.Thread(target=_track_metrics, args=[pid, _get_display_filter(pid), 1, end_time, args.interface, int(args.bandwidth), int(args.cpu)]).start()

    print('Staring pinging IPs...')
    threading.Thread(target=_ping, args=[end_time, _get_ip_addresses(pid)]).start()

    print('Start monitor...')
    threading.Thread(target=_monitor, args=[end_time]).start()


if __name__ == "__main__":
    main()
