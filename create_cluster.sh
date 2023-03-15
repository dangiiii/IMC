redis-cli -a testpw --cluster create 172.20.1.101:8001 172.20.1.102:8002 172.20.1.103:8003 172.20.1.104:8004 172.20.1.105:8005 172.20.1.106:8006 --cluster-replicas 1
# redis-cli -a testpw --cluster create localhost:8001 localhost:8002 localhost:8003 localhost:8004 localhost:8005 localhost:8006 --cluster-replicas 1
