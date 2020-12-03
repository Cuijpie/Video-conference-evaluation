import pandas as pd
import datetime
import matplotlib.pyplot as plt
import numpy as np
import sys


def data_analyzer(data):
    result_dict={}
    """
    For each second present in the datetimes it saves: how many times this second appear;
    the sum of every:   -'avg_packet_len'
                        -'packet_count'
                        -'cpu_usage'
                        -'mem_usage'
                        -'bandwidth_calc'
                        -'bandwidth'
    for that second
    """
    index=0
    for d in data['time']:
        date_time_obj = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S.%f')
        #print("Time ", date_time_obj.time().strftime('%S'))
        new_time=date_time_obj.time().strftime('%S')

        if new_time in result_dict.keys():
            result_dict[new_time]['count']+=1
            result_dict[new_time]['avg_packet_len']+=data['avg_packet_len'][index]
            result_dict[new_time]['packet_count']+=data['packet_count'][index]
            result_dict[new_time]['cpu_usage']+=data['cpu_usage'][index]
            result_dict[new_time]['mem_usage']+=data['mem_usage'][index]
            result_dict[new_time]['bandwidth_calc']+=data['bandwidth_calc'][index]
            result_dict[new_time]['bandwidth']+=data['bandwidth'][index]
        else:
            result_dict[new_time]={}
            result_dict[new_time]['count']=1
            result_dict[new_time]['avg_packet_len']=data['avg_packet_len'][index]
            result_dict[new_time]['packet_count']=data['packet_count'][index]
            result_dict[new_time]['cpu_usage']=data['cpu_usage'][index]
            result_dict[new_time]['mem_usage']=data['mem_usage'][index]
            result_dict[new_time]['bandwidth_calc']=data['bandwidth_calc'][index]
            result_dict[new_time]['bandwidth']=data['bandwidth'][index]
        index+=1

    """
    Get the mean value for each field based on the count number for each second 
    """

    for v in result_dict.keys():
        count=result_dict[v]["count"]
        result_dict[v]['avg_packet_len']=result_dict[v]['avg_packet_len']/count
        result_dict[v]['packet_count']=result_dict[v]['packet_count']/count
        result_dict[v]['cpu_usage']=result_dict[v]['cpu_usage']/count
        result_dict[v]['mem_usage']= result_dict[v]['mem_usage']/count
        result_dict[v]['bandwidth_calc']=result_dict[v]['bandwidth_calc']/count
        result_dict[v]['bandwidth']=result_dict[v]['bandwidth']/count

    return result_dict

def sort_ris(result_dict):
    """
    Sort the dictionary 
    """

    dictionary_items = result_dict.items()

    result_dict_list= sorted(dictionary_items)
    
    avg_packet_len=[]
    packet_count=[]
    cpu_usage=[]
    mem_usage=[]
    bandwidth_calc=[]
    bandwidth=[]

    for r in result_dict_list:
        avg_packet_len.append(r[1]["avg_packet_len"])
        packet_count.append(r[1]["packet_count"])
        cpu_usage.append(r[1]["cpu_usage"])
        mem_usage.append(r[1]["mem_usage"])
        bandwidth_calc.append(r[1]["bandwidth_calc"])
        bandwidth.append(r[1]["bandwidth"])

    return avg_packet_len,packet_count,cpu_usage,mem_usage,bandwidth_calc,bandwidth

def plot_graph0(line1, line2, output):

    fig=plt.figure()
    #plt.ylabel('Packet count')
    plt.xlabel('Time (seconds)')
    plt.plot(line1, label='Average packet lenght')
    plt.plot(line2, label='Packet count')
    plt.legend()
    plt.show()
    plt.plot()
    fig.savefig(output, dpi=200)
    return

def plot_graph1(line1, line2, output):
    
    fig=plt.figure()
    #plt.ylabel('Memory usage')
    plt.xlabel('Time (seconds)')
    plt.plot(line1, label='CPU usage')
    plt.plot(line2, label='Memory usage')
    plt.legend()
    plt.show()
    plt.plot()
    fig.savefig(output, dpi=200)
    return

def plot_graph2(line1, line2, output):
    
    fig=plt.figure()
    #plt.ylabel('Bandwidth')
    plt.xlabel('Time (seconds)')
    plt.plot(line1, label='Expected bandwidth')
    plt.plot(line2, label='Bandwidth')
    plt.legend()
    plt.show()
    plt.plot()
    fig.savefig(output, dpi=200)
    return

if __name__ == "__main__":
    #get the name from command line
    file = sys.argv[1]
    graph = sys.argv[2]

    data = pd.read_csv('%s'%file)
    result_dict=data_analyzer(data)
    avg_packet_len,packet_count,cpu_usage,mem_usage,bandwidth_calc,bandwidth=sort_ris(result_dict)

    if(graph == '0'):
        plot_graph0(avg_packet_len,packet_count,"1.png")
    if(graph == '1'):
        plot_graph1(cpu_usage,mem_usage,"2.png")
    if(graph == '2'):
        plot_graph2(bandwidth_calc,bandwidth,"3.png")

    

    











