from rediscluster import RedisCluster
import os
#todo - change the host, port and db to your system settings
###redis connection parameters###
# redis_host = "redis_container"
redis_host = os.environ["REDIS_HOST"]
# redis_port = 6379
redis_port = os.environ["REDIS_PORT"]
# redis_db = 0
redis_db = int(os.environ["REDIS_DB"])
redis_password = os.environ["REDIS_PASSWORD"]
num_redis = int(os.environ["NUM_REDIS_INSTANCES"])

startup_nodes = [{"host":f"{redis_host}{i}", "port":f"{str(redis_port)}{str(i)}"} for i in range(1,num_redis+1)]
# startup_nodes = [{"host":"172.20.1.101", "port":"8001"},{"host":"172.20.1.102", "port":"8002"},{"host":"172.20.1.103", "port":"8003"},
#                  {"host":"172.20.1.104", "port":"8004"},{"host":"172.20.1.105", "port":"8005"},{"host":"172.20.1.106", "port":"8006"},]
print(f"startup_nodes: {startup_nodes}")
###end - redis connection parameters###
def connect():
    try:
        r = RedisCluster(startup_nodes=startup_nodes, decode_responses=True, password="testpw")
        return r
    except:
        e = "Error creating Redis connection"
        print(e)
        return None

def main():
    redis_con = connect()
    if connect() != None:
        print("connection success")
        redis_con.ping()

if __name__ == "__main__":
    main()







    
