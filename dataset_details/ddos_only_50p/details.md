# ip of mqtt brokers

- 192.168.2.1
- 192.168.3.1
- 192.168.0.4

# legitimate MQTT traffic

450 sensors

ip 192.168.18.10-234 and 192.168.19.10-234

| ip mqtt broker dst     | nb of distinct publishers | ip range                             | 
|------------------------|---------------------------|--------------------------------------|
| 192.168.2.1 anon Clear | 225                       | 192.168.18.10-234                    | 
| 192.168.3.1 auth Clear | 103                       | 192.168.19.10-113                    | 
| 192.168.0.4 anon TLS   | 122                       | 192.168.19.54 and 192.168.19.114-234 | 

# compromised IoT launching DDoS

225 distinct ips

- 192.168.18.10
- 192.168.18.100
- 192.168.18.103
- 192.168.18.104
- 192.168.18.105
- 192.168.18.106
- 192.168.18.108
- 192.168.18.109
- 192.168.18.11
- 192.168.18.112
- 192.168.18.113
- 192.168.18.115
- 192.168.18.117
- 192.168.18.119
- 192.168.18.12
- 192.168.18.120
- 192.168.18.121
- 192.168.18.122
- 192.168.18.125
- 192.168.18.126
- 192.168.18.127
- 192.168.18.128
- 192.168.18.13
- 192.168.18.130
- 192.168.18.132
- 192.168.18.134
- 192.168.18.135
- 192.168.18.136
- 192.168.18.137
- 192.168.18.14
- 192.168.18.140
- 192.168.18.143
- 192.168.18.144
- 192.168.18.146
- 192.168.18.147
- 192.168.18.148
- 192.168.18.151
- 192.168.18.158
- 192.168.18.159
- 192.168.18.16
- 192.168.18.160
- 192.168.18.163
- 192.168.18.164
- 192.168.18.166
- 192.168.18.17
- 192.168.18.170
- 192.168.18.174
- 192.168.18.175
- 192.168.18.176
- 192.168.18.178
- 192.168.18.18
- 192.168.18.180
- 192.168.18.183
- 192.168.18.184
- 192.168.18.185
- 192.168.18.188
- 192.168.18.189
- 192.168.18.19
- 192.168.18.192
- 192.168.18.193
- 192.168.18.196
- 192.168.18.197
- 192.168.18.198
- 192.168.18.199
- 192.168.18.20
- 192.168.18.205
- 192.168.18.211
- 192.168.18.212
- 192.168.18.213
- 192.168.18.215
- 192.168.18.216
- 192.168.18.220
- 192.168.18.221
- 192.168.18.222
- 192.168.18.223
- 192.168.18.227
- 192.168.18.229
- 192.168.18.23
- 192.168.18.232
- 192.168.18.233
- 192.168.18.234
- 192.168.18.25
- 192.168.18.29
- 192.168.18.31
- 192.168.18.34
- 192.168.18.35
- 192.168.18.36
- 192.168.18.42
- 192.168.18.44
- 192.168.18.45
- 192.168.18.46
- 192.168.18.47
- 192.168.18.51
- 192.168.18.52
- 192.168.18.54
- 192.168.18.55
- 192.168.18.56
- 192.168.18.57
- 192.168.18.58
- 192.168.18.60
- 192.168.18.65
- 192.168.18.69
- 192.168.18.73
- 192.168.18.74
- 192.168.18.75
- 192.168.18.77
- 192.168.18.78
- 192.168.18.80
- 192.168.18.82
- 192.168.18.83
- 192.168.18.85
- 192.168.18.86
- 192.168.18.87
- 192.168.18.88
- 192.168.18.89
- 192.168.18.96
- 192.168.18.98
- 192.168.18.99
- 192.168.19.100
- 192.168.19.101
- 192.168.19.105
- 192.168.19.106
- 192.168.19.108
- 192.168.19.109
- 192.168.19.111
- 192.168.19.112
- 192.168.19.114
- 192.168.19.116
- 192.168.19.117
- 192.168.19.118
- 192.168.19.124
- 192.168.19.126
- 192.168.19.129
- 192.168.19.13
- 192.168.19.130
- 192.168.19.132
- 192.168.19.133
- 192.168.19.135
- 192.168.19.137
- 192.168.19.14
- 192.168.19.141
- 192.168.19.142
- 192.168.19.143
- 192.168.19.144
- 192.168.19.145
- 192.168.19.147
- 192.168.19.148
- 192.168.19.149
- 192.168.19.15
- 192.168.19.153
- 192.168.19.158
- 192.168.19.159
- 192.168.19.160
- 192.168.19.161
- 192.168.19.163
- 192.168.19.166
- 192.168.19.167
- 192.168.19.168
- 192.168.19.177
- 192.168.19.179
- 192.168.19.18
- 192.168.19.180
- 192.168.19.185
- 192.168.19.186
- 192.168.19.187
- 192.168.19.188
- 192.168.19.189
- 192.168.19.191
- 192.168.19.192
- 192.168.19.193
- 192.168.19.195
- 192.168.19.204
- 192.168.19.205
- 192.168.19.207
- 192.168.19.209
- 192.168.19.21
- 192.168.19.22
- 192.168.19.220
- 192.168.19.222
- 192.168.19.224
- 192.168.19.226
- 192.168.19.228
- 192.168.19.23
- 192.168.19.233
- 192.168.19.234
- 192.168.19.24
- 192.168.19.26
- 192.168.19.31
- 192.168.19.32
- 192.168.19.36
- 192.168.19.38
- 192.168.19.39
- 192.168.19.40
- 192.168.19.41
- 192.168.19.43
- 192.168.19.44
- 192.168.19.46
- 192.168.19.47
- 192.168.19.50
- 192.168.19.52
- 192.168.19.53
- 192.168.19.55
- 192.168.19.56
- 192.168.19.57
- 192.168.19.59
- 192.168.19.60
- 192.168.19.62
- 192.168.19.64
- 192.168.19.71
- 192.168.19.73
- 192.168.19.76
- 192.168.19.77
- 192.168.19.78
- 192.168.19.79
- 192.168.19.80
- 192.168.19.81
- 192.168.19.84
- 192.168.19.85
- 192.168.19.86
- 192.168.19.89
- 192.168.19.91
- 192.168.19.92
- 192.168.19.94
- 192.168.19.95
- 192.168.19.96


