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

cpu_usage = -1
mem_usage = -1
average_packet_length = -1
packet_count = 0


def _monitor(end_time: datetime) -> None:
    cursor.hide()
    print('cpu_usage', '\t', 'mem_usage', '\t\t', 'Packet_count', '\t', 'Avg_packet_length', '\t')

    while end_time >= datetime.now():
        sys.stdout.write(
            '\r ' + str(cpu_usage) + '\t\t' + str(mem_usage) + '\t\t' + str(average_packet_length) + '\t\t' + str(packet_count) + '\t')
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


def _track_metrics(pid: int, display_filter: str, sample: int, end_time: datetime) -> None:
    global average_packet_length, cpu_usage, mem_usage, packet_count
    _process = psutil.Process(pid)
    sample_time = datetime.now() + timedelta(seconds=sample)
    capture = pyshark.LiveCapture(interface='enp6s0',
                                  display_filter=display_filter)

    data = []
    packet_length = []

    for packet in capture.sniff_continuously():
        packet_length.append(int(packet[1].get('len')))
        packet_count += 1

        if sample_time < datetime.now():
            sample_time = datetime.now() + timedelta(seconds=sample)

            average_packet_length = round(sum(packet_length) / len(packet_length)) if len(packet_length) != 0 else 0
            cpu_usage = _process.cpu_percent()
            mem_usage = _process.memory_percent()
            data.append([
                datetime.now(),
                average_packet_length,
                packet_count,
                cpu_usage,
                mem_usage
            ])

            packet_length.clear()
            packet_count = 0
        if end_time < datetime.now():
            break

    df = pd.DataFrame(data, columns=['time',
                                     'avg_packet_len',
                                     'packet_count',
                                     'cpu_usage',
                                     'mem_usage'])
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

    end_time = datetime.now() + timedelta(minutes=args.duration)

    return pid, end_time


def _throttle_cpu(pid: int, limit: int):
    os.system(f'cpulimit -b -p {pid} -l {limit}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--process', help='Process you want to measure', default="zoom")
    parser.add_argument('-d', '--duration', type=int, help='Duration you want to measure the system for in minutes',
                        default=1)
    parser.add_argument('-s', '--sample', type=int, help='Sample size in seconds', default=1)
    parser.add_argument('-ct', '--cputhrottle', type=int, help='Limit cpu usage for given process', default=-1)
    args = parser.parse_args()

    pid, end_time = _setup(args)

    print('Initialize...')

    if args.cputhrottle != -1:
        print(f'Set CPU throttling to {args.cputhrottle} percent...')
        threading.Thread(target=_throttle_cpu, args=[pid, args.cputhrottle]).start()

    print('Tracking metrics...')
    threading.Thread(target=_track_metrics, args=[pid, _get_display_filter(pid), args.sample, end_time]).start()

    # print('Staring pinging IPs...')
    # threading.Thread(target=_ping, args=[end_time, _get_ip_addresses(pid)]).start()

    print('Start monitor...')
    threading.Thread(target=_monitor, args=[end_time]).start()


if __name__ == "__main__":
    main()
