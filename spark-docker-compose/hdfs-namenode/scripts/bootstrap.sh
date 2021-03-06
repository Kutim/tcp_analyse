#!/bin/bash

# Start the SSH daemon
service ssh restart

ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa -y
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys

# Setup password less ssh
sshpass -f ssh-copy-id root@localhost

export HOSTNAME=`hostname`
sed -i "s#localhost#$HOSTNAME#g" /opt/hadoop/etc/hadoop/core-site.xml
sed -i "s#localhost#$HOSTNAME#g" /opt/hadoop/etc/hadoop/yarn-site.xml
sed -i "s#localhost#$HOSTNAME#g" /opt/hadoop/etc/hadoop/hdfs-site.xml

# Format the NameNode data directory
hdfs namenode -format -force

# Start HDFS services
start-dfs.sh

# Wait for HDFS services to be up and running
sleep 5

# Create a tmp directory and make it accessible to everyone
hadoop fs -mkdir -p /tmp
hadoop fs -chmod -R 777 /tmp

# start yarn services
start-yarn.sh

# Run in daemon mode, don't exit
while true; do
  sleep 100;
done
