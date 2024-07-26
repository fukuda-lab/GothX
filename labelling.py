import csv

from collections import defaultdict
from datetime import datetime, timezone
from os import path
from pathlib import Path

NO_IP_FOUND = "no_ip_found"

def is_datetime_between(
    timestamp: datetime, datetime_start: datetime, datetime_end: datetime
):
    # print(datetime_end, datetime_start)
    return datetime_start <= timestamp <= datetime_end


def get_times_ddos(
    path_times: Path,
) -> dict[str, list[tuple[int, int, int, int, int, int, int]]]:
    """

    :param path_times:
    :return: dict with
    keys: gns3_node_name#gns3_node_ip and
    values [(ddos_start), (ddos_end)]
    where ddos_start and ddos_start are of the form (year, month, day, hour, min, sec, millisecond)
    """
    with open(path_times, "r") as f_times:
        for l in f_times:
            if l.find("datetime") < 0:
                continue
            clean_line = l.replace("datetime.datetime", "").replace(
                ", tzinfo=datetime.timezone.utc", ""
            )
            return eval(clean_line)


def get_times(path_times: Path, times_type: str) -> tuple[datetime, datetime]:
    type_start_stop: list[datetime] = []
    with open(path_times, "r") as f_times:
        for l in f_times:
            idx_type = l.find(times_type)
            if idx_type < 0:
                continue
            str_time = " ".join(l[idx_type + len(times_type) :].strip().split(" ")[1:])
            type_start_stop.append(
                datetime.strptime(str_time, "%Y-%m-%d %H:%M:%S.%f%z")
            )
    if len(type_start_stop) != 2:
        raise ValueError(f"{type_start_stop} value len must be 2")
    if type_start_stop[0] > type_start_stop[1]:
        raise ValueError(
            f"{times_type} {type_start_stop[0]} must be before {type_start_stop[1]}"
        )
    return tuple((type_start_stop[0], type_start_stop[1]))


def get_ip_kafka_connect(path_times: Path) -> str:
    nmap_line = "start nmap"
    with open(path_times, "r") as f_times:
        for l in f_times:
            idx_type = l.find(nmap_line)
            if idx_type < 0:
                continue
            return l[idx_type + len(nmap_line) :].strip().split(" ")[0]
    return NO_IP_FOUND


def get_ip_port_src_revshell(path_times: Path) -> tuple[str, str]:
    nmap_line = "revshell"
    with open(path_times, "r") as f_times:
        for l in f_times:
            idx_type = l.find(nmap_line)
            if idx_type < 0:
                continue
            ip_port_list = (
                l[idx_type + len(nmap_line) :].strip().split(" ")[0].split(":")
            )
            if len(ip_port_list) != 2:
                raise ValueError(f"ip_port_src list len must be 2 {ip_port_list=}")
            return tuple(ip_port_list)
    return (NO_IP_FOUND,"-1")

def check_paths(paths_list: list[Path]):
    for path_p in paths_list:
        if not path_p.is_file():
            raise FileNotFoundError(path_p)
        if path_p.suffix != ".csv":
            raise ValueError(f"You did not select a CSV file {path_p}")


# /home/mpoisson/Documents/NII/Manuel/experiments_res/long_big_attack/captures_long_big
base_path = "/home/manuel/Documents/NII/Manuel/gotham-iot-testbed/dataset_details/full_attack_scenario_v2"

path_times = Path(
    f"{base_path}/times_gothX_fullDataset_240724_1432.txt"
)

path_csv_mqtt = Path(f"{base_path}/VyOS130-1_1-0_to_VyOS130-2_1-0_ordered.pcap_Flow.csv")
path_csv_kafka_connect = Path(
    f"{base_path}/OpenvSwitch-24_4-0_to_sinetstream-connect-kafka-1_0-0_ordered.pcap_Flow.csv"
)
csv_paths = [path_csv_mqtt, path_csv_kafka_connect]

check_paths(csv_paths)

# src ip of nmap scan, hydra bruteforce and payload transfert
ip_vulnerable_kafka_connect = get_ip_kafka_connect(path_times)
ip_dst_revshell, port_dst_revshell = get_ip_port_src_revshell(path_times)

