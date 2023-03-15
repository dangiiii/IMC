# forget about the other nodes in the cluster on each node
redis-cli -a testpw --cluster call 172.20.1.101:8001 FLUSHALL
redis-cli -a testpw --cluster call 172.20.1.102:8002 FLUSHALL
redis-cli -a testpw --cluster call 172.20.1.103:8003 FLUSHALL
redis-cli -a testpw --cluster call 172.20.1.104:8004 FLUSHALL
redis-cli -a testpw --cluster call 172.20.1.105:8005 FLUSHALL
redis-cli -a testpw --cluster call 172.20.1.106:8006 FLUSHALL

redis-cli -a testpw --cluster call 172.20.1.101:8001 CLUSTER RESET
redis-cli -a testpw --cluster call 172.20.1.102:8002 CLUSTER RESET
redis-cli -a testpw --cluster call 172.20.1.103:8003 CLUSTER RESET
redis-cli -a testpw --cluster call 172.20.1.104:8004 CLUSTER RESET
redis-cli -a testpw --cluster call 172.20.1.105:8005 CLUSTER RESET
redis-cli -a testpw --cluster call 172.20.1.106:8006 CLUSTER RESET
