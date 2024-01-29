#!/bin/bash
source /root/vars.sh
# Addition of command arrays to allow for greater visability during deployment to track
# commands being run and the progress of deployment for future automation projects

domain="$domain_name"
if [ -z "$domain" ]
then
    echo "NO DOMAIN"
else
    touch /etc/motd
    echo -e "\n\n\n\n\n\n\n\n\n\n\nYou are accessing a system operated by the organization owning $domain_name.\n\n\n" >> /etc/motd
fi

## SETTING DEFAULT ROOT PASSWORD ##
declare -a commands
commands=("hostname $system_name")
commands+=("echo $system_name > /etc/hostname")
commands+=("chattr +i /etc/hostname")
commands+=("apt update -y")
commands+=('UCF_FORCE_CONFOLD=1 DEBIAN_FRONTEND=noninteractive apt -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" -qq -y install unzip docker-compose docker.io containerd')
commands+=("sudo adduser $USER docker")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done

## DISABLE UPDATES/UPGRADES ##
systemctl stop apt-daily.service
systemctl stop apt-daily.timer
systemctl stop apt-daily-upgrade.timer
systemctl disable apt-daily.service
systemctl disable apt-daily.timer
systemctl disable apt-daily-upgrade.timer
systemctl kill --kill-who=all apt-daily.service


## ENABLES SSH ##
sed -i 's/ssh_pwaut h:   0/ssh_pwauth:   1/g' /etc/cloud/cloud.cfg
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
sed -i 's/#Port 22/Port 22/g' /etc/ssh/sshd_config
sed -i 's/PrintMotd no/PrintMotd yes/g' /etc/ssh/sshd_config
sed -i 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config
sed -i 's/#PrintLastLog no/PrintLastLog yes/g' /etc/ssh/sshd_config
service sshd restart

sleep 1m

mkdir -p /var/lib/guacamole/recordings/
chmod -R 2750 /var/lib/guacamole/recordings/
chown 1000:1001 /var/lib/guacamole/recordings/

apt install guacd -y
sed -i s'/127.0.0.1/0.0.0.0/g' /etc/default/guacd
systemctl restart guacd
systemctl enable guacd