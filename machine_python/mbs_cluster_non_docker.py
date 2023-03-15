import os
import time
from datetime import datetime
from threading import Timer, Thread

import numpy as np
import plotext as plt

import timeit

from rediscluster import RedisCluster
import argparse

location_id = 3
machine_id = 3

### definitions
mean_velocity_f = 1  # mean velocity of the rolled material exiting the process in m/s
mean_velocity_r = 1  # max velocity of the roll in m/s
max_slip = 0.1 # max slip (delta)

# stream_name = f"rm_{os.environ['LOCATION_ID']}_{os.environ[MACHINE_ID']}:signals"s
stream_name_kpis = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:kpis"
stream_name_infos = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:metrics"
stream_name_deltas = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:deltas"
stream_name_rtts = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:rtts"
stream_name_slips = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:slips"
stream_name_slips_norm = f"rm_{os.environ['LOCATION_ID']}_{os.environ['MACHINE_ID']}:slips_norm"


startup_nodes = [{"host":"172.20.1.101", "port":"8001"},{"host":"172.20.1.102", "port":"8002"},{"host":"172.20.1.103", "port":"8003"},
                 {"host":"172.20.1.104", "port":"8004"},{"host":"172.20.1.105", "port":"8005"},{"host":"172.20.1.106", "port":"8006"}]

print(f"startup_nodes: {startup_nodes}")

num_simulation_runs = 5000
simulation_delay_ms = 50
event_window_size = 20
refresh_time_ms = 50
kpi1_threshold = 0.3
kpi2_seqlength = int(event_window_size * 0.25)

class Measurement:
    def __init__(self, f: float, r: float):
        self.velocity_f = f
        self.velocity_r = r
        self.date = datetime.now()

    def __str__(self):
        return "Measurement taken " + self.date.strftime("%m/%d/%Y, %H:%M:%S:%f") + " - velocity_f: " + str(self.velocity_f) + " - velocity_r: " + str(self.velocity_r)

    def __repr__(self):
        return str(self)

class MeasurementStore(object):
    def __new__(cls, redisClient: object, streamName: str):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MeasurementStore, cls).__new__(cls)
        return cls.instance

    def __init__(self, redisClient: object, streamName: str):
        self._redisClient = redisClient
        self._streamName = streamName

    def store(self, m: Measurement):
        # print(f"store: date: {m.date}  vel_f: {m.velocity_f}  vel_r: {m.velocity_f}")
        with self._redisClient:
            self._redisClient.xadd(self._streamName, {"name": str(m.name), "date": str(m.date), "velocity_f": str(m.velocity_f),
                                                      "velocity_r": str(m.velocity_r)})
            return True
        return False

    def getLast(self, count: int):
        with self._redisClient:
            l = self._redisClient.xlen(self._streamName)

            if l > 0:
                values = self._redisClient.xrevrange(self._streamName, min='-', max='+',
                                                     count=min(l, count))  # getting the last elements from stream
                values.reverse()  # reversing for better plot
                return values
        return []



# custom thread to run simulation and store to Redis
class SimulationThread(Thread):
    # constructor
    def __init__(self, delay: float):
        # execute the base constructor
        Thread.__init__(self)
        # set the delay for run
        self.delay = delay
        # set a default value
        self.value = None

    def simulateMeasurement(self):
        num_r = np.random.default_rng().normal(mean_velocity_r, 0.1, size=None)
        num_f = np.random.uniform(low=max(mean_velocity_f, num_r), high=min(mean_velocity_f, num_r), size=None) # this could be made more meaningful
        m = Measurement(num_f, num_r)
        return m

    # function executed in a new thread
    def run(self):
        # block for a moment
        time.sleep(self.delay)
        # store data in an instance variable
        self.value = self.simulateMeasurement()

def simulateRuns(runs: int, delay_ms: int, s: MeasurementStore):
    start = timeit.default_timer()
    i = 0
    while ((timeit.default_timer() - start) < 300):
        # for i in range(runs):
        t = SimulationThread(delay_ms / 1000)
        t.start()
        t.join()
        s.store(t.value)
        if i % 200 == 0:
            print(f"time past: {(timeit.default_timer() - start)}s")
        i += 1


def make_decision(kpi1: int, kpi2: int, kpi1_threshold: int):
    if kpi1 > kpi1_threshold or kpi2 == 1:
        print("slow down")
        return -1
    elif kpi1 < kpi1_threshold or kpi2 == -1:
        print("speed up")
        return 1
    else:
        print("do nothing")
        return 0

def get_kpis(deltas: list, seq_length: int):
    vals = [1 if d > 0 else -1 if d < 0 else 0 for d in deltas]
    kpi1 = get_kpi1(vals)
    kpi2 = get_kpi2(vals, seq_length)

    return kpi1, kpi2

