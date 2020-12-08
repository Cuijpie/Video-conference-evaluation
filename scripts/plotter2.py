import pandas as pd
import datetime
import sys


def data_analyzer(data: pd.DataFrame) -> dict:
    result_dict = {}
    for index, time in enumerate(data['time']):
        date_time_obj = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        new_time = date_time_obj.time().strftime('%S')

        if new_time in result_dict.keys():
            result_dict[new_time]['avg_packet_len'].append(data['avg_packet_len'][index])
            result_dict[new_time]['packet_count'].append(data['packet_count'][index])
            result_dict[new_time]['cpu_usage'].append(data['cpu_usage'][index])
            result_dict[new_time]['bandwidth_calc'].append(data['bandwidth_calc'][index])
        else:
            result_dict[new_time] = {}
            result_dict[new_time]['avg_packet_len'] = [data['avg_packet_len'][index]]
            result_dict[new_time]['packet_count'] = [data['packet_count'][index]]
            result_dict[new_time]['cpu_usage'] = [data['cpu_usage'][index]]
            result_dict[new_time]['bandwidth_calc'] = [data['bandwidth_calc'][index]]

    return result_dict


if __name__ == "__main__":
    # get the name from command line
    file = sys.argv[1]

    csv = pd.read_csv('%s' % file)
    results = data_analyzer(csv)

    print(results['01'])