is_full_attack_scenario = (ip_vulnerable_kafka_connect != NO_IP_FOUND) and (ip_vulnerable_kafka_connect != NO_IP_FOUND)

ddos_times = get_times_ddos(path_times)

ddos_ip_to_datetimes: dict[str, list[datetime]] = defaultdict(list)
for node_name_and_ip, dates in ddos_times.items():
    for time_tuple in dates:
        datetime_naive = datetime(*time_tuple)
        datetime_aware = datetime_naive.replace(tzinfo=timezone.utc)
        # Format the datetime object
        formatted_date = datetime_aware.strftime("%A %B %d, %Y %Hh%M %S.%f%z sec")

        # Print the result
        print(formatted_date)
        ddos_ip_to_datetimes[node_name_and_ip.split("#")[1]].append(datetime_aware)
    print("==")

if is_full_attack_scenario:
    datetimes_cve_exploitation = get_times(path_times, "cve_2023_25194_exploitation")
    datetimes_revershell = get_times(path_times, "revshell")
    datetimes_scan_ports = get_times(path_times, "nmap")
    datetimes_creds_bruteforce = get_times(path_times, "hydra")
    datetimes_transfert_payload_to_iot = get_times(path_times, "scp transfert file on IoT")

label_cve_exploitation = "cve_exploitation"
label_revshell = "reverse_shell"
label_scan_ports = "scan_ports"
label_creds_bruteforce = "credentials_bruteforce"
label_transfert_payload_to_iot = "transfert_payload_to_iot"
label_ddos = "mqttsa_slowite"
label_normal = "normal"
label_default = "NeedManualLabel"

new_csv_rows: list[list[str]] = []

for path_csv in csv_paths:
    path_labelled_csv = (
        path.splitext(path_csv)[0] + "_labelled" + path.splitext(path_csv_mqtt)[1]
    )
    new_csv_rows = []
    with open(path_csv, "r", newline="", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        headers = next(reader)
        new_csv_rows.append(headers)
        print(headers)
        # Modify the data
        for row in reader:
            # fix case when timestamp is 2024-07-24 01:47:46 instead of 2024-07-24 01:47:46.000000
            if row[6].count(".") == 0:
                row[6] += ".000000"
                print(row[6])
            timestamp = datetime.strptime(row[6] + "+00:00", "%Y-%m-%d %H:%M:%S.%f%z")
            src_ip = row[1]
            src_port = row[2]
            dst_ip = row[3]
            dst_port = row[4]

            if is_full_attack_scenario:
                if (
                    dst_ip == ip_dst_revshell
                    and dst_port == port_dst_revshell
                    and is_datetime_between(timestamp, *datetimes_revershell)
                ):
                    row[-1] = label_revshell

                elif dst_ip == ip_vulnerable_kafka_connect and is_datetime_between(
                    timestamp, *datetimes_cve_exploitation
                ):
                    row[-1] = label_cve_exploitation

                elif src_ip == ip_vulnerable_kafka_connect:
                    # ports scan with nmap
                    if is_datetime_between(timestamp, *datetimes_scan_ports):
                        row[-1] = label_scan_ports
                    # credentials bruteforce with hydra
                    elif is_datetime_between(timestamp, *datetimes_creds_bruteforce):
                        row[-1] = label_creds_bruteforce
                    # transferring payload via scp to compromised IoT
                    elif is_datetime_between(
                        timestamp, *datetimes_transfert_payload_to_iot
                    ):
                        row[-1] = label_transfert_payload_to_iot

            # DDoS labels
            if src_ip in ddos_ip_to_datetimes.keys():
                time_range = ddos_ip_to_datetimes[src_ip]
                if is_datetime_between(timestamp, time_range[0], time_range[1]):
                    row[-1] = label_ddos

            if row[-1] == label_default:
                row[-1] = label_normal
            new_csv_rows.append(row)

    with open(path_labelled_csv, "w", newline="") as label_csv:
        for row in new_csv_rows:
            # print(",".join(row))
            label_csv.write(",".join(row) + "\n")
