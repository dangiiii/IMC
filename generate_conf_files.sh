for port in $(seq 1 6); \
do \
# rm ./redis${port}/data/appendonlydir/*
# mkdir ./redis${port}
# mkdir ./redis${port}/data
rm -R ./redis/redis${port}/data
mkdir ./redis/redis${port}/data

touch ./redis/redis${port}/redis.conf
cat << EOF > ./redis/redis${port}/redis.conf
port 800${port}
# bind 172.20.1.10${port}
bind 0.0.0.0
protected-mode no
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 1000
cluster-slave-validity-factor 0
# cluster-announce-ip 172.20.1.10${port}
# cluster-announce-port 800${port}
# cluster-announce-bus-port 2000${port}
enable-debug-command yes
appendonly yes
masterauth "testpw"
EOF
done
