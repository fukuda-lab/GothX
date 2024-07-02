#!/usr/bin/env bash

path_qemu_bin="/usr/bin/qemu-system-x86_64"

path_gns3_images="$HOME/GNS3/images"
path_download=$(xdg-user-dir DOWNLOAD)

echo """
This script assumes that
- GNS3 VM disk images are in $path_gns3_images
- VyOs files 'empty8G.qcow2' and 'vyos-1.3.0-rc6-amd64.iso' are in $path_download (following Makefile target 'make vyosiso')
"""
sleep 2

qemu_version=$("$path_qemu_bin" -version)
# Convert $v to lowercase for case-insensitive comparison
qemu_version_lowercase=$(echo "$qemu_version" | tr '[:upper:]' '[:lower:]')

# Check if qemu binary is at the expected location
if [[ "$qemu_version_lowercase" =~ "version" && "$qemu_version_lowercase" =~ "qemu" ]]; then
  echo "qemu binary found"
else
  echo "qemu binary not found in $path_qemu_bin"
  echo """
    possibles solutions
    - install qemu and move qemu binary to $path_qemu_bin
    - modify file router/iotsim-vyos-template.json, json key 'qemu_path'
    """
  exit 1
fi

## copy iso and to GNS3 files
path_qemu="$path_gns3_images/QEMU"
mkdir "$path_gns3_images/QEMU"
cd "$path_qemu" || exit
for vyos_file in "empty8G.qcow2" "vyos-1.3.0-rc6-amd64.iso"; do
  cp "$path_download/$vyos_file" .
  chmod +x $vyos_file
  md5sum $vyos_file | cut -d " " -f1 >"$vyos_file.md5sum"
done

echo """
Success
Now (activate your python virtual environment and) run 'python create_templates.py vyos_template'
"""
sleep 3
