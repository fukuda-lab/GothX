#!/usr/bin/env python

import json
from collections import namedtuple
from pprint import pprint
from gns3fy import Gns3Connector
import gns3fy
import requests as requests
import sys


def stop_all_nodes(prj_nodes: list[gns3fy.Node]):
    if prj_nodes:
        for n in prj_nodes:
            print(n.name, n.status, end=" > ")
            n.stop()
            print(n.status)

def delete_proj(proj: gns3fy.Project):
    proj.get()
    if proj.status != "closed":
        stop_all_nodes(proj.nodes)
        proj.close()
    proj.delete()


def manage_node(node: gns3fy.Node, proj: gns3fy.Project):
    userin = ""
    while userin != "exit":
        userin = input(
            f"{node.name}\np: print info, sa: start node, so: stop node, co: get connected nodes, exit "
        )
        if userin == "p":
            pprint(node)
        elif userin == "sa":
            node.start()
            print(node.status)
        elif userin == "so":
            node.stop()
            print(node.status)
        elif userin == "co":
            from src.gns3utils import get_connected_nodes

            for con_node_id in get_connected_nodes(proj, node.node_id):
                conn_node = proj.get_node(node_id=con_node_id)
                print(f"{conn_node.name} {conn_node.status}")


def interactive_mode(projects: list[str]):
    proj = select_project_by_number(projects)
    userin = ""
    while userin != "exit":
        userin = input(
            "n: select a node, nq: select a node quiet, cl: close project, del: delete project "
        )
        if userin == "n" or userin == "nq":
            project_nodes = proj.nodes
            if userin != "nq":
                project_nodes.sort(key=lambda node: node.name)
                for idx_node, node_obj in enumerate(proj.nodes):
                    print(f"[{idx_node}]: {node_obj.name} {node_obj.status}")
            userin = input("node name or number ")
            try:
                userin = int(userin)
                node = project_nodes[userin]
            except ValueError:
                node = proj.get_node(name=userin)

            manage_node(node, proj)
        elif userin == "cl":
            proj.get_nodes()
            stop_all_nodes(proj.nodes)
            proj.close()
        elif userin == "del":
            delete_proj(proj)
    exit(0)

def delete_multiple_prjects():
    delete_projects_with_name_containing = input("delete_projects_with_name_containing: ")
    if delete_projects_with_name_containing.strip() == "":
        delete_projects_with_name_containing = "azertyuijhgfds"

    for p in proj_list:
        if delete_projects_with_name_containing in p[0]:
            print(f"will close and delete project {p[0]}")
            proj = gns3fy.Project(name=p[0], connector=server_connector)
            delete_proj(proj)

def select_project_by_number(projects) -> gns3fy.Project:
    proj_idx = int(input("Select project number "))
    print(f"{projects[proj_idx]}=")
    proj = gns3fy.Project(name=projects[proj_idx][0], connector=server_connector)
    proj.get()
    print(proj)
    return proj

# credentials are in ~/.config/GNS3/2.2/gns3_server.conf
server_connector = Gns3Connector(
    url="http://localhost:3080",
    user="admin",
    cred="P1Dwt0FBoFM0yKTx9yGOjzErmXDJIvpxm5AmxqEegTcHWspKd58dykRczak6yzHL",
)
print(server_connector)

new_uuid = "f4aadcdd-8989-47cf-aaf4-8c84bc891618"
# new_params = {
#     "name": "api_imported_gns3",
#     "path": "%2Fhome%2Fmpoisson%2FGNS3%2Fprojects%2Fimported_gns3"
# }
# new_params = {"name": "python_imported_gns3", "project_id": new_uuid, "path": "/home/mpoisson/GNS3/projects/python_imported_gns3"}
# resp = server_connector.http_call("post", f"http://localhost:3080/v2/projects/{new_uuid}/import", params=new_params)
# pprint(vars(resp))
proj_list = server_connector.projects_summary(is_print=False)
print(f"{len(proj_list)} projects")
for idx, proj in enumerate(proj_list):
    print(f"{idx}: {proj}")

print("run with -i for interactive program")
possible_arguments = ["-i", "-del", "-stop"]
if len(sys.argv) != 2:
    print(sys.argv)
    print(f"you must have 1 argument among {','.join(possible_arguments)}")
    exit(1)

if sys.argv[1] == "-i":
    interactive_mode(proj_list)
elif sys.argv[1] == "-del":
    print("-del mode: delete multiple projects")
    delete_multiple_prjects()
elif sys.argv[1] == possible_arguments[2]:
    project_to_stop = select_project_by_number(proj_list)
    stop_all_nodes(project_to_stop.nodes)
else:
    print(sys.argv)
    print(f"you must have 1 argument among {','.join(possible_arguments)}")
    exit(1)


