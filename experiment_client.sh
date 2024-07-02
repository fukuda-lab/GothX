#!/usr/bin/env bash

client_path="/home/mpoisson/Documents/NII/Manuel/gotham-iot-testbed/Dockerfiles/iot/domotic_monitor"
client_file="client_bis.py"
name_regex="domotic"

cont_ids=$(docker container ls | grep "$name_regex" | cut -d " " -f1)
for id in $cont_ids; do
  echo -n "cont $id "
  docker container cp "$client_path/$client_file" "$id:/"
  docker container exec -d "$id" chmod +x /$client_file
  docker container exec "$id" hostname
  #docker -d container exec $id "ls"
  echo "docker container exec $id bash"
done

exit
