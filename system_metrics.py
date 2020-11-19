#!/usr/bin/python3
import argparse
import psutil
from datetime import datetime, timedelta
import time
import pandas as pd
import os

import matplotlib.pyplot as plt
import sys


def track(args) -> None:
    _process = psutil.Process(int(args.process))

    end_time = datetime.now() + timedelta(minutes=int(args.duration))

    data = []
    print('cpu_usage', '\t', 'mem_usage', '\t\t\t', 'packets_sent', '\t', 'packets_recv', '\t', 'bytes_sent', '\t',
          'bytes_recv')
    try:
        while end_time >= datetime.now():
            net_io_counter_t1 = psutil.net_io_counters()
            time.sleep(int(args.sample))
            net_io_counter_t2 = psutil.net_io_counters()

            packets_sent = net_io_counter_t2.packets_sent - net_io_counter_t1.packets_sent
            packets_recv = net_io_counter_t2.packets_recv - net_io_counter_t1.packets_recv
            bytes_sent = net_io_counter_t2.bytes_sent - net_io_counter_t1.bytes_sent
            bytes_recv = net_io_counter_t2.bytes_recv - net_io_counter_t1.bytes_recv

            cpu_usage = _process.cpu_percent()
            mem_usage = _process.memory_percent()
            sys.stdout.write(
                '\r ' + str(cpu_usage) + '\t\t' + str(mem_usage) + '\t\t' + str(packets_sent) + '\t\t' + str(
                    packets_recv) + '\t\t' + str(bytes_sent) + '\t\t' + str(bytes_recv) + '\t\t')
            sys.stdout.flush()
            data.append([datetime.now(), cpu_usage, mem_usage, packets_sent, packets_recv, bytes_sent, bytes_recv])
    except KeyboardInterrupt:
        pass

    df = pd.DataFrame(data, columns=['time',
                                     'cpu_usage',
                                     'mem_usage',
                                     "packets_sent",
                                     "packets_recv",
                                     "bytes_sent",
                                     "bytes_recv"])
    df.plot(x='time', y='bytes_recv', kind='line')
    plt.show()

    df.to_csv(f'results/s{args.sample}-d{args.duration}-{datetime.today().strftime("%H:%M:%S")}-sysmetrics.csv')


def setup() -> None:
    if not os.path.exists("results"):
        os.makedirs("results")


def main() -> None:
    print('Initialize...')
    # for proc in psutil.process_iter():
    #    try:
    #        # Get process name & pid from process object.
    #        processName = proc.name()
    #        processID = proc.pid
    #        if processName == 'Zoom.exe':
    #            print(processName, ' ::: ', processID)
    #    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
    #        pass

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--process', help='Process you want to measure system metrics for', default=16620)
    parser.add_argument('-s', '--sample', help='Sample size in seconds', default=1)
    parser.add_argument('-d', '--duration', help='The duration you want to measure the system for in minutes',
                        default=5)
    args = parser.parse_args()

    setup()
    track(args)


if __name__ == "__main__":
    main()
