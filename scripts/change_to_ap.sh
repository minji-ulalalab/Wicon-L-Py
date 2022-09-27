#!/bin/bash

sudo cp /etc/dhcpcd.conf.ap /etc/dhcpcd.conf
sudo cp /etc/dnsmasq.conf.ap /etc/dnsmasq.conf

sudo cp /etc/sysctl.d/routed-ap.conf.ap /etc/sysctl.d/routed-ap.conf
sudo cp /etc/hostapd/hostapd.conf.ap /etc/hostapd/hostapd.conf

sudo systemctl reboot
