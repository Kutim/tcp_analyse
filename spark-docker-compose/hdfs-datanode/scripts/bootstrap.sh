#!/bin/bash

# Start the SSH daemon
service ssh restart

ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa -y
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys

# Setup password less ssh
sshpass ssh-copy-id root@localhost

cat /etc/hosts | grep hdfs-datanode >>IP.txt
scp IP.txt hdfs-namenode:/tmp
sleep 3;
ssh hdfs-namenode 'cat /tmp/IP.txt >> /etc/hosts'

# Replace "localhost" in Hadoop core-site xml with actual hostname which is passed
# as NAMENODE_HOSTNAME env variable
sed -i "s#localhost#$NAMENODE_HOSTNAME#g" /opt/hadoop/etc/hadoop/core-site.xml

# Start Datanode
hadoop-daemon.sh start datanode

# Run in daemon mode, don't exit
while true; do
  sleep 100;
done
