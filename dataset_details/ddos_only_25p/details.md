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

112 distinct ips

- 192.168.18.10
- 192.168.18.100
- 192.168.18.104
- 192.168.18.106
- 192.168.18.109
- 192.168.18.115
- 192.168.18.117
- 192.168.18.125
- 192.168.18.126
- 192.168.18.128
- 192.168.18.132
- 192.168.18.134
- 192.168.18.135
- 192.168.18.136
- 192.168.18.137
- 192.168.18.140
- 192.168.18.144
- 192.168.18.146
- 192.168.18.147
- 192.168.18.148
- 192.168.18.151
- 192.168.18.159
- 192.168.18.160
- 192.168.18.164
- 192.168.18.166
- 192.168.18.17
- 192.168.18.170
- 192.168.18.174
- 192.168.18.176
- 192.168.18.183
- 192.168.18.184
- 192.168.18.185
- 192.168.18.188
- 192.168.18.189
- 192.168.18.19
- 192.168.18.192
- 192.168.18.193
- 192.168.18.197
- 192.168.18.212
- 192.168.18.213
- 192.168.18.215
- 192.168.18.216
- 192.168.18.221
- 192.168.18.222
- 192.168.18.223
- 192.168.18.227
- 192.168.18.229
- 192.168.18.232
- 192.168.18.234
- 192.168.18.29
- 192.168.18.45
- 192.168.18.55
- 192.168.18.56
- 192.168.18.57
- 192.168.18.58
- 192.168.18.65
- 192.168.18.75
- 192.168.18.77
- 192.168.18.78
- 192.168.18.87
- 192.168.18.96
- 192.168.18.99
- 192.168.19.105
- 192.168.19.106
- 192.168.19.108
- 192.168.19.111
- 192.168.19.116
- 192.168.19.118
- 192.168.19.126
- 192.168.19.13
- 192.168.19.132
- 192.168.19.133
- 192.168.19.135
- 192.168.19.14
- 192.168.19.144
- 192.168.19.147
- 192.168.19.148
- 192.168.19.153
- 192.168.19.158
- 192.168.19.159
- 192.168.19.160
- 192.168.19.161
- 192.168.19.166
- 192.168.19.179
- 192.168.19.180
- 192.168.19.186
- 192.168.19.187
- 192.168.19.188
- 192.168.19.191
- 192.168.19.193
- 192.168.19.195
- 192.168.19.204
- 192.168.19.207
- 192.168.19.22
- 192.168.19.224
- 192.168.19.228
- 192.168.19.233
- 192.168.19.234
- 192.168.19.39
- 192.168.19.40
- 192.168.19.46
- 192.168.19.52
- 192.168.19.59
- 192.168.19.60
- 192.168.19.62
- 192.168.19.73
- 192.168.19.76
- 192.168.19.77
- 192.168.19.80
- 192.168.19.85
- 192.168.19.86
- 192.168.19.95


# command executed by compromised IoT

mqttsa -fc 100 -fcsize 10 -sc 2400 192.168.2.1

# statistics on pcap files

using `capinfos <filename>`
```text
File name:           VyOS130-1_1-0_to_VyOS130-2_1-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   8,122 k
File size:           880 MB
Data size:           750 MB
Capture duration:    1792.661204 seconds
First packet time:   2024-04-09 10:39:00.095729
Last packet time:    2024-04-09 11:08:52.756933
Data byte rate:      418 kBps
Data bit rate:       3,350 kbps
Average packet size: 92.45 bytes
Average packet rate: 4,530 packets/s
SHA256:              d74b617e98b708787bc50cfe11abd47ef1357ca20d9968a61d22d2ef3cf9f304
RIPEMD160:           115b6722e5aef82af623c959cff782990091c4bc
SHA1:                0ec68dcb5753ab03547976d989fc8b08e672975a
Strict time order:   False
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 8122318
```
```text
File name:           OpenvSwitch-24_2-0_to_sinetstream-zookeeper-1_0-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   1,494
File size:           214 kB
Data size:           190 kB
Capture duration:    1789.807337 seconds
First packet time:   2024-04-09 10:39:03.000425
Last packet time:    2024-04-09 11:08:52.807762
Data byte rate:      106 bytes/s
Data bit rate:       853 bits/s
Average packet size: 127.84 bytes
Average packet rate: 0 packets/s
SHA256:              c08eb4a7c951a115c3b714729a2727d9576db7fa38faf0b1e1c1e8bbc1df97cc
RIPEMD160:           628610994ac7aa7a52b743753e31956463d3dbe8
SHA1:                ec2b8b22c2d8024f8096a2a1aea2b10dc8a893f7
Strict time order:   True
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 1494
```
```
File name:           OpenvSwitch-24_4-0_to_sinetstream-connect-kafka-1_0-0.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
File timestamp precision:  microseconds (6)
Packet size limit:   file hdr: 65535 bytes
Number of packets:   314 k
File size:           78 MB
Data size:           73 MB
Capture duration:    1793.374205 seconds
First packet time:   2024-04-09 10:39:01.135003
Last packet time:    2024-04-09 11:08:54.509208
Data byte rate:      40 kBps
Data bit rate:       326 kbps
Average packet size: 232.70 bytes
Average packet rate: 175 packets/s
SHA256:              3322b425745f65042120463067fcb29ef4e614894ad260a794f8621b4abff856
RIPEMD160:           89487efb54eb49d18d440ce608fa7647baf0ee31
SHA1:                520b247689f3ed902de9b78c6762bb30e43c83cb
Strict time order:   False
Number of interfaces in file: 1
Interface #0 info:
                     Encapsulation = Ethernet (1 - ether)
                     Capture length = 65535
                     Time precision = microseconds (6)
                     Time ticks per second = 1000000
                     Number of stat entries = 0
                     Number of packets = 314420
```