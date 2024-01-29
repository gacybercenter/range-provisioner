#!/bin/bash
declare -a commands

source /root/vars.sh

## DISABLE DAILY UPDATE SERVICE / APPARMOR ##
commands=("echo '*** USER DATA SCRIPT START ***'")
commands+=("systemctl stop apt-daily.service")
commands+=("systemctl stop apt-daily.timer")
commands+=("systemctl stop apt-daily-upgrade.timer")
commands+=("systemctl disable apt-daily.service")
commands+=("systemctl disable apt-daily.timer")
commands+=("systemctl disable apt-daily-upgrade.timer")
commands+=("systemctl kill --kill-who=all apt-daily.service")
commands+=("systemctl stop apparmor && systemctl disable apparmor")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done


## PACKAGE INSTALLS ##
commands=("export DEBIAN_FRONTEND=noninteractive")
commands+=("apt-get update")
commands+=("apt-get upgrade -y")
commands+=("apt-get install cockpit vsftpd apache2 tcpdump ncat iptables-persistent traceroute libmcrypt4 tree binutils zip acl -y")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done


## USER/GROUP CREATION ##
commands=("useradd -m -U -s /bin/bash RickSanchez")
commands+=("echo 'RickSanchez:P7Bird' | chpasswd")
commands+=("usermod -aG sudo,netdev RickSanchez")
commands+=("useradd -m -U -s /bin/bash Summer")
commands+=("echo 'Summer:winter' | chpasswd")
commands+=("useradd -m -U -s /bin/bash Morty")
commands+=("echo 'Morty:passw0rd321' | chpasswd")
commands+=("setfacl -R -m u:Summer:rwx /home/RickSanchez")
commands+=("setfacl -R -m u:Summer:rwx /home/Morty")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done


## ENABLES SSH ##
commands=("sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config")
commands+=("sed -i 's/#Port 22/Port 22222/g' /etc/ssh/sshd_config")
commands+=("service sshd restart")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done

