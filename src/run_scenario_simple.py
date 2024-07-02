"""Run scenario using the iot simulation topology (simple)."""

import sys

from gns3utils import *

PROJECT_NAME = "iot_simple_231127_1701"

check_resources()
check_local_gns3_config()
server = Server(*read_local_gns3_config())

check_server_version(server)

project = get_project_by_name(server, PROJECT_NAME)

if project:
    print(f"Project {PROJECT_NAME} exists. ", project)
else:
    print(f"Project {PROJECT_NAME} does not exsist!")
    print(f"{get_all_projects(server)}")
    sys.exit(1)

open_project_if_closed(server, project)

if len(get_all_nodes(server, project)) == 0:
    print(f"Project {PROJECT_NAME} is empty!")
    sys.exit(1)

check_ipaddrs(server, project)

#######
# Run #
#######

start_all_routers(server, project)
start_all_switches(server, project)
start_all_iot(server, project)
