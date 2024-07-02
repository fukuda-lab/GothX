# read project configuration file
import configparser
import random

random.seed(1538)

sim_config = configparser.ConfigParser()
with open("../iot-sim.config", "r", encoding="utf-8") as cf:
    # include fake section header 'main'
    sim_config.read_string(f"[main]\n{cf.read()}")
    sim_config = sim_config["main"]

NEIGH_BROKER_PLAIN_NAME = (f"broker.neigh.{sim_config['LOCAL_DOMAIN']}", "192.168.2.1")
STEEL_BROKER_AUTH_NAME = (f"broker.steel.{sim_config['LOCAL_DOMAIN']}", "192.168.3.1")
MQTT_CLOUD_TLS_NAME = (sim_config["MQTT_TLS_BROKER_CN"], "192.168.0.4")
NTP_CLOUD_NAME = (f"ntp.{sim_config['LOCAL_DOMAIN']}", "192.168.0.3")

ENV_SLEEP_TIME = "SLEEP_TIME"
ENV_SLEEP_TIME_SD = "SLEEP_TIME_SD"
ENV_DATASET_COLUMNS = "DATASET_COLUMNS"
MQTT_BROKER_ADDR = "MQTT_BROKER_ADDR"
ACTIVE_TIME = "ACTIVE_TIME"
INACTIVE_TIME = "INACTIVE_TIME"

SINETSTREAM_TEMPLATE_NAMES = (
    "sinetstream-zookeeper",
    "sinetstream-kafka-broker",
    "sinetstream-connect-kafka",
    "sinetstream-client-connect",
)

# passwords that can be discovered using hydra dictionary-based attack (see Dockerfiles/mqtt-connect-kafka/client_connect/tools/p.txt)
IN_DICT_PASSWORDS = (
    "password",
    "password",
    "password",
    "1234",
    "123456",
    "1234",
    "superman",
    "password",
    "rockyou",
    "qwerty",
    "000000",
    "111111",
    "111111"
)
# usernames that can be discovered using hydra dictionary-based attack (see Dockerfiles/mqtt-connect-kafka/client_connect/tools/u.txt)
IN_DICT_USERNAMES = (
    "test",
    "administrator",
    "test",
    "admin",
    "admin",
    "test",
    "man",
    "guest",
    "toor",
    "toor",
    "guest",
    "guest",
    "guest",
)


def choose_random_columns_in_dataset(nb_columns_in_dataset: int, nb_columns_to_choose: int = 0):
    if nb_columns_to_choose < 1 or nb_columns_to_choose > nb_columns_in_dataset:
        nb_columns_to_choose = random.randint(1, nb_columns_in_dataset) // 2 + 1
    return ",".join((str(random.randint(0, nb_columns_in_dataset - 1)) for _ in range(nb_columns_to_choose)))
