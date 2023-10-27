#!/bin/bash
declare -a commands

source /root/vars.sh

## ENABLES SSH ##
commands=("BEGIN SSH SETUP")
commands+=("sed -i 's/ssh_pwauth:   0/ssh_pwauth:   1/g' /etc/cloud/cloud.cfg")
commands+=("sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config")
commands+=("sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config")
commands+=("sed -i 's/disable_root: true/disable_root: 0\nssh_pwauth: 1/g' /etc/cloud/cloud.cfg")
commands+=("sed -i 's/ssh_pwaut h:   0/ssh_pwauth:   1/g' /etc/cloud/cloud.cfg")
commands+=("sed -i 's/PrintMotd no/PrintMotd yes/g' /etc/ssh/sshd_config")
commands+=("sed -i 's/#PrintLastLog no/PrintLastLog yes/g' /etc/ssh/sshd_config")
commands+=("sed -i 's/#Port 22/Port 22/g' /etc/ssh/sshd_config")
commands+=("service sshd restart")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done

## RDP INSTALL ##
commands=("BEGIN RDP SETUP")
commands+=("export DEBIAN_FRONTEND=noninteractive")
commands+=("apt-get update")
commands+=("UCF_FORCE_CONFOLD=1 DEBIAN_FRONTEND=noninteractive apt -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' -y install xrdp xorgxrdp")
commands+=("adduser xrdp ssl-cert")
commands+=("systemctl start xrdp")
commands+=("systemctl enable xrdp")
commands+=("systemctl stop gvmd && systemctl disable gvmd")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done

newgrp wireshark
usermod -aG wireshark kali

## Disable Color profile issue ##
cat > /etc/polkit-1/localauthority/50-local.d/color.pkla <<"__EOF__"
[Allow colord for all users]
Identity=unix-user:*
Action=org.freedesktop.color-manager.create-device;org.freedesktop.color-manager.create-profile;org.freedesktop.color-manager.delete-device;org.freedesktop.color-manager.delete-profile;org.freedesktop.color-manager.modify-device;org.freedesktop.color-manager.modify-profile
ResultAny=yes
ResultInactive=yes
ResultActive=yes
__EOF__

reboot