# command executed by compromised IoT

mqttsa -fc 100 -fcsize 10 -sc 2400 192.168.2.1

# statistics on pcap files

using `capinfos <filename>`
```text
File name:           OpenvSwitch-24_2-0_to_sinetstream-zookeeper-1_0-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   1,507
File size:           216 kB
Data size:           191 kB
Capture duration:    1812.374651 seconds
First packet time:   2024-04-16 16:39:23.764699
Last packet time:    2024-04-16 17:09:36.139350
Data byte rate:      105 bytes/s
Data bit rate:       847 bits/s
Average packet size: 127.34 bytes
Average packet rate: 0 packets/s
SHA256:              2abd4675dd7bfcf995b1541cf0e81546aa72d9a95965363be98e2ee97ad610a0
RIPEMD160:           514a0bf1b3d1ddc31f65abc9844ba32eba3694e3
SHA1:                b931ebeba35a9ece0bbfdbd38b46d7df21c8a8dc
Strict time order:   True
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 1507
```
```
File name:           OpenvSwitch-24_4-0_to_sinetstream-connect-kafka-1_0-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   385 k
File size:           96 MB
Data size:           90 MB
Capture duration:    1814.089530 seconds
First packet time:   2024-04-16 16:39:23.764558
Last packet time:    2024-04-16 17:09:37.854088
Data byte rate:      50 kBps
Data bit rate:       400 kbps
Average packet size: 235.71 bytes
Average packet rate: 212 packets/s
SHA256:              2b252f49f573d31862270911089c65b4adf77e06bec2b9e7e1a456cb778786f4
RIPEMD160:           7e2b5c0edae3450d55aeb35db6151181a8a41d29
SHA1:                b3e0b72c0f0c8f9b84833b62a1bd8fb01188743e
Strict time order:   False
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 385120
```
```
File name:           VyOS130-1_1-0_to_VyOS130-2_1-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   7,696 k
File size:           1,002 MB
Data size:           879 MB
Capture duration:    1814.067532 seconds
First packet time:   2024-04-16 16:39:21.509488
Last packet time:    2024-04-16 17:09:35.577020
Data byte rate:      484 kBps
Data bit rate:       3,877 kbps
Average packet size: 114.25 bytes
Average packet rate: 4,242 packets/s
SHA256:              8bedf200026272dd349595c3e96fce499996ffa6cfa341ca792eb220d59c8c48
RIPEMD160:           e3be04d6b8f3042a8d5674bdcb0c4b66bcde626b
SHA1:                fb880aae7cdda8bcaeac3d4a0f99decf89350b47
Strict time order:   False
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 7696673
```