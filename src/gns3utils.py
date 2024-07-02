"""Functions to automate network topology creation/manipulation etc. using the GNS3 API."""
import asyncio
import base64
import configparser
import datetime
import hashlib
import ipaddress
import json
import logging
import os
import re
import tarfile

import resource
import shlex
import time
import warnings
from collections import namedtuple, defaultdict
from pathlib import Path
from telnetlib import Telnet
from typing import Any, List, Dict, Optional, Pattern, Tuple, Set
from urllib.error import HTTPError

import docker
import gns3fy
import requests

path_gns3_server_conf: str = os.path.expanduser("~/.config/GNS3/2.2/gns3_server.conf")


class ProjectGNS3:
    def __init__(self, name: str, id: str, grid_unit: int, gns3fy_proj: gns3fy.Project):
        self.name: str = name
        self.id: str = id
        self.grid_unit: int = grid_unit
        self.gns3fy_proj: gns3fy.Project = gns3fy_proj


Item = namedtuple("Item", ("name", "id"))
Position = namedtuple("Position", ("x", "y"))
Server = namedtuple("Server", ("addr", "port", "auth", "user", "password"))


def md5sum_file(fname: str) -> str:
    """Get file MD5 checksum."""
    # TODO update in chunks.
    with open(fname, "rb") as f:
        data = f.read()
    return hashlib.md5(data).hexdigest()


def make_grid(num: int, cols: int):
    """Make grid."""
    xi, yi = 0, 0
    for i in range(1, num + 1):
        yield (xi, yi)
        xi += 1
        if i % cols == 0:
            yi += 1
            xi = 0


def check_resources() -> None:
    """Check some system resources."""
    nofile_soft, nofile_hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    if nofile_soft <= 1024:
        msg = (
            f"The maximum number of open file descriptors for the current process is set to {nofile_soft}.\n"
            "This limit might not be enough to run multiple devices in GNS3 (approx more than 150 docker devices, may vary).\n"
            "To increase the limit, edit '/etc/security/limits.conf' and append: \n"
            "*                hard    nofile          65536\n"
            "*                soft    nofile          65536\n"
        )
        warnings.warn(msg, RuntimeWarning)


def check_local_gns3_config() -> bool:
    """Checks for the GNS3 server config."""
    if not os.path.isfile(path_gns3_server_conf):
        print(
            f"No gns3 config file found at {path_gns3_server_conf}. Could not check if KVM is enabled.\n"
            f"(if KVM is not enabled): Enable KVM for better performance."
        )
        return False

    config = configparser.ConfigParser()
    with open(path_gns3_server_conf) as f:
        config.read_file(f)
    if "Qemu" not in config.keys():
        warnings.warn(
            "Qemu settings are not configured. Enable KVM for better performance.",
            RuntimeWarning,
        )
        return False
    kvm = config["Qemu"].get("enable_kvm")
    if kvm is None:
        warnings.warn(
            "'enable_kvm' key not defined. Enable KVM for better performance.",
            RuntimeWarning,
        )
        return False
    if kvm == "false":
        warnings.warn(
            "'enable_kvm' set to false. Enable KVM for better performance.",
            RuntimeWarning,
        )
        return False
    print(f"KVM is set to {kvm}")
    return True


def read_local_gns3_config():
    """Return some GNS3 configuration values."""
    if not os.path.isfile(path_gns3_server_conf):
        config = configparser.ConfigParser()

        default_server_conf = (
            "localhost",  # host
            3080,  # port
            False,  # auth
            "",  # user
            "",  # password
        )
        print(
            f"No gns3 config file found at {path_gns3_server_conf} use default server config:\n {default_server_conf}"
        )
        return default_server_conf
    config = configparser.ConfigParser()
    with open(path_gns3_server_conf) as f:
        config.read_file(f)
    return (
        config["Server"].get("host"),
        config["Server"].getint("port"),
        config["Server"].getboolean("auth"),
        config["Server"].get("user"),
        config["Server"].get("password"),
    )


def check_server_version(server: Server) -> str:
    """Check GNS3 server version."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/version",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    return req.json()["version"]


def get_all_projects(server: Server) -> List[Dict[str, Any]]:
    """Get all the projects in the GNS3 server."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    return req.json()


def get_project_by_name(server: Server, name: str) -> Optional[ProjectGNS3]:
    """Get GNS3 project by name."""
    projects = get_all_projects(server)
    filtered_project = list(filter(lambda x: x["name"] == name, projects))
    if not filtered_project:
        return None
    filtered_project = filtered_project[0]
    gns3fy_proj: gns3fy.Project = gns3fy.Project(
        name=name,
        connector=gns3fy.Gns3Connector(
            url=f"http://{server.addr}:{server.port}",
            user=server.user,
            cred=server.password,
        ),
    )
    gns3fy_proj.get()
    return ProjectGNS3(
        name=filtered_project["name"],
        id=filtered_project["project_id"],
        grid_unit=int(filtered_project["grid_size"]),
        gns3fy_proj=gns3fy_proj,
    )


def create_docker_template(
    server: Server, name: str, image: str, environment: str = ""
) -> Optional[Dict[str, Any]]:
    """Create a new GNS3 docker template.

    'environment' should be the empty string '' or a string with newline separated key=value pairs,
    e.g. environment = 'VAR_ONE=value1\nVAR2=2\nBLABLABLA=something'
    """
    defaults = {
        "adapters": 1,
        "builtin": False,
        "category": "guest",
        "compute_id": "local",
        "console_auto_start": False,
        "console_http_path": "/",
        "console_http_port": 80,
        "console_resolution": "1024x768",
        "console_type": "telnet",
        "custom_adapters": [],
        "default_name_format": "{name}-{0}",
        "extra_hosts": "",
        "extra_volumes": [],
        "start_command": "",
        "symbol": ":/symbols/docker_guest.svg",
        "template_type": "docker",
        "usage": "autogenerated template from iot-sim.",
    }

    defaults["name"] = name
    defaults["image"] = image
    defaults["environment"] = environment

    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/templates",
        data=json.dumps(defaults),
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    return req.json()


def environment_dict_to_string(env: dict):
    """Environment variable dictionary to string."""
    res = []
    for k, v in env.items():
        res.append(f"{k}={v}")
    return "\n".join(res)


def extrahosts_dict_to_string(hosts: dict):
    """GNS3 extra_hosts."""
    res = []
    for k, v in hosts.items():
        res.append(f"{k}:{v}")
    return "\n".join(res)


def environment_string_to_dict(env: str):
    """Environment variable string to dictionary."""
    return {pair.split("=", 1)[0]: pair.split("=", 1)[1] for pair in env.split("\n")}


