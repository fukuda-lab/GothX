from constants import (
    ENV_SLEEP_TIME,
    ENV_SLEEP_TIME_SD,
    MQTT_BROKER_ADDR,
    NEIGH_BROKER_PLAIN_NAME,
    MQTT_CLOUD_TLS_NAME,
    ENV_DATASET_COLUMNS,
    STEEL_BROKER_AUTH_NAME,
    ACTIVE_TIME,
    INACTIVE_TIME,
    choose_random_columns_in_dataset,
)
import random


PROJECT_NAME = "config_sinetstream_max_iot_DDoS_25p"

iot_devices: dict[str, dict[str, str]] = {}
########################################
# configuration of legitimate actions  #
########################################

# for iot devices iotsim-domotic-monitor-bis, dataset have 24 columns
# all values >=23 in ENV_DATASET_COLUMNS are ignored
for idx_iot_device in range(1, 15 * 15 + 1):
    iot_devices[f"iotsim-domotic-monitor-bis-{idx_iot_device}"] = {
        ENV_SLEEP_TIME: str(int(1 + 0.5 * idx_iot_device)),
        ENV_SLEEP_TIME_SD: "0",
        ENV_DATASET_COLUMNS: choose_random_columns_in_dataset(24),
        MQTT_BROKER_ADDR: NEIGH_BROKER_PLAIN_NAME[0],
    }

# for iot devices iotsim-cooler-motor, dataset have 5 columns
# all values >=4 in ENV_DATASET_COLUMNS are ignored
for cooler_index in range(1, 3 * 15):
    iot_devices[f"iotsim-cooler-motor-{cooler_index}"] = {
        ENV_SLEEP_TIME: str(int(1 + 0.5 * cooler_index)),
        ENV_DATASET_COLUMNS: choose_random_columns_in_dataset(4),
        MQTT_BROKER_ADDR: STEEL_BROKER_AUTH_NAME[0],
    }
for pred_index in range(1, 4 * 15):
    iot_devices[f"iotsim-predictive-maintenance-{pred_index}"] = {
        ENV_SLEEP_TIME: str(int(20 + pred_index * 0.5)),
        ENV_SLEEP_TIME_SD: "1",
        ENV_DATASET_COLUMNS: choose_random_columns_in_dataset(15),
    }
for cooler_index in range(3 * 15, 4 * 15 + 1):
    iot_devices[f"iotsim-cooler-motor-{cooler_index}"] = {
        ENV_SLEEP_TIME: str(int(40 + 0.5 * cooler_index)),
        ENV_DATASET_COLUMNS: choose_random_columns_in_dataset(4),
        MQTT_BROKER_ADDR: MQTT_CLOUD_TLS_NAME[0],
        "TLS": True,
    }
for pred_index in range(4 * 15, 11 * 15 + 1):
    iot_devices[f"iotsim-predictive-maintenance-{pred_index}"] = {
        ENV_SLEEP_TIME: str(int(35 + pred_index * 0.5)),
        ENV_SLEEP_TIME_SD: "1",
        ENV_DATASET_COLUMNS: choose_random_columns_in_dataset(15),
        MQTT_BROKER_ADDR: MQTT_CLOUD_TLS_NAME[0],
        "TLS": True,
    }
"""
define the name of the kafka topic that will receive all registered mqtt topics
"""
kafka_topic = "kafka-topic"

"""
define which mqtt topic from a given mqtt broker will be copied in the kafka broker (through the connect-kafka node)
e.g.: 
read from mqtt broker node with name broker1, topics "topic-10" and "topic-11"
read from mqtt broker node with name broker2, topic "topic-20"
{
    "broker1": ["topic-10", "topic-11"],
    "broker2": ["topic-20"],
}
if the mqtt topic does not exist on the specified mqtt broker, the worker is created but will have no effect
"""
mqtt_topics_domotic = list(
    (
        f"domotic/iotsim-domotic-monitor-bis-{i}"
        for i in range(
            1, len(list(device for device in iot_devices.keys() if "domotic" in device))
        )
    )
)
mqtt_topics_vibration = list(
    (
        f"vibration/cooler-iotsim-cooler-motor-{i}"
        for i in range(
            1, len(list(device for device in iot_devices.keys() if "cooler" in device))
        )
    )
)

mqtt_topics_to_connect = {
    "iotsim-mqtt-broker-1.6-1": mqtt_topics_domotic,
    "iotsim-mqtt-broker-1.6-auth-1": mqtt_topics_vibration,
}

########################################
# configuration of attack actions  #
########################################

