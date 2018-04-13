 FROM hadoop-spark
 ENV PYTHONUNBUFFERED 1
 RUN \
   mkdir -p /root/.config/pip/ && \
   echo "[global] \n index-url = https://mirrors.ustc.edu.cn/pypi/web/simple \n format = columns" > ~/.config/pip/pip.conf

 RUN \
   sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
   apt-get update && \
   apt-get -y upgrade && \
   apt-get install -y tcpflow gcc && \
   apt-get install -y python3-pip && \
   cp /usr/bin/pip3 /usr/bin/pip && \
   apt-get install -y nginx  net-tools iputils-ping && \
   rm -rf /var/lib/apt/lists/*

 RUN mkdir /code
 WORKDIR /code
 ADD pylib/pylib_list.txt /code/
 RUN pip install -r pylib_list.txt
 ADD . /code/
 USER root
 EXPOSE 80

