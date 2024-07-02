#!/bin/vbash
source /opt/vyatta/etc/functions/script-template

configure

set interfaces ethernet eth0 address '192.168.33.1/24'
set interfaces ethernet eth1 address '192.168.32.10/20'
set interfaces ethernet eth1 ip enable-proxy-arp
set interfaces loopback lo
set protocols static route 0.0.0.0/0 next-hop 192.168.32.1
set system config-management commit-revisions '100'
set system console device ttyS0 speed '115200'
set system host-name 'Rloc-5'
set system login user vyos authentication encrypted-password '$6$wXLc225poEM$BA3MXWwUECowWYt.0Nk.haVGGWmB.HboqFg1daxANhwQ8a/25X3y2OKjh8Ee683.Nb5sqMHsbOdciN3uivh3c1'
set system login user vyos authentication plaintext-password ''
set system ntp server 0.pool.ntp.org
set system ntp server 1.pool.ntp.org
set system ntp server 2.pool.ntp.org
set system syslog global facility all level 'info'
set system syslog global facility protocols level 'debug'

commit
save

exit
