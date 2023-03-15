import argparse
import os
import time
from datetime import datetime
from threading import Timer, Thread

import numpy as np
import plotext as plt

import timeit

import os
import redis_connector_cluster as connector

### definitions
mean_velocity_f = 1  # mean velocity of the rolled material exiting the process in m/s
mean_velocity_r = 1  # max velocity of the roll in m/s
max_slip = 0.1 # max slip (delta)

# stream_name = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:signals"
# stream_name_kpis = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:kpis"
# stream_name_infos = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:metrics"
# stream_name_deltas = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:deltas"
# stream_name_rtts = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:rtts"
# stream_name_slips = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:slips"
# stream_name_slips_norm = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:slips_norm"




def getLast(stream_name, count: int, redisClient: object):
    with redisClient:
        l = redisClient.xlen(stream_name)

        if l > 0:
            values = redisClient.xrevrange(stream_name, min='-', max='+',
                                                    count=min(l, count))  # getting the last elements from stream
            values.reverse()  # reversing for better plot
            return values
    return []


def displayRuns(client: object, window_size: int, refresh_ms: int, stream_name: str, stream_name_kpis: str):
    velocities_f = []
    velocities_r = []
    deltas = []

    values_sensor = getLast(stream_name, window_size, client)
    values_kpi = getLast(stream_name_kpis, window_size, client)

    if len(values_sensor) != 0:
        for id,data in values_sensor:            
            velocities_f.append(float(data.get('velocity_f')))
            velocities_r.append(float(data.get('velocity_r')))
            deltas.append(float(data.get('velocity_r')) - float(data.get('velocity_f')))
    
    kpi1s = []
    kpi2s = []
    decisions = []

    if len(values_kpi) != 0:
        for id, data in values_kpi:
            kpi1s.append(float(data.get('kpi1')))
            kpi2s.append(float(data.get('kpi2')))
            decisions.append(int(data.get('decision')))

        title = 'Last Runs for machine 1'
        os.system('cls' if os.name == 'nt' else 'clear')
        plt.clt()
        plt.clf()
        plt.plot(deltas, label="delta", yside="right", fillx=True, color="gray")
        plt.interactive(True)
        plt.show()

    time.sleep(refresh_ms/1000)

def main(location_id, machine_id):
    client = connector.connect()
    stream_name = f"rm_{location_id}_{machine_id}:signals"
    stream_name_kpis = f"rm_{location_id}_{machine_id}:kpis"

    event_window_size = 20
    refresh_time_ms = 50
    with client:
        client.ping()
        try:
            while True:
                displayRuns(client, event_window_size, refresh_time_ms, stream_name, stream_name_kpis)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="-l location_id -m machine_id")
    parser.add_argument("location_id", help="id of location and machine to monitor")
    parser.add_argument("machine_id", help="id of machine to monitor")
    args = parser.parse_args()
    main(args.location_id, args.machine_id)
