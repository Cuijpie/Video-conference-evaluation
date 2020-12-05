#!/usr/bin/python3

import click
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
import time
import getpass
from requests import get

# Find automatically the possible network interfaces.
addrs = psutil.net_if_addrs()
NW = list(addrs.keys())

# Global variables for monitor.
cpu_usage = -1
mem_usage = -1
average_packet_length = -1
packet_count = 0
bandwidth = -1

def _monitor(end_time: datetime) -> None:
    global cpu_usage, mem_usage, average_packet_length, packet_count, bandwidth
    cursor.hide()
    print('cpu_usage', '\t', 'mem_usage', '\t', 'Avg_packet_length', '\t', 'Packet_count', '\t', 'Bandwidth')
    
    try:
        while end_time >= datetime.now():
            sys.stdout.write(
                '\r' + str(cpu_usage) + '\t\t' + str(round(mem_usage, 3)) + '\t\t\t' + str(average_packet_length) + \
                '\t\t\t' + str(packet_count) + '\t\t' + str(bandwidth) + '\t')
            sys.stdout.flush()
            time.sleep(1)
            sys.stdout.write('\r                                                                                         ')
    except Exception as e:
        print(e)

def _track_metrics(pids: list, display_filter: str, sample: int, end_time: datetime, interface: str,
                   bandwidth_change_in: int) -> None:
    
    global average_packet_length, cpu_usage, mem_usage, packet_count, bandwidth
    
    _processes = []
    for pid in pids:
        _processes.append(psutil.Process(int(pid)))
    sample_time = datetime.now() + timedelta(seconds=sample)
    capture = pyshark.LiveCapture(interface=interface, display_filter=display_filter)
    
    data = []
    packet_length = []

    # Parameters for bandwidth throttling.
    bw_start = 500
    bw_run = False
    bw_throttle = 0
    bw_change = timedelta(minutes=bandwidth_change_in)
    bw_time = datetime.now()

    # Parameter for bandwidth
    net_io_counter = psutil.net_io_counters()

    try:
        for packet in capture.sniff_continuously():
            packet_length.append(int(packet[1].get('len')))
            packet_count += 1

            if sample_time < datetime.now():
                sample_time = datetime.now() + timedelta(seconds=sample)

                average_packet_length = round(sum(packet_length) / len(packet_length)) if len(packet_length) != 0 else 0
                
                cpu_usage = 0
                mem_usage = 0
                for _process in _processes:
                    cpu_usage += _process.cpu_percent()
                    mem_usage += _process.memory_percent()

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
                    bw_throttle * 1000
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

            if end_time < datetime.now() or (bw_throttle < 50 and bw_run):
                break

    except Exception as e:
        print('Error: ', e)

    if int(bandwidth_change_in) > 0:
        _stop_throttle_bandwidth()

    df = pd.DataFrame(data, columns=['time',
                                     'avg_packet_len',
                                     'packet_count',
                                     'cpu_usage',
                                     'mem_usage',
                                     'bandwidth_calc',
                                     'bandwidth',
                                     'bandwidth_limit'])
    df.to_csv(f'results/system/{datetime.today().strftime("%H:%M")}-system-metrics.csv')

    
def _get_ip_addresses(interface: str) -> list:
    # Assume that no other applications are used and the most used IP is correct.
    
    count = {}
    
    time_change = timedelta(seconds=30)
    time = datetime.now()
    capture = pyshark.LiveCapture(interface=interface)
    print('Calculate IP used by meeting software...(30 sec)')
    for packet in capture.sniff_continuously():
        try:
            src = packet['ip'].src
            dst = packet['ip'].dst 
            if src in count.keys():
                count[src] = count[src] + 1
            else:
                count[src] = 1
            if dst in count.keys():
                count[dst] = count[dst] + 1
            else:
                count[dst] = 1
            
            if datetime.now() > time + time_change:
                break
        except:
            pass
    if len(count.keys()) == 0:
        print('No packets found, check if the correct interface is used.')
        sys.exit()
    
    # Remove own external IP.
    local_ip = get('https://api.ipify.org').text
    if local_ip in count.keys():
        del count[local_ip]
    max_used_ip = [k for k, v in count.items() if v == max(count.values())][0]
    
    print('Automatic selected process IDs: ', max_used_ip)
    result = None
    while result not in ['Y', 'N']:
        result = input('Is IP ' + max_used_ip + ' correct? (Y/N): ')
        if result == 'N':
              ip = input('IP address of meeting software: ')
              return [ip]
        else:
            return [max_used_ip]

def _get_display_filter(interface: str) -> str:
    return 'ip.addr == ' + ' || ip.addr == '.join(_get_ip_addresses(interface))


def _get_pid_from_user():
    pids = input("Give list of process IDs ';' seperated: ")
    return pids.split(';')
    
def _setup(process, duration) -> tuple:
    if not os.path.exists("results"):
        os.makedirs("results")
    if not os.path.exists("results/system"):
        os.makedirs("results/system")
    if not os.path.exists("results/ping"):
        os.makedirs("results/ping")
    
    pids = [p.pid for p in psutil.process_iter() if len(p.name()) >= len(process) and process == p.name()[:len(process)]]
    if len(pids) == 0:
        # Ask the user for the Process IDs
        user_name = getpass.getuser()
        print('Processes started by user: ', user_name)
        pids_list = [proc for proc in psutil.process_iter()]
        for p in pids_list:
            print('\t', p.pid, p.name())
        pids = _get_pid_from_user()
        print(pids)
    else:
        print('Automatic selected process IDs: ', pids)
        result = None
        while result not in ['Y', 'N']:
            result = input('Are process IDs ' + str(pids) + ' correct? (Y/N): ')
            if result == 'N':
              pids = _get_pid_from_user()
              break
    
    end_time = datetime.now() + timedelta(minutes=int(duration))
    
    return pids, end_time

def _start_throttle_bandwidth(limit: int):
    os.system(f'wondershaper enp6s0 {limit} {limit}')


def _stop_throttle_bandwidth():
    print('Stop bandwidth limitation...')
    os.system(f'wondershaper clear enp6s0')


@click.command()
@click.option(
    "--process",
    prompt="Video conferencing software: ",
    help="The video conferencing software you want to measure.",
    required=True,
    type=click.Choice(["zoom", "teams", "Discord"])
)
@click.option(
    "--network_interface",
    prompt="Network interface",
    help="The network interface you are using.",
    required=True,
    type=click.Choice(NW)
)
@click.option(
    "--duration",
    prompt="Duration in minutes",
    help="The duration you want to experiment to take.",
    required=True,
)
@click.option(
    "--bandwidth_decrease",
    prompt="Duration of bandwidth steps in minutes (0 = no throttling)",
    required = True,
    help="The amount you want to throttle every minute.",
)

def main(process, network_interface, duration, bandwidth_decrease) -> None:
    
    print('Initialize...')
    pid, end_time = _setup(process, duration)

    print('Tracking metrics...')
    threading.Thread(target=_track_metrics, args=[pid, _get_display_filter(network_interface), 1, end_time, network_interface, int(bandwidth_decrease)]).start()

    print('Start monitor...')
    threading.Thread(target=_monitor, args=[end_time]).start()

if __name__ == "__main__":    
    main()