## OBJECT PULL AND PLACEMENT ##
files=$(curl https://$dashboard.gacyberrange.org:7480/swift/v1/AUTH_$tenant_id/$container_name/ | grep "assets/rickdiculous")
for line in $files
do
  path=$(echo "$line" | sed 's/assets\/rickdiculous//g')
  curl https://$dashboard.gacyberrange.org:7480/swift/v1/AUTH_$tenant_id/$container_name/$line --create-dirs -o /tmp/staging/$path
done

## COPY SYSTEM FILES ##
commands=("chmod +x -R /tmp/staging/etc/*")
commands+=("cp /tmp/staging/etc/init.d/* /etc/init.d/")
# commands+=("cp /tmp/staging/etc/rc.d/* /etc/rc.d/")
commands+=("chmod 644 /tmp/staging/etc/ssh/*.pub")
commands+=("mv /tmp/staging/etc/ssh/*.pub /etc/ssh/")
commands+=("chmod 600 /tmp/staging/etc/ssh/*_key")
commands+=("mv /tmp/staging/etc/ssh/*_key /etc/ssh/")
commands+=("chmod 644 -R /tmp/staging/etc/ssh/*")
commands+=("cp /tmp/staging/etc/ssh/* /etc/ssh/")
commands+=("chmod +x -R /tmp/staging/etc/vsftpd/*")
commands+=("cp /tmp/staging/etc/vsftpd/* /etc/")
commands+=("cp /tmp/staging/home/Morty/* /home/Morty/")
commands+=("mkdir -p /home/RickSanchez/RICKS_SAFE/")
commands+=("mkdir -p /home/RickSanchez/ThisDoesntContainAnyFlags/")
commands+=("cp -R /tmp/staging/home/RickSanchez/* /home/RickSanchez/")
commands+=("cp -R /tmp/staging/home/Summer/* /home/Summer/")
commands+=("cp -R /tmp/staging/root/* /root/")
commands+=("chmod 644 /root/.bashrc")
commands+=("mkdir -p /var/ftp/ && cp /tmp/staging/var/ftp/* /var/ftp/")
commands+=("chmod 644 /tmp/staging/var/www/html/index.html")
commands+=("chmod 644 /tmp/staging/var/www/html/morty.png")
commands+=("chmod +x -R /tmp/staging/var/www/html/passwords")
commands+=("chmod 644 /tmp/staging/var/www/html/robots.txt")
commands+=("chmod +x -R /tmp/staging/usr/lib/cgi-bin/")
commands+=("cp /tmp/staging/usr/lib/cgi-bin/* /usr/lib/cgi-bin/")
commands+=("cp -r /tmp/staging/var/www/html/* /var/www/html/")
commands+=("chown www-data:www-data /var/www/html -R")
commands+=("chmod 644 /tmp/staging/etc/apache2/sites-available/")
commands+=("cp /tmp/staging/etc/apache2/sites-available/* /etc/apache2/sites-available/")
commands+=("ln -s /etc/apache2/mods-available/cgi.load /etc/apache2/mods-enabled/")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done

sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
service sshd restart


## FILE PERMISSIONS ##
commands=("chmod 755 /home/RickSanchez/ThisDoesntContainAnyFlags/")
commands+=("chmod 755 /home/RickSanchez/RICKS_SAFE/")
commands+=("chmod 744 /home/RickSanchez/RICKS_SAFE/safe")
commands+=("chmod 700 /home/Summer")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done


## AUTOLAUNCH SCRIPTS ##
cat > /etc/init.d/autolaunch <<"__EOF__"
#!/bin/bash

### BEGIN INIT INFO
# Provides:          autolaunch
# Required-Start:
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description:
# Description:
### END INIT INFO

. /etc/init.d/functions
iptables-restore </etc/iptables.conf

case "$1" in
start)
    ((/bin/bash /etc/init.d/netcat) &)
    ((/bin/bash /etc/init.d/fakessh) &)
    ((/bin/bash /etc/init.d/test) &)
    ;;
*)
    ;;
esac
exit 0
__EOF__

chmod -x /etc/update-motd.d/*
chmod +x /etc/init.d/autolaunch
update-rc.d autolaunch defaults



## Mute MOTD ##
commands=("sed -i 's/session    optional   pam_motd.so motd=\/run\/motd.dynamic/#session    optional   pam_motd.so motd=\/run\/motd.dynamic/g' /etc/pam.d/login")
commands+=("sed -i 's/session    optional   pam_motd.so noupdate/#session    optional   pam_motd.so noupdate/g' /etc/pam.d/login")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done

## CATS ##
commands=("chmod +x /tmp/staging/usr/bin/*")
commands+=("cp /tmp/staging/usr/bin/* /usr/bin/")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done

## FTP Config ##
touch /etc/vsftpd.user_list

## Apache Mods ##
commands=("sudo a2enmod proxy")
commands+=("sudo a2enmod proxy_http")
commands+=("sudo a2enmod proxy_balancer")
commands+=("sudo a2enmod lbmethod_byrequests")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done


## Force PASSV mode to be used for FTP (block ftp data)##
iptables -A OUTPUT -p tcp --sport 20 -j DROP
iptables-save -f /etc/iptables/rules.v4

## SERVICE ENABLE AND RESTARTS ##
commands=("systemctl enable cockpit")
commands+=("systemctl start cockpit")
# commands+=("systemctl enable httpd")
# commands+=("systemctl start httpd")
for cmd in "${commands[@]}"; do
    printf "\n**** Running: $cmd *****\n\n"
    eval $cmd
done

## Cockpit Flag ##
sed -i 's/<h1 id="brand" class="hide-before"><\/h1>/<h1>"FLAG{THERE IS NO ZEUS, IN YOUR FACE!}-10 POINTS"<\/h1>/g' /usr/share/cockpit/static/login.html

reboot