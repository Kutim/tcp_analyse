FROM ubuntu:17.10
MAINTAINER Venki Korukanti (venki.korukanti@gmail.com)

# Install.
RUN \
  sed -i 's/archive.ubuntu.com/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y build-essential && \
  apt-get install -y software-properties-common && \
  apt-get install -y byobu curl git htop man unzip vim wget && \
  apt-get install -y openssh-server sshpass && \
  apt-get install -y python3-pip && \
  rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd
RUN echo 'root:screencast' | chpasswd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#   StrictHostKeyChecking ask/StrictHostKeyChecking no/' /etc/ssh/ssh_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# Set environment variables.
ENV HOME /root

# Install Java.
RUN \
  echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
  add-apt-repository -y ppa:webupd8team/java && \
  apt-get update && \
  apt-get install -y oracle-java8-installer && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer

# Define commonly used JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

# Download Hadoop package
RUN cd /tmp/ && wget http://mirrors.ustc.edu.cn/apache/hadoop/common/hadoop-2.7.6/hadoop-2.7.6.tar.gz 

# Download Spark package
RUN cd /tmp/ && wget http://mirrors.ustc.edu.cn/apache/spark/spark-2.3.0/spark-2.3.0-bin-hadoop2.7.tgz 

# Download scala package
RUN cd /tmp/ && wget https://downloads.lightbend.com/scala/2.12.5/scala-2.12.5.tgz


RUN cp /usr/bin/python3 /usr/bin/python && \
  cp /usr/bin/pip3 /usr/bin/pip

RUN mkdir -p ~/.config/pip && \
  echo "[global]\n index-url = https://mirrors.ustc.edu.cn/pypi/web/simple \n format = columns" > ~/.config/pip/pip.conf

RUN echo "numpy \n elasticsearch \n kafka \n chardet \n pyinotify \n scipy \n sklearn \n pandas \n hmmlearn \n pyspark \n hdfs" > req.txt && pip install -r req.txt


# Create /opt directory
RUN mkdir -p /opt/

# Unpack hadoop into /opt/ and set HADOOP_HOME
RUN tar -xzf /tmp/hadoop-2.7.6.tar.gz -C /opt/  && \
  mv /opt/hadoop-2.7.6 /opt/hadoop

# Copy hadoop confs
ADD /hadoop-conf /opt/hadoop/etc/hadoop/

# Copy scala 
RUN tar -xzf /tmp/scala-2.12.5.tgz -C /opt/ && \
  mv /opt/scala-2.12.5 /opt/scala

# Set scala home
ENV SCALA_HOME /opt/scala

# Set Hadoop sepcific environment variables
ENV HADOOP_HOME /opt/hadoop
ENV HADOOP_CONF_DIR="${HADOOP_HOME}/etc/hadoop"
ENV HADOOP_LIBEXEC_DIR="${HADOOP_HOME}/libexec"

RUN sed -i 's/export JAVA_HOME=${JAVA_HOME}/export JAVA_HOME=\/usr\/lib\/jvm\/java-8-oracle/' /opt/hadoop/etc/hadoop/hadoop-env.sh

RUN mkdir -p /opt/data/apps/tmp
RUN mkdir -p /opt/data/apps/dfs/name
RUN mkdir -p /opt/data/apps/dfs/data

# Unpack spark into /opt and set SPARK_HOME
RUN tar -xzf /tmp/spark-2.3.0-bin-hadoop2.7.tgz -C /opt/ && \
  mv /opt/spark-2.3.0-bin-hadoop2.7 /opt/spark-bin-hadoop
ENV SPARK_HOME /opt/spark-bin-hadoop

ENV PATH $PATH:${HADOOP_HOME}/sbin/:${HADOOP_HOME}/bin:${SPARK_HOME}/sbin/:${SPARK_HOME}/bin:${SCALA_HOME}/bin

RUN ssh-keygen -f /root/.ssh/id_rsa -t rsa -N ''

# Spark ports
EXPOSE 7077 6066 8080 8081

# Hdfs ports
EXPOSE 50010 50020 50070 50075 50090 8020 9000
# Mapred ports
EXPOSE 19888
#Yarn ports
EXPOSE 8030 8031 8032 8033 8040 8042 8088
#Other ports
EXPOSE 49707 2122



