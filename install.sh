#!/usr/bin/env bash

set -x

gns3() {
  sudo add-apt-repository ppa:gns3/ppa
  sudo apt update
  sudo apt install gns3-gui gns3-server
}
docker() {
  for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
  # Add Docker's official GPG key:
  sudo apt-get update
  sudo apt-get install ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc

  # Add the repository to Apt sources:
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update
  sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo groupadd docker
  sudo usermod -aG docker $USER
  newgrp docker
}
packages() {
  sudo apt install make wget python3 konsole
  python_version=$(python3 -V 2>&1 | awk '{print $2}' | cut -d '.' -f 1,2)
  sudo apt install $(echo "python$python_version-venv")
}
add_groups() {
  for gname in ubridge libvirt docker; do
    sudo usermod -aG "$gname" $USER;newgrp "$gname"
  done
}

"$@"
