# ip of mqtt brokers

- 192.168.2.1
- 192.168.3.1
- 192.168.0.4


# command line executed during attack
## arguments to append to the nmap scan 

`./nmap -Pn -oG ips.txt 192.168.18-20.10-150 --max-rate 0.7 -p 22`

## arguments to append to the hydra bruteforce on ssh: 

`hydra/hydra -o success.txt -M ssh_ips.txt ssh -f -L u.txt -P p.txt -t 2`

## arguments when lauching DDoS: 

`mqttsa -fc 100 -fcsize 10 -sc 2400 192.168.2.1`

# legitimate and malicious (DDoS) ips

### legitimate ips

450 IoT publishing MQTT messages

192.168.18.10 to 192.168.18.234
192.168.19.10 to 192.168.19.234

### compromised IoT ips launching DDoS

60 compromised IoT

- 192.168.18.10
- 192.168.18.104
- 192.168.18.109
- 192.168.18.115
- 192.168.18.118
- 192.168.18.119
- 192.168.18.125
- 192.168.18.126
- 192.168.18.128
- 192.168.18.131
- 192.168.18.132
- 192.168.18.135
- 192.168.18.136
- 192.168.18.140
- 192.168.18.144
- 192.168.18.146
- 192.168.18.147
- 192.168.18.31
- 192.168.18.55
- 192.168.18.56
- 192.168.18.57
- 192.168.18.58
- 192.168.18.73
- 192.168.18.74
- 192.168.18.75
- 192.168.18.77
- 192.168.18.78
- 192.168.18.88
- 192.168.18.96
- 192.168.18.99
- 192.168.19.105
- 192.168.19.106
- 192.168.19.107
- 192.168.19.110
- 192.168.19.112
- 192.168.19.116
- 192.168.19.117
- 192.168.19.124
- 192.168.19.133
- 192.168.19.139
- 192.168.19.141
- 192.168.19.144
- 192.168.19.148
- 192.168.19.22
- 192.168.19.24
- 192.168.19.26
- 192.168.19.33
- 192.168.19.38
- 192.168.19.47
- 192.168.19.49
- 192.168.19.51
- 192.168.19.53
- 192.168.19.60
- 192.168.19.62
- 192.168.19.64
- 192.168.19.69
- 192.168.19.71
- 192.168.19.76
- 192.168.19.78
- 192.168.19.91


# number of packets
```text
capinfos OpenvSwitch-24_2-0_to_sinetstream-zookeeper-1_0-0.pcap 
File name:           OpenvSwitch-24_2-0_to_sinetstream-zookeeper-1_0-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   26 k
File size:           2523 kB
Data size:           2107 kB
Capture duration:    49052.260802 seconds
First packet time:   2024-07-23 22:47:07.393000
Last packet time:    2024-07-24 12:24:39.653802
Data byte rate:      42 bytes/s
Data bit rate:       343 bits/s
Average packet size: 81.05 bytes
Average packet rate: 0 packets/s
SHA256:              9580271d0e3fd6cd35cb2a61421df1e07442e1ff34777df832cfbc99c15b3a4e
RIPEMD160:           8525ccd55e3cb0aa0e3ba19d76d63eb6887097fc
SHA1:                067223832397daf8c0ed579d0d147b723e8c8997
Strict time order:   True
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 26000
```
===============
```text
capinfos OpenvSwitch-24_4-0_to_sinetstream-connect-kafka-1_0-0.pcap 
File name:           OpenvSwitch-24_4-0_to_sinetstream-connect-kafka-1_0-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   9533 k
File size:           2827 MB
Data size:           2675 MB
Capture duration:    49052.090730 seconds
First packet time:   2024-07-23 22:47:08.831569
Last packet time:    2024-07-24 12:24:40.922299
Data byte rate:      54 kBps
Data bit rate:       436 kbps
Average packet size: 280.63 bytes
Average packet rate: 194 packets/s
SHA256:              df395119bd70d26c9b5c7cdd808a140ed4c2a1a3b5c86ad4835b0e9c33daee17
RIPEMD160:           04100a6b45d21d26d9d1c33d8db88061bb407577
SHA1:                3282a7b1c51658b22b07b2207fc886c957503321
Strict time order:   False
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 9533058
```
===============
```text
capinfos VyOS130-1_1-0_to_VyOS130-2_1-0.pcap 
File name:           VyOS130-1_1-0_to_VyOS130-2_1-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   18 M
File size:           3504 MB
Data size:           3208 MB
Capture duration:    49054.289524 seconds
First packet time:   2024-07-23 22:47:04.708480
Last packet time:    2024-07-24 12:24:38.998004
Data byte rate:      65 kBps
Data bit rate:       523 kbps
Average packet size: 173.48 bytes
Average packet rate: 377 packets/s
SHA256:              002521af0af43ea87399e043bcf4c50038ccac13078fd5c8ef406e82a5fc0ba5
RIPEMD160:           8840a477ad814de0a96bb354b59dde54d2fc3e0d
SHA1:                eed856a9a59c977575546dbaa374a8b4f5f42fdc
Strict time order:   False
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 18497286
```
