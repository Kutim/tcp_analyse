import time
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from operator import add


sc = SparkContext(master="spark://192.168.30.57:7077",appName="PythonSparkStreamingRokidDtSnCount")
ssc = StreamingContext(sc, 2)
zkQuorum = 'zookeeper:2181'
topic = {'http_test':1}
groupid = "test-consumer-group"
lines = KafkaUtils.createStream(ssc, zkQuorum, groupid, topic)
lines1 = lines.flatMap(lambda x: x.split("\n"))
valuestr = lines1.map(lambda x: x.value.decode())
valuedict = valuestr.map(lambda x:eval(x))
message = valuedict.map(lambda x: x["message"])
rdd2 = message.map(lambda x: (time.strftime("%Y-%m-%d",time.localtime(float(x.split("\u0001")[0].split("\u0002")[1])/1000))+"|"+x.split("\u0001")[1].split("\u0002")[1],1)).map(lambda x: (x[0],x[1]))
rdd3 = rdd2.reduceByKey(add)
rdd3.saveAsTextFiles("/tmp/wordcount")
rdd3.pprint()
ssc.start()
ssc.awaitTermination()
