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

`mqttsa -fc 100 -fcsize 10 -sc 4800 192.168.2.1`

# legitimate and malicious (DDoS) ips

### legitimate ips

450 IoT publishing MQTT messages

192.168.18.10 to 192.168.18.234
192.168.19.10 to 192.168.19.234

### compromised IoT ips launching DDoS

72 compromised IoT

- 192.168.18.10
- 192.168.18.100
- 192.168.18.104
- 192.168.18.106
- 192.168.18.109
- 192.168.18.115
- 192.168.18.117
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
- 192.168.18.148
- 192.168.18.17
- 192.168.18.19
- 192.168.18.29
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
- 192.168.18.83
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
- 192.168.19.13
- 192.168.19.133
- 192.168.19.139
- 192.168.19.141
- 192.168.19.142
- 192.168.19.144
- 192.168.19.148
- 192.168.19.22
- 192.168.19.24
- 192.168.19.26
- 192.168.19.33
- 192.168.19.38
- 192.168.19.43
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
- 192.168.19.96


# number of packets
```text
capinfos OpenvSwitch-24_2-0_to_sinetstream-zookeeper-1_0-0.pcap
File name:           OpenvSwitch-24_2-0_to_sinetstream-zookeeper-1_0-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   27 k
File size:           2 652 kB
Data size:           2 214 kB
Capture duration:    51710,201830 seconds
First packet time:   2024-07-24 15:07:18,257632
Last packet time:    2024-07-25 05:29:08,459462
Data byte rate:      42 bytes/s
Data bit rate:       342 bits/s
Average packet size: 80,93 bytes
Average packet rate: 0 packets/s
SHA256:              7dcfc6ad9f950dbf06b63dd95faa491b0b9aa279532cacd49dccb90a992dccfa
RIPEMD160:           cec4ef7ca4e2909c37181dbf679b03ff48e9880c
SHA1:                ba3f433f7ed16bc5726164a86d1e489ef5278adb
Strict time order:   True
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 27362
```
===
```text
capinfos OpenvSwitch-24_4-0_to_sinetstream-connect-kafka-1_0-0.pcap
File name:           OpenvSwitch-24_4-0_to_sinetstream-connect-kafka-1_0-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   10 M
File size:           3 147 MB
Data size:           2 983 MB
Capture duration:    51718,045659 seconds
First packet time:   2024-07-24 15:07:16,352999
Last packet time:    2024-07-25 05:29:14,398658
Data byte rate:      57 kBps
Data bit rate:       461 kbps
Average packet size: 292,09 bytes
Average packet rate: 197 packets/s
SHA256:              0d23854bacce7ba8d84190601cad0d37481e839e9bfca58c514c09dc7af4695b
RIPEMD160:           ebff8516dd8246b2d909b7c8fe36f32ae22aad74
SHA1:                309433c37c639ac78b26bf1bdc5cecfb6e0a9210
Strict time order:   False
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 10215529
```
===
```text
capinfos VyOS130-1_1-0_to_VyOS130-2_1-0.pcap
File name:           VyOS130-1_1-0_to_VyOS130-2_1-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   18 M
File size:           3 797 MB
Data size:           3 505 MB
Capture duration:    51715,779201 seconds
First packet time:   2024-07-24 15:07:16,923475
Last packet time:    2024-07-25 05:29:12,702676
Data byte rate:      67 kBps
Data bit rate:       542 kbps
Average packet size: 192,10 bytes
Average packet rate: 352 packets/s
SHA256:              1f3b74a735a29afe5a24def5563bfdf65261bd010d91ab6862609160e46e54f7
RIPEMD160:           e3142a5023dcd15bb53c2f3cb36483cfc2e90b25
SHA1:                07f3446dfca2e564b6eb99cdbd08dce11ae1a833
Strict time order:   False
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 18247565
```
