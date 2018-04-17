from __future__ import print_function
from Utils.get_ssc import *
from pyspark.streaming.kafka import KafkaUtils
from pyspark.sql import SQLContext
from pyspark.streaming import StreamingContext
import json


class FromKafkaToHdfsJob(object):
    def __init__(self, conf):
        self.conf = conf
        self.app_conf = conf["App"]["FromKafkaToHdfsJob"]
        self.sc = get_sc(self.app_conf)
        self.ssc = StreamingContext(self.sc, 2)
        self.sqlcontext = SQLContext(self.sc)

    def startJob(self):
        print("Start Job!")
        zookeeper = self.app_conf["zookeeper"]
        in_topic = self.app_conf["in_topic"]
        in_topic_partitions = self.app_conf["in_topic_partitions"]
        topic = {in_topic: in_topic_partitions}
        dstream = KafkaUtils.createStream(self.ssc, zookeeper, self.app_conf["app_name"], topic)
        dstream = dstream.map(lambda record: json.loads(record[1], encoding="utf8"))
        # dstream.foreachRDD(lambda rdd: self.save(rdd))
        dstream.pprint()
        self.ssc.start()
        self.ssc.awaitTermination()

    def save(self, rdd):
        if rdd.take(1):
            df = self.sqlcontext.createDataFrame(rdd)
            df.write.json(self.app_conf["savedir"], mode="append")
            print("........... save ")
        else:
            print("........... save pass")
            pass