def get_slip_events_count(vals: list, length: int):
    return sum([1 if el > 0 else 0 for el in vals[:length]])


# vals: delta presented with 1: delta positive, 0: delta neutral, -1: delta negative (see get_kpis())
# if r > f: slow down
# if r < f: speed up
def get_kpi1(vals: list):
    return sum(vals)/len(vals)

# vals: delta presented with 1: delta positive, 0: delta neutral, -1: delta negative (see get_kpis())
# kpi2: checks whether or not all seq_length consecutive elements of the list are the same (meaning: all need to be either delta positive or delta negative
# for this parameter to switch its value, the actual delta value does not fall into account). 
# Possible values: [-1,0,1]:  1: more then seq_length consecutive elements delta pos -> rolls too fast, slow down
#                             0: less than seq_length consecutive elements delta pos or delta neg -> do nothing
#                            -1: more then seq_length consecutive elements delta neg -> rolls too slow, speed up

def get_kpi2(vals: list, seq_length: int):
    return int(all([el == vals[0] for el in vals[:seq_length]])) * vals[0]

def get_deltas(values):
    deltas = [float(data.get('velocity_r')) - float(data.get('velocity_f')) for id, data in values]
    return deltas

def get_delta(deltas, window_size):
    return sum(deltas[:window_size])/len(deltas[:window_size])

# def manage_queue(new_val, vals: deque, length: int):
#     if len(vals) == length:
#         vals.pop()
#     vals.appendleft(new_val)

def monitorRuns(window_size: int, d: MeasurementStore, refresh_ms: int, kpi1_threshold: int, kpi2_seqlength: int, rtts: list, stream_name_kpis: str, stream_name_infos: str):
    velocities_f = []
    velocities_r = []
    deltas = []

    values = d.getLast(window_size)

    if len(values) != 0:
        rtts_tmp = []
        velocities_f = []
        velocities_r = []

        for id, data in values[:20]:
            # labels.append(datetime.strptime(data.get('date'), "%Y-%m-%d %H:%M:%S.%f"))
            velocities_f.append(float(data.get('velocity_f')))
            velocities_r.append(float(data.get('velocity_r')))
            rtts_tmp.append(timeit.default_timer() - float(data.get('local_timestamp')))
        
        deltas = get_deltas(values)
        delta_20 = get_delta(deltas,20)
        delta_40 = get_delta(deltas,40)
        delta_80 = get_delta(deltas,80)
        delta_160 = get_delta(deltas,160)

        se_20 = get_slip_events_count(deltas,20)
        se_40 = get_slip_events_count(deltas,40)
        se_80 = get_slip_events_count(deltas,80)
        se_160 = get_slip_events_count(deltas,160)

        kpi1,kpi2 = get_kpis(deltas[:20],kpi2_seqlength)
        decision = make_decision(kpi1,kpi2,kpi1_threshold)

        rtts.append(min(rtts_tmp))

        d._redisClient.xadd(stream_name_kpis, {"kpi1": str(kpi1), "kpi2": str(kpi2), "decision": str(decision)})
        d._redisClient.xadd(stream_name_deltas, {"delta20": str(delta_20), "delta40": str(delta_40), "delta80": str(delta_80),"delta160": str(delta_160)})
        d._redisClient.xadd(stream_name_rtts, {"rtt": str(min(rtts_tmp))})
        d._redisClient.xadd(stream_name_slips, {"slip20": str(se_20), "slip40": str(se_40), "slip80": str(se_80), "slip160": str(se_160)})
        d._redisClient.xadd(stream_name_slips_norm, {"slip20": str(se_20/20), "slip40": str(se_40/40), "slip80": str(se_80/80), "slip160": str(se_160/160)})
      
    time.sleep(refresh_ms/1000)

def connect():
    try:
        # r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password, charset="utf-8", decode_responses=True)
        r = RedisCluster(startup_nodes=startup_nodes, decode_responses=True, password="testpw")
        return r
    except:
        e = "Error creating Redis connection"
        print(e)
        return None

def main():
    client = connect()
    with client:
        client.ping()

        # set expiry for keys
        # client.expire(stream_name_kpis,10800000)
        # client.expire(stream_name,80000)

        store = MeasurementStore(client, stream_name)
        test = Timer(1, simulateRuns, args=(num_simulation_runs, simulation_delay_ms, store))
        test.start()

        rtts = []

        try:
            while True:
                monitorRuns(event_window_size, store, refresh_time_ms, kpi1_threshold, kpi2_seqlength, store, stream_name_kpis, stream_name_infos)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()