def get_docker_node_environment(
    server: Server, project: ProjectGNS3, node_id: str
) -> str:
    """Get GNS3 docker node environment variables."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    return req.json()["properties"]["environment"]


def update_docker_node_environment(
    server: Server, project: ProjectGNS3, node_id: str, env: str
):
    """Update GNS3 docker node environment variables."""
    payload = {"environment": env}
    req = requests.put(
        f"http://{server.addr}:{server.port}/v2/compute/projects/{project.id}/docker/nodes/{node_id}",
        data=json.dumps(payload),
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    return req.json()


def update_docker_node_extrahosts(
    server: Server, project: ProjectGNS3, node_id: str, hosts: str
):
    """Update GNS3 docker node extra_hosts."""
    payload = {"extra_hosts": hosts}
    req = requests.put(
        f"http://{server.addr}:{server.port}/v2/compute/projects/{project.id}/docker/nodes/{node_id}",
        data=json.dumps(payload),
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    return req.json()


def create_project(
    server: Server, name: str, height: int, width: int, zoom: Optional[int] = 40
):
    """Create GNS3 project."""
    # http://api.gns3.net/en/2.2/api/v2/controller/project/projects.html
    # Coordinate 0,0 is located in the center of the project
    payload_project = {
        "name": name,
        "show_grid": True,
        "scene_height": int(height),
        "scene_width": int(width),
        "zoom": int(zoom),
    }
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects",
        data=json.dumps(payload_project),
        auth=(server.user, server.password),
    )
    try:
        req.raise_for_status()
    except HTTPError as http_err:
        print(f"existing projects : {get_all_projects(server)}")
        raise http_err
    req = req.json()
    gns3fy_proj: gns3fy.Project = gns3fy.Project(
        name=name,
        connector=gns3fy.Gns3Connector(
            url=f"http://{server.addr}:{server.port}",
            user=server.user,
            cred=server.password,
        ),
    )
    gns3fy_proj.get()
    return ProjectGNS3(
        name=req["name"],
        id=req["project_id"],
        grid_unit=int(req["grid_size"]),
        gns3fy_proj=gns3fy_proj,
    )


def open_project_if_closed(server: Server, project: ProjectGNS3):
    """If the GNS3 project is closed, open it."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}",
        auth=(server.user, server.password),
    )
    try:
        req.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(vars(req))
        # requests.exceptions.HTTPError about client version is a false error that appears at first try
        # just retry and it works well
        if (
            req.content.decode().find(
                "client version 1.12 is too old. Minimum supported API version is 1.24"
            )
            >= 0
        ):
            req = requests.get(
                f"http://{server.addr}:{server.port}/v2/projects/{project.id}",
                auth=(server.user, server.password),
            )
            req.raise_for_status()
        else:
            raise http_err
    req.raise_for_status()
    if req.json()["status"] == "opened":
        print(f"Project {project.name} is already open.")
        return
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/open",
        auth=(server.user, server.password),
    )
    try:
        req.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(vars(req))
        # requests.exceptions.HTTPError about client version is a false error that appears at first try
        # just retry and it works well
        if (
            req.content.decode().find(
                "client version 1.12 is too old. Minimum supported API version is 1.24"
            )
            >= 0
        ):
            req = requests.post(
                f"http://{server.addr}:{server.port}/v2/projects/{project.id}/open",
                auth=(server.user, server.password),
            )
            req.raise_for_status()
        else:
            raise http_err
    print(f"Project {project.name} {req.json()['status']}.")
    assert req.json()["status"] == "opened"


def get_all_templates(server: Server) -> List[Dict[str, Any]]:
    """Get all the defined GNS3 templates."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/templates",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    return req.json()


def get_static_interface_config_file(
    iface: str,
    address: str,
    netmask: str,
    gateway: str,
    nameserver: Optional[str] = None,
) -> str:
    """Configuration file for a static network interface."""
    if nameserver is None:
        nameserver = gateway
    return (
        "# autogenerated\n"
        f"# Static config for {iface}\n"
        f"auto {iface}\n"
        f"iface {iface} inet static\n"
        f"\taddress {address}\n"
        f"\tnetmask {netmask}\n"
        f"\tgateway {gateway}\n"
        f"\tup echo nameserver {nameserver} > /etc/resolv.conf\n"
    )


def get_template_from_id(server: Server, template_id: str) -> Dict[str, Any]:
    """Get templete description from template ID."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/templates/{template_id}",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    return req.json()


def get_template_id_from_name(
    templates: List[Dict[str, Any]], name: str
) -> Optional[str]:
    """Get GNS3 template ID from the template name."""
    for template in templates:
        if template["name"] == name:
            return template["template_id"]
    return None


def get_all_nodes(server: Server, project: ProjectGNS3) -> List[Dict[str, Any]]:
    """Get all nodes in a GNS3 project."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    return req.json()


def get_nodes_id_by_name_regexp(
    server: Server,
    project: ProjectGNS3,
    name_regexp: Pattern,
    return_items: bool = True,
) -> None | list[Item] | list[dict[str, Any]]:
    """
    Get the list of all node IDs that match a node name regular expression.
    if return_items is False, returns a list of dictionary with all characteristics of the node
    """
    nodes = get_all_nodes(server, project)
    nodes_filtered: list[dict[str, Any]] = list(
        filter(lambda n: name_regexp.match(n["name"]), nodes)
    )
    if len(nodes_filtered) == 0:
        print(f"0 node's name match regex {name_regexp}")
        return None
    if return_items:
        return [Item(n["name"], n["node_id"]) for n in nodes_filtered]
    else:
        return nodes_filtered


def get_node_telnet_host_port(
    server: Server, project: ProjectGNS3, node_id: str
) -> tuple:
    """Get the telnet hostname and port of a node."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    # TODO include checks for console type
    assert req.json()["console_type"] == "telnet"
    if req.json()["console_host"] in ("0.0.0.0", "::"):
        host = server.addr
    else:
        host = req.json()["console_host"]
    return (host, req.json()["console"])


