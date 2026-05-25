**===============**

**Client:**

**===============**



✅

**Optics Removed:**

admin up port 2 while there isn't optic connected to the port.



✅

**Optics Loss of Light:**

Setup: T.G of 10GbE-LAN (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

admin up for Uplinks.

admin up for ports 1.

full provision of port 1 of device 1.

full provision of port 1 of device 2.

turn off the laser on the T.G.

the alarm is at port 1 of device 1.



✅

**Signal Loss of Lock:**

Setup: T.G of 10GbE-LAN (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

admin up for Uplinks.

admin up for ports 1.

full provision of port 1 of device 1.

full provision of port 1 of device 2.

on T.G --> PHYS --> PHYS Config --> Interface --> Frequency Offset: 500 ppm.

the alarm is at port 1 of device 1.

**viavi\_basic\_functions --> insert\_PCS\_Alarm(Alarm\_Type='Loss of Lock')**



✅

**Loss of Synchronization:**

Setup: T.G of 8GFC (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

apply 10GbE-LAN service at port 1 of device 1.

admin up for port 1 of device 1.



✅

**High BER (Signal Fail):**

Setup: T.G of 10GbE-LAN (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

admin up for Uplinks.

admin up for ports 1.

full provision of port 1 of device 1.

full provision of port 1 of device 2.

on T.G --> PCS --> Alarms/Errors --> 64B/66B --> TX: Error --> Type: Invalid Sync Header, Mode: Rate, Rate: 1.0E-4 --> Insert 64B/66B Error.



✅

**Ethernet Link Failure:**

admin up for ETH 2 while there is no Lan connected to it.



✅

**Remote Fault:**

Setup: T.G of 10GbE-LAN (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

admin up for Uplinks.

admin up for ports 1.

full provision of port 1 of device 1.

full provision of port 1 of device 2.

on T.G --> PCS --> Alarms/Errors --> Reconciliation --> TX: Alarm --> Type: Remote Fault, Mode: Continuous --> Insert Reconc. Alarm.

the alarm is at port 1 of device 1.

**viavi\_basic\_functions --> Inject\_Alarm\_Class(Alarm\_Type = 'Remote Fault', Service\_Type = CLIENT\_SERVICE)**



✅

**License Expired or No License Applied:**

apply Encrypted service --> admin up port 1 of device 1.

alarm is at port 1 at device 1.



✅

**FarLCS (Far-end Loss of Client Signal):**

Setup: T.G of 10GbE-LAN (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

admin up for Uplinks.

admin up for ports 1.

full provision of port 1 of device 1.

full provision of port 1 of device 2.

turn off the laser on the T.G.

the alarm is at port 1 of device 2.



✅

**Unequipped / Unprovisioned:**

admin up port 2 while there isn't optic connected to the port.



✅

**Provisioning Mismatch:**

Setup: T.G of 10GbE-LAN (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

admin up for Uplinks.

admin up for ports 1.

full provision of port 1 of device 1.

not provision at all of port 1 of device 2.

the alarm is at port 1 of device 1.



✅

**Muxponder Path AIS:**

LOS Propagation Enabled --> admin up port 1 while there isn't optic connected to the port --> provisioning but not for all the expected slots --> wait 30 seconds



✅

**Optical Switch Loss of Signal:**

on 1000IL --> admin up for COM Port



✅

**Optics Loss Propagation:**

LOS Propagation Enabled --> admin up port 1 while there isn't optic connected to the port --> provisioning but not for all the expected slots --> wait 30 seconds



✅

**Optics Bit Rate Mismatch:**

Setup: T.G of 10GbE-LAN (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

remove provisioning to port 1 on device 1.

apply 16G FC service on port 1 on device 1.

admin up for port 1 of device 1.







**===============**

**Uplink:**

**===============**



✅

**Optics Removed:**

admin up uplink 2 while there isn't optic connected to the port.





**High BER (Signal Fail):**

Setup: T.G of 10GbE-LAN (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

admin up for Uplinks.

admin up for ports 1.

full provision of port 1 of device 1.

full provision of port 1 of device 2.

uplink 1 of device 1: uplink fec mode G.709

uplink 1 of device 2: uplink fec mode Zero FEC





**Optics Loss of Light:**

Setup: T.G of 10GbE-LAN (slot 4 port 1, 172.16.10.101) -> Port 1 of device 1.

&#x20;      Uplink of device 1 to Uplink of device 2.

&#x20;      Loop on Port 1 of device 2.

admin up for Uplinks.

admin down on uplink 1 on device 2.

alarm is at uplink 1 on device 1.







**===============**

**System:**

**===============**





**Power Supply Failure:**

PSU 2 usually unplugged so this alarm exist on PSU 2 (P2)

