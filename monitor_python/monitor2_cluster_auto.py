import os
import time
from datetime import datetime
# from threading import Timer, Thread

import numpy as np
import plotext as plt

from rediscluster import RedisCluster
import timeit
import os

import redis_connector_cluster as connector

# startup_nodes = [{"host":"172.20.1.101", "port":"8001"},{"host":"172.20.1.102", "port":"8002"},{"host":"172.20.1.103", "port":"8003"},
#                  {"host":"172.20.1.104", "port":"8004"},{"host":"172.20.1.105", "port":"8005"},{"host":"172.20.1.106", "port":"8006"}]

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
    # labels = []
    velocities_f = []
    velocities_r = []
    deltas = []

    values_sensor = getLast(stream_name, window_size, client)
    values_kpi = getLast(stream_name_kpis, window_size, client)

    if len(values_sensor) != 0:
        for i,v in enumerate(values_sensor):
            id, data = v
            
            # labels.append(datetime.strptime(data.get('date'), "%Y-%m-%d %H:%M:%S.%f"))
            velocities_f.append(float(data.get('velocity_f')))
            velocities_r.append(float(data.get('velocity_r')))
            deltas.append(float(data.get('velocity_r')) - float(data.get('velocity_f')))
            # rtts.append(timeit.default_timer() - float(data.get('local_timestamp')))

            # print(f"i: {i} local_timestamp: {float(data.get('local_timestamp'))}")
    
    kpi1s = []
    kpi2s = []
    decisions = []

    if len(values_kpi) != 0:
        for i,v in enumerate(values_kpi):
            id, data = v
            
            # labels.append(datetime.strptime(data.get('date'), "%Y-%m-%d %H:%M:%S.%f"))
            kpi1s.append(float(data.get('kpi1')))
            kpi2s.append(float(data.get('kpi2')))
            decisions.append(int(data.get('decision')))
            # rtts.append(timeit.default_timer() - float(data.get('local_timestamp')))

            # print(f"i: {i} local_timestamp: {float(data.get('local_timestamp'))}")



        # kpi1,kpi2 = get_kpis(deltas,kpi2_seqlength)
        # decision = make_decision(kpi1,kpi2,kpi1_threshold)
        # print(f"min_rtts: {min(rtts)}   values[-1]: {timeit.default_timer() - float(values[-1][1].get('local_timestamp'))}")
        # manage_queue(timeit.default_timer() - float(values[-1][1].get('local_timestamp')),rtt_queue,RTT_QUEUE_SIZE)

        # min_rtt = min(rtt_queue)
        # max_rtt = max(rtt_queue)
        # mean_rtt = sum(rtt_queue)/len(rtt_queue)

        # client.xadd(stream_name_kpis, {"kpi1": str(kpi1), "kpi2": str(kpi2), "decision": str(decision)})
        # store.client.xadd(stream_name_infos, {"min_rtt": str(min_rtt), "max_rtt": str(max_rtt), "mean_rtt": str(mean_rtt), "window_size": str(window_size)})

        # print(f"min_rtt: {min_rtt}s  max_rtt: {max_rtt}s  mean_rtt: {mean_rtt}s")
        title = 'Last Runs for machine 1'
        os.system('cls' if os.name == 'nt' else 'clear')
        plt.clt()
        plt.clf()
        #
        #todo make dates used in visualizations
        # dates = plt.datetimes_to_string(labels)
        # plt.plot([decision]*len(deltas), label="delta", yside="right", fillx=True, color="orange")
        plt.plot(deltas, label="delta", yside="right", fillx=True, color="gray")
        # plt.plot([kpi1]*len(deltas), label="kpi1", yside="left", color="blue")
        # plt.plot([kpi2]*len(deltas), label="kpi2", yside="left", color="green")
        # plt.plot(velocities_f, label="f", yside="left", color="blue")
        # plt.plot(velocities_r, label="r", yside="left", color="green")
        #
        plt.interactive(True)
        plt.show()

    time.sleep(refresh_ms/1000)

# def connect():
#     try:
#         # r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password, charset="utf-8", decode_responses=True)
#         r = RedisCluster(startup_nodes=startup_nodes, decode_responses=True, password="testpw")
#         # r = RedisCluster(host="127.0.0.1", port=8001, decode_responses=True)
#         return r
#     except:
#         e = "Error creating Redis connection"
#         print(e)
#         return None

def main():
    client = connector.connect()
    stream_name = "rm_1_1_signals"
    stream_name_kpis = "rm_1_1_kpis"
    stream_name_infos = "rm_1_1_metrics"

    # num_simulation_runs = 5000
    # simulation_delay_ms = 50
    event_window_size = 20
    refresh_time_ms = 50
    with client:
        client.ping()
        try:
            while True:
                displayRuns(client, event_window_size, refresh_time_ms, stream_name, stream_name_kpis) # , stream_name_infos)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