def get_node_docker_container_id(
    server: Server, project: ProjectGNS3, node_id: str
) -> str:
    """Get the Docker container id."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    assert req.json()["node_type"] == "docker"
    return req.json()["properties"]["container_id"]


def get_container(server, project, node_id) -> docker.client.DockerClient:
    return docker.from_env().containers.get(
        get_node_docker_container_id(server, project, node_id)
    )


def send_command_via_container(
    server,
    project: ProjectGNS3,
    node_id: str,
    command: str,
    print_command: bool = False,
    exec_detach: bool = False,
    work_dir: str = None,
) -> str | None:
    """
    :param server:
    :param project:
    :param node_id:
    :return: the str output of the command, None in case of docker.errors.APIError
    """
    if print_command:
        print(f"Container will execute {command=}")
    # b64 encoding avoids problems like quotes
    b64_cmd = base64.b64encode(command.encode())
    shell_type = "sh"
    new_cmd = f"echo '{b64_cmd.decode()}' | base64 -d | {shell_type}"
    sh_split = shlex.split(f'{shell_type} -c "{new_cmd}"')

    container = get_container(server, project, node_id)
    try:
        # Use the input parameter to provide input to the executed command
        out = container.exec_run(sh_split, detach=exec_detach, workdir=work_dir).output
    except docker.errors.APIError as dockerAPIError:
        print(
            f"Error: could not execute command on container "
            f"with node name {project.gns3fy_proj.get_node(node_id=node_id).name}:"
            f" {dockerAPIError}"
        )
        return None
    if isinstance(out, bytes):
        out = out.decode()
    if (
        "error" in out.lower()
        and "connect.mqtt.converter.throw.on.error".lower() not in out.lower()
    ):
        print("\033[91m Command output contains 'error'")
        print(out + "\033[0m")
    return out


def copy_file_to_container_node(
    server, project: ProjectGNS3, node_name: str, src_path: Path, dst_dir_path: Path
) -> bool:
    """
    :param server:
    :param project:
    :param node_name:
    :param src_path: path on local computer of A FILE (no directory)
    :param dst_dir_path: path on container of an existing directory
    :return: True if everything went well
    """
    container = get_container(
        server, project, project.gns3fy_proj.get_node(name=node_name).node_id
    )
    if not os.path.isfile(src_path):
        raise FileNotFoundError(src_path)
    # save current directory
    current_dir = os.getcwd()

    os.chdir(os.path.dirname(src_path))
    tar_path = str(os.path.basename(src_path)) + ".tar"
    tar = tarfile.open(tar_path, mode="w")
    try:
        tar.add(str(os.path.basename(src_path)))
        data = open(tar_path, "rb").read()
        ok = container.put_archive(str(dst_dir_path), data)
    finally:
        tar.close()
        os.remove(tar_path)
        # restore directory used at the begining of the function
        os.chdir(current_dir)
    return ok


def is_watched_cmd_executed_in_container(
    watched_str: str, container: docker.DockerClient
) -> bool:
    """
    :param container:
    :param watched_str:
    :return: True if watched_str is in the commands in any of the running processes in the container
    """
    try:
        cmds_processus = str(
            list(process[-1] for process in container.top()["Processes"])
        )
    except TypeError as e:
        print(e)
        return False
    return watched_str in cmds_processus


def get_time_all_containers_do_not_execute_cmd(
    server,
    project,
    watched_str: str,
    watched_containers_names: list[str],
    max_wait_time: int,
) -> dict[str, list[datetime.datetime, datetime.datetime]]:
    """
    keep getting processes list of containers
    until all container nodes do not have a process command containing watched_str started.
    :param server:
    :param project:
    :param watched_str:
    :param watched_containers_names: names of the containers nodes to watch
    :param watched_containers_names: maximum number of seconds to wait after 1st end was detected. (If no error, all end detected before max_wait_time)
    :return: {node_name: [date1,date2] datetime (utc 0, timezone independent) when all processes in container did not contain watched_str in their cmd}
    """

    def zero_in_alltimes(
        alltimes: dict[docker.DockerClient : list[datetime.datetime]],
    ) -> bool:
        for val_1, val_2 in alltimes.values():
            if val_1 == 0 or val_2 == 0:
                return True
        return False

    logger = logging.getLogger()
    logging.info(f"Waiting start and end of process on {watched_containers_names}")

    watched_containers: list[docker.client.DockerClient] = list(
        get_container(server, project, project.gns3fy_proj.get_node(name=name).node_id)
        for name in watched_containers_names
    )
    # sleep to give some time for DDoS to begin
    time.sleep(1 * len(watched_containers))
    date_start_watching = datetime.datetime.now(datetime.timezone.utc)
    all_times: dict[docker.DockerClient : list[datetime.datetime]] = {
        cont: [date_start_watching, 0] for cont in watched_containers
    }

    first_end_time = None
    # While not all end have been detected on containers, or timeout not reached
    while zero_in_alltimes(all_times):
        # if not all ends have been found max_wait_time seconds after the 1st end was detected
        # fill with dummy coherent values, which will stop the while loop (zero_in_alltimes(all_times) will return False)
        current_datetime = datetime.datetime.now(datetime.timezone.utc)
        if (
            first_end_time is not None
            and (current_datetime - first_end_time).seconds > max_wait_time
        ) or (current_datetime - date_start_watching).seconds > (max_wait_time + 60 * 30):
            logging.info(
                f"timeout of {max_wait_time} seconds reached while waiting processus stop. "
                f"Early exit replacing times '0' by current time"
            )
            logger.handlers[0].flush()

            for container_obj, times in all_times.values():
                for start_end_idx in range(2):
                    if times[start_end_idx] == 0:
                        all_times[container_obj][start_end_idx] = datetime.datetime.now(
                            datetime.timezone.utc
                        )

        # time.sleep(1)
        for container in (
            cont for cont in watched_containers if all_times[cont][1] == 0
        ):
            try:
                watched_cmd_executed_in_container = (
                    is_watched_cmd_executed_in_container(watched_str, container)
                )
            except docker.errors.APIError:
                # happens when the container is not running (anymore)
                # fill all remaining times for the container in the dict and go to next iteration
                for idx_start_end in range(2):
                    if all_times[container][idx_start_end] == 0:
                        all_times[container][idx_start_end] = datetime.datetime.now(
                            datetime.timezone.utc
                        )
                continue

            if not watched_cmd_executed_in_container:
                # the cmd is not executed by the container, we consider it finished its execution
                all_times[container][1] = datetime.datetime.now(datetime.timezone.utc)
                logging.info(f"end detected for {container} {all_times=}")
                logger.handlers[0].flush()

                if first_end_time is None:
                    first_end_time = all_times[container][1]

    return {
        watched_containers_names[
            watched_containers.index(container_obj)
        ]: times_start_stop
        for container_obj, times_start_stop in all_times.items()
    }


def get_links_id_from_node_connected_to_name_regexp(
    server: Server, project: ProjectGNS3, node_id: str, name_regexp: Pattern
) -> Optional[List[Item]]:
    """Get all the link IDs from node node_id connected to other nodes with names that match name_regexp regular expression."""
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    node_name = req.json()["name"]

    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}/links",
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    links = req.json()
    relevant_nodes = get_nodes_id_by_name_regexp(server, project, name_regexp)
    if relevant_nodes is None:
        print(
            f"get_links_id_from_node_connected_to_name_regexp, no nodes found with regex {name_regexp}"
        )
        return None

    def is_link_relevant(link: Dict) -> Optional[Item]:
        for c in link["nodes"]:  # two ends of the link
            for rn in relevant_nodes:
                if c["node_id"] == rn.id:
                    return rn
        return None

    links_filtered: List[Item] = []
    for link in links:
        linked_node = is_link_relevant(link)
        if linked_node:
            links_filtered.append(
                Item(f"{linked_node.name} <--> {node_name}", link["link_id"])
            )

    return links_filtered


def create_node(
    server: Server,
    project: ProjectGNS3,
    start_x: int,
    start_y: int,
    node_template_id: str,
):
    """Create selected node at coordinates start_x, start_y."""
    payload = {"x": int(start_x), "y": int(start_y)}
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/templates/{node_template_id}",
        data=json.dumps(payload),
        auth=(server.user, server.password),
    )
    try:
        req.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(vars(req))
        # requests.exceptions.HTTPError about client version is a false error that appears at first try
        # just retry and it works well
        if (
            req.content.decode().find(
                "client version 1.12 is too old. Minimum supported API version is 1.24"
            )
            >= 0
        ):
            req = requests.post(
                f"http://{server.addr}:{server.port}/v2/projects/{project.id}/templates/{node_template_id}",
                data=json.dumps(payload),
                auth=(server.user, server.password),
            )
            req.raise_for_status()
        else:
            raise http_err
    if project.gns3fy_proj:
        project.gns3fy_proj.get()
    return req.json()


def start_node(
    server: Server, project: ProjectGNS3, node_id: str, sleep_time: float = 0
) -> None:
    """Start selected node."""
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}/start",
        data={},
        auth=(server.user, server.password),
    )
    try:
        req.raise_for_status()
    except HTTPError as http_err:
        print(http_err.reason)
        raise http_err
    time.sleep(sleep_time)


def stop_node(server: Server, project: ProjectGNS3, node_id: str) -> None:
    """Stop selected node."""
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}/stop",
        data={},
        auth=(server.user, server.password),
    )
    req.raise_for_status()


def delete_node(server: Server, project: ProjectGNS3, node_id: str) -> None:
    """Delete selected node."""
    # check if node is running?
    req = requests.delete(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}",
        auth=(server.user, server.password),
    )
    req.raise_for_status()


def create_link_easy(server, project, node1_id, node2_id):
    """
    Create a link between nodes using the 1st free adapter it finds
    :raise KeyError if all adapters are occupied for node1 or node2
    :param server:
    :param project:
    :param node1_id:
    :param node2_id:
    :return: str, json content http reponse from server
    """
    _, free1 = get_node_occupied_free_adapters(
        node_id=node1_id, gns3fy_proj=project.gns3fy_proj
    )
    _, free2 = get_node_occupied_free_adapters(
        node_id=node2_id, gns3fy_proj=project.gns3fy_proj
    )
    # TODO check if link already exist, if it exists, do not create link

    for node, free_set in zip((node1_id, node2_id), (free1, free2)):
        if len(free_set) == 0:
            raise KeyError(
                f"All adapters occupied for node {project.gns3fy_proj.get_node(node_id=node)}"
            )
    return create_link(server, project, node1_id, free1.pop(), node2_id, free2.pop())


def create_link(
    server: Server,
    project: ProjectGNS3,
    node1_id: str,
    node1_adapter: int,
    node2_id: str,
    node2_adapter: int,
) -> str:
    """
    Create link between two nodes. **Use function create_link_easy** if you do not want to specify node1/2_adapter
    :return str, json content http reponse from server
    """
    payload = {
        "nodes": [
            {"node_id": node1_id, "adapter_number": node1_adapter, "port_number": 0},
            {"node_id": node2_id, "adapter_number": node2_adapter, "port_number": 0},
        ]
    }
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/links",
        data=json.dumps(payload),
        auth=(server.user, server.password),
    )
    req.raise_for_status()
    # TODO rename link node labels
    return req.json()


def set_node_network_interfaces(
    server: Server,
    project: ProjectGNS3,
    node_id: str,
    iface_name: str,
    ip_iface: ipaddress.IPv4Interface,
    gateway: str,
    nameserver: Optional[str] = None,
) -> None:
    """Configure the /etc/network/interfaces file for the node."""
    if ip_iface.netmask == ipaddress.IPv4Address("255.255.255.255"):
        warnings.warn(f"Interface netmask is set to {ip_iface.netmask}", RuntimeWarning)
    payload = get_static_interface_config_file(
        iface_name, str(ip_iface.ip), str(ip_iface.netmask), gateway, nameserver
    )
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}/files/etc/network/interfaces",
        data=payload,
        auth=(server.user, server.password),
    )
    req.raise_for_status()


def create_cluster_of_nodes(
    server: Server,
    project: ProjectGNS3,
    num_devices: int,
    start_x: int,
    start_y: int,
    nodes_per_row: int,
    switch_template_id: str,
    node_template_id: str,
    upstream_switch_id: Optional[str],
    upstream_switch_port: Optional[int],
    node_start_ip_iface: ipaddress.IPv4Interface,
    gateway: str,
    nameserver: str,
    spacing: Optional[float] = 2,
):
    """Create cluster of nodes.

          R  <--- gateway (must exist in the topology).
          |
          S  <--- upstream switch (must exist in the topology).
         /
        S  <----- cluster switch, based on switch_template_id. At coordinates (start_x, start_y).
        |
    n n n n n    |  num_devices number of            first ip address = node_start_ip_iface.ip
    n n n n n  <-|  nodes, based on                  last ip address = node_start_ip_iface.ip + num_devices - 1
    n n n n n    |  node_template_id.

    :return: cluster_switch, devices, coord_first, coord_last
    """
    assert num_devices > 0
    assert nodes_per_row > 0
    assert get_template_from_id(server, switch_template_id)["adapters"] >= (
        num_devices - (1 if upstream_switch_id else 0)
    )
    if not spacing:
        spacing = 2

    # create cluster switch
    cluster_switch = create_node(server, project, start_x, start_y, switch_template_id)
    print(f"Created node {cluster_switch['name']}")
    _, free_adapters = get_node_occupied_free_adapters(
        node_id=cluster_switch["node_id"], gns3fy_proj=project.gns3fy_proj
    )
    if num_devices > len(free_adapters):
        raise ValueError(
            f"The cluster switch can be linked to {len(free_adapters) - 1} devices. "
            f"Current argument: {num_devices=} must be reduced"
        )
    # create device grid
    coord_first = Position(
        start_x - project.grid_unit * spacing * (nodes_per_row - 1) // 2,
        start_y + project.grid_unit * spacing,
    )
    devices = []

    for dx, dy in make_grid(num_devices, nodes_per_row):
        device = create_node(
            server,
            project,
            coord_first.x + project.grid_unit * spacing * dx,
            coord_first.y + project.grid_unit * spacing * dy,
            node_template_id,
        )
        devices.append(device)
        print(f"Created node {device['name']}")
        time.sleep(0.1)

    coord_last = Position(devices[-1]["x"], devices[-1]["y"])

    # links
    if upstream_switch_id:
        create_link_easy(server, project, cluster_switch["node_id"], upstream_switch_id)
        print(f"Created link {cluster_switch['name']} <--> {upstream_switch_id}")
    for i, device in enumerate(devices, start=1):
        create_link(server, project, device["node_id"], 0, cluster_switch["node_id"], i)
        print(f"Creating link {device['name']} <--> {cluster_switch['name']}")
        time.sleep(0.1)

    # configure devices
    for i, device in enumerate(devices, start=0):
        device_ip_iface = ipaddress.IPv4Interface(
            f"{node_start_ip_iface.ip + i}/{node_start_ip_iface.netmask}"
        )
        set_node_network_interfaces(
            server,
            project,
            device["node_id"],
            "eth0",
            device_ip_iface,
            gateway,
            nameserver,
        )
        print(
            f"Configuring {device['name']} addr: {device_ip_iface.ip}/{device_ip_iface.netmask} gw: {gateway} ns: {nameserver}"
        )

    # decoration
    payload = {
        "x": int(start_x + project.grid_unit * spacing),
        "y": int(start_y - 15),
        "svg": f'<svg><text font-family="monospace" font-size="12">Start addr: {node_start_ip_iface.ip}/{node_start_ip_iface.netmask}</text></svg>',
    }
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/drawings",
        data=json.dumps(payload),
        auth=(server.user, server.password),
    )
    req.raise_for_status()

    payload = {
        "x": int(start_x + project.grid_unit * spacing),
        "y": int(start_y),
        "svg": f'<svg><text font-family="monospace" font-size="12">End addr  : {device_ip_iface.ip}/{device_ip_iface.netmask}</text></svg>',
    }
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/drawings",
        data=json.dumps(payload),
        auth=(server.user, server.password),
    )
    req.raise_for_status()

    payload = {
        "x": int(start_x + project.grid_unit * spacing),
        "y": int(start_y + 15),
        "svg": f'<svg><text font-family="monospace" font-size="12">Gateway   : {gateway}</text></svg>',
    }
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/drawings",
        data=json.dumps(payload),
        auth=(server.user, server.password),
    )
    req.raise_for_status()

    payload = {
        "x": int(start_x + project.grid_unit * spacing),
        "y": int(start_y + 30),
        "svg": f'<svg><text font-family="monospace" font-size="12">Nameserver: {nameserver}</text></svg>',
    }
    req = requests.post(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/drawings",
        data=json.dumps(payload),
        auth=(server.user, server.password),
    )
    req.raise_for_status()

    return (cluster_switch, devices, coord_first, coord_last)


def start_capture(server, project, link_ids):
    """Start packet capture (wireshark) in the selected link_ids."""
    for link in link_ids:
        req = requests.post(
            f"http://{server.addr}:{server.port}/v2/projects/{project.id}/links/{link}/start_capture",
            data={},
            auth=(server.user, server.password),
        )
        msg_already = "Packet capture is already activated "
        already = msg_already in req.content.decode()
        result = {}
        result["capture_file_name"] = "Unknown"
        result["capturing"] = "Unknown"
        if already:
            print(msg_already)
        else:
            req.raise_for_status()
            result = req.json()
        print(
            f"Capturing {result['capturing']}, in file GNS3/projects/{project.id}/project-files/captures/{result['capture_file_name']}"
        )
        time.sleep(0.3)


def stop_capture(server, project, link_ids):
    """Stop packet capture in the selected link_ids."""
    for link in link_ids:
        req = requests.post(
            f"http://{server.addr}:{server.port}/v2/projects/{project.id}/links/{link}/stop_capture",
            data={},
            auth=(server.user, server.password),
        )
        req.raise_for_status()
        result = req.json()
        print(f"Capturing {result['capturing']}, {result['capture_file_name']}")
        time.sleep(0.3)


def start_all_nodes_by_name_regexp(
    server: Server,
    project: ProjectGNS3,
    node_pattern: Pattern,
    sleeptime: float = 0.1,
) -> List[str]:
    """
    Start all nodes that match a name regexp.

    :param server:
    :param project:
    :param node_pattern:
    :param sleeptime: time to wait between two nodes start
    :return: the list of ids of nodes started
    """
    nodes = get_nodes_id_by_name_regexp(server, project, node_pattern)
    print(f"going to start {len(nodes)} nodes ({node_pattern})")
    started_ids = []
    if nodes:
        for node in nodes:
            print(f"Starting {node.name}... ", end="", flush=True)
            if project.gns3fy_proj.get_node(name=node.name).status != "started":
                # project.gns3fy_proj.get_node(node_id=node.id).start()
                start_node(server, project, node.id)
                print("OK")
                time.sleep(sleeptime)
            else:
                print(f"It was already started")
            started_ids.append(node.id)
    return started_ids


def stop_all_nodes_by_name_regexp(
    server: Server,
    project: ProjectGNS3,
    node_pattern: Pattern,
    sleeptime: float = 0.1,
) -> None:
    """Stop all nodes that match a name regexp."""
    nodes = get_nodes_id_by_name_regexp(server, project, node_pattern)
    if nodes:
        print(f"found {len(nodes)} nodes")
        for node in nodes:
            print(f"Stopping {node.name}... ", end="", flush=True)
            stop_node(server, project, node.id)
            print("OK")
            time.sleep(sleeptime)


def start_all_switches(
    server: Server,
    project: ProjectGNS3,
    switches_pattern: Pattern = re.compile("openvswitch.*", re.IGNORECASE),
    sleeptime: float = 1.0,
) -> None:
    """Start all network switch nodes (OpenvSwitch switches)."""
    start_all_nodes_by_name_regexp(server, project, switches_pattern, sleeptime)


def start_all_routers(
    server: Server,
    project: ProjectGNS3,
    routers_pattern: Pattern = re.compile("vyos.*", re.IGNORECASE),
    sleeptime: float = 60.0,
) -> List[str]:
    """Start all router nodes (VyOS routers)."""
    return start_all_nodes_by_name_regexp(server, project, routers_pattern, sleeptime)


def start_all_iot(
    server: Server,
    project: ProjectGNS3,
    iot_pattern: Pattern = re.compile("iotsim-.*", re.IGNORECASE),
) -> None:
    """Start all iotsim-* docker nodes."""
    start_all_nodes_by_name_regexp(server, project, iot_pattern)


def stop_all_switches(
    server: Server,
    project: ProjectGNS3,
    switches_pattern: Pattern = re.compile("openvswitch.*", re.IGNORECASE),
) -> None:
    """Stop all network switch nodes (OpenvSwitch switches)."""
    stop_all_nodes_by_name_regexp(server, project, switches_pattern)


def stop_all_routers(
    server: Server,
    project: ProjectGNS3,
    routers_pattern: Pattern = re.compile("vyos.*", re.IGNORECASE),
) -> None:
    """Stop all router nodes (VyOS routers)."""
    stop_all_nodes_by_name_regexp(server, project, routers_pattern)


def start_capture_all_iot_links(
    server,
    project,
    nodes1_name_pattern: Pattern = re.compile("openvswitch.*", re.IGNORECASE),
    nodes2_name_pattern: Pattern = re.compile(
        "mqtt-device.*|coap-device.*", re.IGNORECASE
    ),
) -> None:
    """
    Start packet capture on links between nodes matching @nodes1_name_pattern and nodes matching @nodes2_name_pattern.
    """
    switches = get_nodes_id_by_name_regexp(server, project, nodes1_name_pattern)
    if switches:
        print(f"found {len(switches)} switches")
        for sw in switches:
            print(f"Finding links in switch {sw.name}... ", end="", flush=True)
            links = get_links_id_from_node_connected_to_name_regexp(
                server, project, sw.id, nodes2_name_pattern
            )
            print(f"{len(links)} links found")
            if links:
                for lk in links:
                    gns3fy_lk: gns3fy.Link = project.gns3fy_proj.get_link(lk.id)
                    if gns3fy_lk.capturing:
                        print("Link already capturing")
                    else:
                        print(
                            f"\t Starting capture in link {lk.name}... ",
                            end="",
                            flush=True,
                        )
                        start_capture(server, project, [lk.id])
                        print("OK")
            else:
                print("0 links, skipping.")
        time.sleep(0.3)


def start_capture_between_two_nodes(
    server, project, node1_name_regex: str, node2_name_regex: str
):
    n1 = get_nodes_id_by_name_regexp(
        server, project, re.compile(node1_name_regex, re.IGNORECASE), return_items=False
    )
    n2 = get_nodes_id_by_name_regexp(
        server, project, re.compile(node2_name_regex, re.IGNORECASE), return_items=False
    )
    for node_retrieved in (n1, n2):
        if len(node_retrieved) != 1:
            print(len(node_retrieved))
            raise ValueError(
                f"name regex must match exactly 1 node. Regex {node1_name_regex} and {node2_name_regex}\n retrieved {node_retrieved}"
            )
    n1_links = [
        link["link_id"] for link in get_node_links(server, project, n1[0]["node_id"])
    ]
    n2_links = [
        link["link_id"] for link in get_node_links(server, project, n2[0]["node_id"])
    ]
    print(n1_links)
    print(n2_links)
    link_target = set(n1_links).intersection(set(n2_links))
    if len(link_target) != 1:
        raise ValueError(
            f"There must be exactly 1 link in common for nodes. Regex {node1_name_regex} and {node2_name_regex}\n retrieved link {link_target} intersection"
        )
    start_capture(server, project, link_target)


def get_node_links(server, project, node_id: str) -> Dict[str, Any]:
    r = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node_id}/links",
        auth=(server.user, server.password),
    )
    r.raise_for_status()
    return r.json()


def get_connected_nodes(gns3fy_proj: gns3fy.Project, node_id: str) -> List[str]:
    """

    :param gns3fy_proj:
    :param node_id:
    :return: list of nodes'id of the nodes connected to the node with @node_id
    """
    gns3fy_proj.get()
    node: gns3fy.Node = gns3fy_proj.get_node(node_id=node_id)
    node.get_links()
    # print(node.links)
    id_connected_nodes = []
    for link in node.links:
        # print(f"search in {link}")
        if link.nodes[0]["node_id"] == node_id:
            id_connected_nodes.append(link.nodes[1]["node_id"])
        elif link.nodes[1]["node_id"] == node_id:
            id_connected_nodes.append(link.nodes[0]["node_id"])
    return id_connected_nodes


def get_connected_switch(
    gns3fy_proj: gns3fy.Project, node_id: str
) -> List[gns3fy.Node]:
    connected_switches: List[gns3fy.Node] = []
    id_connected = get_connected_nodes(gns3fy_proj, node_id)
    gns3fy_proj.get()
    for id in id_connected:
        node_obj: gns3fy.Node = gns3fy_proj.get_node(node_id=id)
        if "openvswitch" in node_obj.name.lower():
            connected_switches.append(node_obj)
    return connected_switches


def get_node_occupied_free_adapters(
    gns3fy_node: gns3fy.Node = None,
    node_id: str = None,
    gns3fy_proj: gns3fy.Project = None,
) -> Tuple[Set[int], Set[int]]:
    """
    Get occupied/free adapters of node gns3fy_node
    :param gns3fy_node:
    :return: set of occupied adapters, set of free adapters
    """
    if node_id is not None and gns3fy_node is not None:
        raise ValueError(
            f"gns3fy_node or node_id must be None.\nCurrently {gns3fy_node}, {node_id}"
        )
    if node_id is not None:
        gns3fy_node = gns3fy_proj.get_node(node_id=node_id)

    gns3fy_node.get_links()
    occupied_adapters = set()
    all_adapters = set(p["adapter_number"] for p in gns3fy_node.ports)

    for link_node_a, link_node_b in [link.nodes for link in gns3fy_node.links]:
        if link_node_a["node_id"] == gns3fy_node.node_id:
            occupied_adapters.add(link_node_a["adapter_number"])
        if link_node_b["node_id"] == gns3fy_node.node_id:
            occupied_adapters.add(link_node_b["adapter_number"])
    return occupied_adapters, set(all_adapters.difference(occupied_adapters))


def wait_specific_log(
    server,
    project,
    node_id: str,
    log_to_wait: list[str],
    match_mode: str,
    window_size: int = 50,
) -> Optional[str]:
    """

    :param server:
    :param project:
    :param node_id:
    :param log_to_wait:
    :param match_mode: can be all (wait until all strings in log_to_wait are found in the logs)
    or 'any' (wait until any of the string in log_to_wait is found in the logs )
    :param window_size: monitor the window_size last characters in the logs
    :return: when the condition (match_mode) is true, return the window_size last characters of the logs.
    :return: None when the expected log did not come (possible container stopped)
    """
    possible_match_mode = ["all", "any"]
    if match_mode not in possible_match_mode:
        raise ValueError(f"{match_mode=}. While {possible_match_mode=}")

    container: docker.client.DockerClient = get_container(server, project, node_id)
    # print(f"waiting container log {log_to_wait} from {container}", end=" ")
    logs = container.logs(follow=True, stream=True, since=int(time.time()))
    window = "_" * window_size
    s_time = datetime.datetime.now()
    for log in logs:
        log_char = log.decode("utf-8")
        window = window[1:] + log_char
        # print("reading logs", window)
        if match_mode == "any":
            for searched in log_to_wait:
                if searched in window:
                    return window
        elif match_mode == "all":
            all_in = True
            for searched in log_to_wait:
                if searched not in window:
                    all_in = False
                    break
            if all_in:
                # print(f"{searched} line found", i ,f"##{window}##", end="", flush=True)
                time_delta = datetime.datetime.now() - s_time
                print(f" waited {time_delta.seconds} seconds")
                return window
    print(f"Error, log never received, the container may have stoped {window=}")
    return None


def get_node_ip(
    server, project, node_name: str = "", node_id: str = ""
) -> Optional[str]:
    """
    choose between node_id or node_name to select the node.
    Only works witch Docker container nodes
    :param server:
    :param project:
    :param node_name:
    :param node_id:
    :return: a string that is the ip of the node or a string with error if getting ip failed
    """
    if (node_name == "" and node_id == "") or (node_name != "" and node_id != ""):
        raise ValueError(
            f"Exactly one of the two arguments node_name or node_id must be defined"
        )
    if node_id != "":
        node: gns3fy.Node = project.gns3fy_proj.get_node(node_id=node_id)
    elif node_name != "":
        node: gns3fy.Node = project.gns3fy_proj.get_node(name=node_name)
    else:
        raise ValueError(
            f"Exactly one of the two arguments node_name or node_id must be defined"
        )
    # print(node)
    if node.node_type == "qemu":
        ip = get_node_ip_from_qemu(server, project, node.node_id)
        time.sleep(0.5)
        return ip
    elif node.node_type == "docker":
        ret_code, ip = get_ip_by_gns3_api(
            server, project, Item(node.name, node.node_id)
        )
        if ret_code == 0:
            return ip
        return get_node_ip_from_docker(server, project, node.node_id, node_name)


def get_node_ip_from_docker(server, project, node_id: str, node_name: str) -> str:
    docker_client = docker.from_env()
    container: docker.client.DockerClient = docker_client.containers.get(
        get_node_docker_container_id(server, project, node_id)
    )
    output = container.exec_run(f"cat /etc/network/interfaces")
    if "address " not in output.output.decode():
        print(
            f"error while searching node ip address (node {node_id}{node_name})\n{output.output.decode()}"
        )
    else:
        return output.output.decode().split("address ")[1].split("\n")[0].strip()


def get_node_ip_from_qemu(server, project, node_id) -> str:
    """

    :param server:
    :param project:
    :param node_id:
    :return: ip (as str) of the fist inet ip that does not end with 1 (gateway) or 255 (broadcast)
    """
    hostname, port = get_node_telnet_host_port(server, project, node_id)
    ipv4_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"

    with Telnet(hostname, port) as tn:
        if telnet_login(tn) == 0:
            tn.write(b"\nip a s\n")
            out = tn.expect([b":~$"], timeout=10)
            ip_a_s_output = out[2].decode("utf-8").split("\n")
            for inet_line in (inet for inet in ip_a_s_output if " inet " in inet):
                # Find all matches in the input string
                matches = re.findall(ipv4_pattern, inet_line)
                # Extract the last digit from each match, return if != 1 or 255
                for ip in matches:
                    if ip.split(".")[-1] != "1" and ip.split(".")[-1] != "255":
                        return ip
        else:
            ip_a_s_output = "unknown, login failed"
    return f"error while searching node ip address (node {node_id})\n{ip_a_s_output}"


def stop_capture_all_iot_links(
    server,
    project,
    switches_pattern: Pattern = re.compile("openvswitch.*", re.IGNORECASE),
    iot_pattern: Pattern = re.compile("mqtt-device.*|coap-device.*", re.IGNORECASE),
) -> None:
    """Stop packet capture on each IoT device."""
    switches = get_nodes_id_by_name_regexp(server, project, switches_pattern)
    if switches:
        print(f"found {len(switches)} switches")
        for sw in switches:
            print(f"Finding links in switch {sw.name}... ", end="", flush=True)
            links = get_links_id_from_node_connected_to_name_regexp(
                server, project, sw.id, iot_pattern
            )
            if links:
                print(f"{len(links)} found")
                for lk in links:
                    print(
                        f"\t Stopping capture in link {lk.name}... ", end="", flush=True
                    )
                    stop_capture(server, project, [lk.id])
                    print("OK")
            else:
                print("0 links, skipping.")
        time.sleep(0.3)


def get_ip_by_gns3_api(
    server: Server, project: ProjectGNS3, node: Item
) -> tuple[int, str]:
    """

    Args:
        server:
        project:
        node_id:

    Returns: tuple (int, str) int is 0 or 1
    (0, ip address found or)
    (1, error msg)
    """
    req = requests.get(
        f"http://{server.addr}:{server.port}/v2/projects/{project.id}/nodes/{node.id}/files/etc/network/interfaces",
        auth=(server.user, server.password),
    )
    if not req.ok:
        return (
            1,
            f"[check_ip] Ignoring  {node.name}:\t{req.status_code} {req.reason} /etc/network/interfaces",
        )
    # ignore comments
    ifaces = "\n".join(
        filter(lambda l: not l.strip().startswith("#"), req.text.split("\n"))
    )
    match = re.search(r"address\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", ifaces)
    if match:
        return (0, match.group(1))
    else:
        return (1, f"[check_ip] Searching {node.name}:\tNo matches")


def check_ipaddrs(server: Server, project: ProjectGNS3):
    """Check for duplicated addresses in the project."""
    nodes = get_all_nodes(server, project)
    found_addrs = defaultdict(lambda: [0, []])
    for node in nodes:
        item_node = Item(node["name"], node["node_id"])
        ret_code, ip_or_errmsg = get_ip_by_gns3_api(server, project, item_node)
        if ret_code != 0:
            print(ip_or_errmsg)
        else:
            addr = ip_or_errmsg
            found_addrs[addr][0] += 1
            found_addrs[addr][1].append(node["name"])
            print(f"[check_ip] Searching {node['name']}:\t{addr}")

    duplicates = {k: v for k, v in found_addrs.items() if v[0] > 1}
    if duplicates:
        raise ValueError(f"Duplicated ip addresses found: {duplicates}")


def telnet_login(tn: Telnet, quiet: bool = True, node_name: str = "") -> int:
    """

    :param tn:
    :param quiet:
    :param node_name: Optional argument: name printed as error msg if login failed
    :return: 1 if error, 0 if login success
    """
    print("router login...", end="")
    tn.write(b"\n")
    out = tn.expect([b" login:", b"vyos@"], timeout=120)

    if out[0] == -1:
        str_to_print = "login impossible. Will lead to errors for this node"
        if node_name != "":
            str_to_print += " " + node_name
        print(str_to_print)
        return 1
    # if a session is already open (login already done)
    elif out[0] == 1:
        print("already logged in")
        return 0
    if not quiet:
        print(out[2].decode("utf-8").split("\n")[-1])

    tn.write(b"vyos\n")
    out = tn.expect([b"Password:"], timeout=10)
    if not quiet:
        print(out[2].decode("utf-8"))

    tn.write(b"vyos\n")
    out = tn.expect([b"vyos@.*:~\$"], timeout=10)
    if not quiet:
        print(out[0])
        print(out[2].decode("utf-8"))
    print("login successfully")
    return 0


def install_vyos_image_on_node(
    hostname: str, telnet_port: int, pre_exec: Optional[str] = None
) -> None:
    """Perform VyOS installation steps.

    pre_exec example:
    pre_exec = "konsole -e telnet localhost 5000"
    """
    if pre_exec:
        import subprocess
        import shlex

        pre_proc = subprocess.Popen(shlex.split(pre_exec))
    with Telnet(hostname, telnet_port) as tn:
        if telnet_login(tn) != 0:
            if pre_exec:
                pre_proc.kill()

            return

        tn.write(b"install image\n")
        out = tn.expect([b"Would you like to continue\? \(Yes/No\)"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"Yes\n")
        out = tn.expect([b"Partition \(Auto/Parted/Skip\)"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"Auto\n")
        out = tn.expect([b"Install the image on"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"\n")
        out = tn.expect([b"Continue\? \(Yes/No\)"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"Yes\n")
        out = tn.expect([b"How big of a root partition should I create"], timeout=30)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"\n")
        out = tn.expect([b"What would you like to name this image"], timeout=30)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"\n")
        out = tn.expect([b"Which one should I copy to"], timeout=30)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"\n")
        out = tn.expect([b"Enter password for user 'vyos':"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"vyos\n")
        out = tn.expect([b"Retype password for user 'vyos':"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"vyos\n")
        out = tn.expect(
            [b"Which drive should GRUB modify the boot partition on"], timeout=10
        )
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"\n")
        out = tn.expect([b"vyos@vyos:~\$"], timeout=30)
        print(out[0])
        print(out[2].decode("utf-8"))

        time.sleep(2)
        tn.write(b"poweroff\n")
        out = tn.expect([b"Are you sure you want to poweroff this system"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"y\n")
        time.sleep(2)

    if pre_exec:
        pre_proc.kill()


def configure_vyos_image_on_node(
    hostname: str,
    telnet_port: int,
    path_script: Path,
    pre_exec: Optional[str] = None,
) -> None:
    """Configure VyOS router.

    pre_exec example:
    pre_exec = "konsole -e telnet localhost 5000"
    """
    if pre_exec:
        import subprocess
        import shlex

        pre_proc = subprocess.Popen(shlex.split(pre_exec))

    local_checksum = md5sum_file(str(path_script))

    with open(path_script, "rb") as f:
        config = base64.b64encode(f.read())

    with Telnet(hostname, telnet_port) as tn:
        telnet_login(tn)

        payload = b"echo '" + config + b"' >> config.b64\n"
        tn.write(payload)
        out = tn.expect([b"vyos@vyos:~\$"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"base64 --decode config.b64 > config.sh\n")
        out = tn.expect([b"vyos@vyos:~\$"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"md5sum config.sh\n")
        out = tn.expect([re.compile(r"[0-9a-f]{32}  config.sh".encode("utf-8"))], 5)
        if out[0] == -1:
            warnings.warn("Error generating file MD5 checksum.", RuntimeWarning)
            return
        uploaded_checksum = out[1].group().decode("utf-8").split()[0]

        if uploaded_checksum != local_checksum:
            warnings.warn("Checksums do not match.", RuntimeWarning)
        else:
            print("Checksums match.")

        tn.write(b"chmod +x config.sh\n")
        out = tn.expect([b"vyos@vyos:~\$"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"./config.sh\n")
        out = tn.expect([b"Done"], timeout=60)
        print(out[0])
        print(out[2].decode("utf-8"))
        out = tn.expect([b"vyos@vyos:~\$"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"poweroff\n")
        out = tn.expect([b"Are you sure you want to poweroff this system"], timeout=10)
        print(out[0])
        print(out[2].decode("utf-8"))

        tn.write(b"y\n")
        time.sleep(2)

    if pre_exec:
        pre_proc.kill()


def wait_ping_answering(
    server,
    project,
    id_node_sending_ping,
    target_ip: str,
    open_konsole: bool = True,
    ping_timeout: int = 120,
) -> int:
    """
    wait ping_timeout sec for node to be able to ping given ip address
    :return 0 if ping was received as expected, 2 if login to router was impossible, 1 else
    """
    if target_ip.find("error") >= 0:
        print(f"{target_ip=}, wait_ping_answering impossible")
        return 1
    if project.gns3fy_proj.get_node(node_id=id_node_sending_ping).node_type == "docker":
        # max_retry = ping_timeout // 3 : If failing, ping response takes about 3 more times to come
        return wait_ping_answering_container(
            server, project, id_node_sending_ping, target_ip, ping_timeout // 3
        )

    hostname, port = get_node_telnet_host_port(server, project, id_node_sending_ping)
    return_code = 1
    if open_konsole:
        import subprocess
        import shlex

        pre_proc = subprocess.Popen(shlex.split(f"konsole -e telnet {hostname} {port}"))

    with Telnet(hostname, port) as tn:
        if (
            telnet_login(
                tn,
                node_name=project.gns3fy_proj.get_node(
                    node_id=id_node_sending_ping
                ).name,
            )
            != 0
        ):
            return 2

        payload = b"/usr/bin/ping " + target_ip.encode() + b"\n"
        print(f"{payload=}")
        tn.write(payload)
        time.sleep(5)
        tn.write(b"\n")
        print(tn.read_until(target_ip.encode(), timeout=5).decode("utf-8"))
        out = tn.expect([b".* time=.* ms"], timeout=ping_timeout)
        line_answer = out[2].decode("utf-8").replace("\n", "")
        if " time=" in line_answer:
            print(f"router {id_node_sending_ping} can ping address {target_ip}")
            return_code = 0
        else:
            print(
                f"router {id_node_sending_ping} failed to ping {target_ip}: {line_answer}",
                flush=True,
            )
        # send CTRL+C signal
        tn.write(b"\x03")
        time.sleep(1)

    if open_konsole:
        pre_proc.kill()

    return return_code


def wait_ping_answering_container(
    server, project, node_id, ip_address, max_retry: int
) -> int:
    container = get_container(server, project, node_id)
    ping_retry = 0
    max_retry = int(max_retry)
    print(f"Waiting ping answer from {ip_address}", end=" ")
    while True:
        try:
            # Run the ping command inside the Docker container
            result = container.exec_run(
                ["ping", "-c", "1", ip_address], stdout=True, stderr=True
            )

            # Check if the ping was successful (return code 0)
            if result.exit_code == 0:
                print("success")
                return result.exit_code
            else:
                ping_retry += 1
                if ping_retry >= max_retry:
                    print(result.output.decode())
                    print("ping fail")
                    return 1
                time.sleep(0.5)  # Wait for 0.5 second before retrying
                if ping_retry % 3 == 0:
                    print(f"{max_retry - ping_retry} ", end=" ")

        except docker.errors.APIError as e:
            print(f"Error executing command in container: {e}")
            break


def background(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, **kwargs)

    return wrapped


@background
def configure_router(
    server: Server, project: ProjectGNS3, router_node: Item, config_file: Path
):
    print(f"Installing {router_node.name}")
    d_ss = datetime.datetime.now()
    hostname, port = get_node_telnet_host_port(server, project, router_node.id)
    terminal_cmd = f"konsole -e telnet {hostname} {port}"
    start_node(server, project, router_node.id)
    install_vyos_image_on_node(hostname, port, pre_exec=terminal_cmd)
    # time to close the terminals, else Telnet throws EOF errors
    time.sleep(10)
    print(f"Configuring {router_node.name} with {config_file}")
    start_node(server, project, router_node.id)
    configure_vyos_image_on_node(hostname, port, config_file, pre_exec=terminal_cmd)
    time.sleep(10)
    print(
        f"router {router_node.name} took {(datetime.datetime.now() - d_ss).seconds} to be configured"
    )


def configure_multiple_routers(server, project, add_routers: list[str]):
    """

    :param server:
    :param project:
    :param add_routers: list with exact names of routers to configure
    :return:
    """
    routers_nodes = get_nodes_id_by_name_regexp(
        server, project, re.compile("VyOS1.3.0.*", re.IGNORECASE)
    )
    print(f"router_nodes {routers_nodes}")
    print(f"Going to configure {add_routers}")
    routers_config_mapping = {
        # backbone
        "VyOS1.3.0-1": Path("../router/backbone/router_north.sh"),
        "VyOS1.3.0-2": Path("../router/backbone/router_west.sh"),
        "VyOS1.3.0-3": Path("../router/backbone/router_east.sh"),
        # west zone
        "VyOS1.3.0-4": Path("../router/locations/router_loc1.sh"),
        "VyOS1.3.0-5": Path("../router/locations/router_loc2.sh"),
        "VyOS1.3.0-6": Path("../router/locations/router_loc3.sh"),
        "VyOS1.3.0-7": Path("../router/locations/router_loc4.sh"),
        # east zone
        "VyOS1.3.0-8": Path("../router/locations/router_loc5.sh"),
        "VyOS1.3.0-9": Path("../router/locations/router_loc6.sh"),
        "VyOS1.3.0-10": Path("../router/locations/router_loc7.sh"),
    }
    for router in routers_nodes:
        if router.name in add_routers:
            print(f"Install {router.name}")
            configure_router(
                server, project, router, routers_config_mapping[router.name]
            )
        else:
            print(f"Skip install {router.name}")


def check_connectivity(
    server,
    project,
    regex_set1: re.Pattern,
    regex_set2: re.Pattern,
    open_konsole_arg: bool = False,
    ping_timeout_arg: int = 120,
) -> None:
    """
    Make sure all nodes with name matching regex_set1 can ping all nodes matching regex_set2.
    if ping from node_in_set1 to node_in_set2 does not work, try ping from node_in_set2 to node_in_set1
    :param server:
    :param project:
    :param regex_set1:
    :param regex_set2:
    :return:
    """
    mqtt_brokers: list[dict[str, Any]] = get_nodes_id_by_name_regexp(
        server, project, regex_set1, return_items=False
    )
    brokers_id_ip: dict[str, str] = {
        broker["node_id"]: get_node_ip(server, project, node_id=broker["node_id"])
        for broker in mqtt_brokers
    }

    for router_id in (
        node_item.id
        for node_item in get_nodes_id_by_name_regexp(server, project, regex_set2)
    ):
        for broker_id, broker_ip in brokers_id_ip.items():
            print(f"from router {router_id}, try ping broker at {broker_ip}")
            router_ping = wait_ping_answering(
                server,
                project,
                router_id,
                broker_ip,
                open_konsole=open_konsole_arg,
                ping_timeout=ping_timeout_arg,
            )
            if router_ping != 0:
                if router_ping == 2:
                    break
                router_ip = get_node_ip(server, project, node_id=router_id)
                if router_ip is None:
                    continue
                print(f"from broker at {broker_ip}, try ping router at {router_ip}")
                wait_ping_answering(server, project, broker_id, router_ip)


def reverse_ping_if_failure(
    server, project, iot_node_id, dns_id, ip_to_node: dict[str, gns3fy.Node]
) -> int:
    """

    :param server:
    :param project:
    :param iot_node_id:
    :param dns_id:
    :param ip_to_node: [ip_mqtt_broker, gns3fy.Node of mqtt broker]
    :return: 0 if IoT node succeeded to ping its mqtt broker, 1 else
    """
    success = ["[  ping   ] pinging", "[telemetry] sending to ", "[telemetry] zZzzZZz"]
    fail_nds = ["failure in name resolution"]
    fail_ping_target = [
        ", 100% packet loss,",
        "Redirect Host(New nexthop:",
        "Destination Host Unreachable",
    ]
    possible_logs = success + fail_nds + fail_ping_target
    ip_node_failing_ping = None
    pattern_str = (
        "("
        + "|".join((re.escape(possible_log) for possible_log in possible_logs))
        + ")"
    )
    log = wait_specific_log(
        server, project, iot_node_id, possible_logs, "any", window_size=200
    )
    if log is None:
        log = fail_ping_target[0]
    log_match = re.search(pattern_str, log).group()
    print(f"{log_match=}")

    if log_match in success:
        return 0
    if log_match in fail_nds:
        ip_node_failing_ping = get_node_ip(server, project, node_id=iot_node_id)
        ret = wait_ping_answering(
            server, project, dns_id, ip_node_failing_ping, open_konsole=False
        )
        print(f"return code ping dns to iot: {ret}")
        log = fail_ping_target[0]
        log_match = re.search(pattern_str, log).group()

    if log_match in fail_ping_target:
        ipv4_pattern = r"PING .*\b(?:\d{1,3}\.){3}\d{1,3}\b"
        all_ips = re.findall(ipv4_pattern, log)
        if len(all_ips) > 0:
            ip_of_node_to_ping = all_ips[0].split("(")[-1]
            print(f"\n{log=},\n{ip_of_node_to_ping=}")
            id_broker_related_to_device = ip_to_node[ip_of_node_to_ping].node_id
            ret = wait_ping_answering(
                server,
                project,
                id_broker_related_to_device,
                get_node_ip(server, project, node_id=iot_node_id),
            )
            print(f"return code ping MQTT broker to iot device: {ret}")
    node_log = wait_specific_log(
        server, project, iot_node_id, success, "any", window_size=50
    )
    if node_log is None:
        return 1
    str_print = node_log.replace("\n", " ")
    print(f"Reverse ping executed: node log match: {str_print}")
    return 0