"""
if DDoS_only then IoT nodes are considered as compromised. 
All steps about initial compromission, ports scan, credentials bruteforce and payload transfert are skipped
The only 3 attack settings taken into account (defined bellow) are
- nodes_with_ssh (username and password are required but have no effect)
- mqttsa_args
- target_mqtt_broker_ip
"""
DDoS_only = True
"""
define which device will have ssh open and be part of the DDoS
for each tuple (node_name, username, password)
ssh server is open on node having node_name (on port 22)
a user is created with the given username and password (possibly found using hydra bruteforce dictionary later)
"""

# nodes_with_ssh: list[tuple[str, str, str]] = [
#     ("iotsim-domotic-monitor-bis-1", "test", "password"),
#     ("iotsim-domotic-monitor-bis-2", "administrator", "password"),
#     ("iotsim-domotic-monitor-bis-3", "test", "password"),
#     ("iotsim-domotic-monitor-bis-4", "admin", "1234"),
#     ("iotsim-domotic-monitor-bis-5", "admin", "123456"),
#     ("iotsim-domotic-monitor-bis-6", "test", "1234"),
#     ("iotsim-domotic-monitor-bis-7", "man", "superman"),
#     ("iotsim-cooler-motor-1", "guest", "password"),
#     ("iotsim-cooler-motor-2", "toor", "rockyou"),
#     ("iotsim-cooler-motor-3", "toor", "qwerty"),
#     ("iotsim-cooler-motor-4", "guest", "000000"),
#     ("iotsim-cooler-motor-5", "guest", "111111"),
#     ("iotsim-cooler-motor-6", "guest", "111111"),
# ]

proportion_devices_launching_ddos = 25 / 100
shuffled_iot_names = list(iot_devices.keys())
random.shuffle(shuffled_iot_names)
print(shuffled_iot_names)
nodes_with_ssh = list(
    (node_name, "placeholder", "placeholder")
    for node_name in shuffled_iot_names[
        : int(proportion_devices_launching_ddos * len(shuffled_iot_names))
    ]
)


"""
define timing (in seconds) between different attack steps
"""

w_time_legitimate_only_before_attack = 60 * 9
w_time_cve_exploitation_openrevshell = 60 * 30
w_time_openrevshell_toolstransfert = 60 * 5
w_time_toolstransfert_nmap = 60 * 60
w_time_nmap_hydra = 60 * 60
w_time_hydra_mqttsa_scp = 60 * 60 * 2
w_time_scp_coordinated_launch = 60 * 60 * 5
w_time_end_ddos_to_end_scenario = 60 * 2

# arguments to append to the nmap scan `./nmap -Pn -oG ips.txt <nmap_args>`
# for details see official nmap documentation https://nmap.org/book/man-briefoptions.html
# this step of the attack is the discovery (trying to find if any ip has ssh port open)
nmap_args = "192.168.18-20.10-150 --max-rate 0.7 -p 22"

# arguments to append to the hydra bruteforce on ssh: `hydra/hydra -o success.txt -M ssh_ips.txt ssh <hydra_args>`# use -f to stop attack on IP x when one login/pwd found for IP x,
#  use -F to stop attack on all IPs when one login/pwd has been found for any IP
# for details see official hydra repo https://github.com/vanhauser-thc/thc-hydra/blob/master/hydra.1
# p.txt and psmall.txt are available passwords lists
hydra_args = "-f -L u.txt -P p.txt -t 2"

# define maximum time during which credentials bruteforce is done (with hydra).
# After this time, found credentials are used, if there is none, attack stops
max_time_creds_bruteforce = 60 * 60 * 8  # seconds

# arguments when lauching mqttsa: `mqttsa <mqttsa_args> <target_mqtt_broker_ip>`
# for details seee official mqttsa repo https://github.com/stfbk/mqttsa?tab=readme-ov-file
# -fc flag launches SlowITe Dos: https://www.researchgate.net/publication/341563324_SlowITe_a_Novel_Denial_of_Service_Attack_Affecting_MQTT
mqttsa_args = "-fc 100 -fcsize 10 -sc 2400"

# ip of the mtqq broker that is targeted by mqttsa tool
target_mqtt_broker_ip = "192.168.2.1"  # ip of node mqtt-broker-1.6
# target_mqtt_broker_ip = "192.168.0.4"  # ip of node iotsim-mqtt-broker-tls-1
# target_mqtt_broker_ip = "192.168.3.1"  # ip of node iotsim-mqtt-broker-1.6-auth-1

# port use for the reverse shell using nc (from connect-kafa to client-connect)
nc_port = 4444
