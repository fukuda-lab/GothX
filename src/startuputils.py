import sys

from gns3utils import *


def startup_proj(project_name, project_should_be_empty: bool):
    check_resources()
    check_local_gns3_config()
    server = Server(*read_local_gns3_config())

    check_server_version(server)

    project = get_project_by_name(server, project_name)

    if project:
        print(f"Project {project_name} exists. ", project)
    else:
        print(f"Project {project_name} does not exsist!")
        # the project does not exist but it should not be empty
        if project_should_be_empty is False:
            sys.exit(1)
        else:
            project = create_project(server, project_name, 5000, 7500, 15)
            print("Created project ", project)

    open_project_if_closed(server, project)

    if (not project_should_be_empty) and len(get_all_nodes(server, project)) == 0:
        print(f"Project {project_name} is empty!")
        sys.exit(1)
    if project_should_be_empty and len(get_all_nodes(server, project)) > 0:
        print("Project is not empty!")
        answer = input("continue anyway? [y/N] ").strip()
        if answer != "y":
            print(answer, "(!='y'): stop")
            sys.exit(1)

    check_ipaddrs(server, project)

    docker_client = docker.from_env()
    docker_client.ping()

    # read project configuration file
    sim_config = configparser.ConfigParser()
    with open("../iot-sim.config", "r", encoding="utf-8") as cf:
        # include fake section header 'main'
        sim_config.read_string(f"[main]\n{cf.read()}")
        sim_config = sim_config["main"]

    return server, project, sim_config


class TopoZone:
    def __init__(self, coord: Position, internal_switch, router):
        self.coord: Position = coord
        self.switch = internal_switch
        self.router = router
