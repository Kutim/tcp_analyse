#!/usr/bin/python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import tempfile, os, threading, pyinotify, json, logging
from multiprocessing import Process, Queue
from elasticsearch import Elasticsearch, TransportError
from kafka import KafkaProducer
from urllib.parse import quote

file_dict = {}


def main():
    # Set loger
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logconsole = logging.StreamHandler()
    logconsole.setLevel(logging.INFO)
    formater = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    logconsole.setFormatter(formater)
    logger.addHandler(logconsole)
    # Set tcpflow path
    tcp_flow_path = "/usr/bin/tcpflow"
    parser = OptionParser(usage="Usage:python %prog[options]")
    parser.add_option("-a", "--args", dest="tcpflow_args", help='tcpflow options,Example:-a "-i eth0 port 80"',
                      default="", type="string")
    parser.add_option("-e", "--elasticsearch", dest="es", help="elasticsearch server ip,ip:port", type="string")
    parser.add_option("-i", "--index", dest="index", help="elasticsearch index name", type="string")
    parser.add_option("-t", "--type", dest="type", help="elasticsearch type name", type="string")
    parser.add_option("-k", "--kafka", dest="kafka", help="kafka server ip,ip:port", type="string")
    parser.add_option("-T", "--topic", dest="topic", help="kafka topic name", type="string")
    parser.add_option("-s", "--screen", dest="screen", help="Out data to screen,True or False", default=False)
    parser.add_option("-l", "--log", dest="log", help="log file", type="string")
    (options, args) = parser.parse_args()
    if not options:
        parser.print_help()
    tcpflow_args = options.tcpflow_args
    if options.log:
        logfile = logging.FileHandler(options.log, mode="w")
        logfile.setLevel(logging.INFO)
        logfile.setFormatter(formater)
        logger.addHandler(logfile)
        logger.info("[+]Write log in :%s" % options.log)
    queue = Queue()
    if [bool(options.es), bool(options.kafka), options.screen].count(True) > 1:
        logger.critical("[-]Data connot be written to Es/Kafka/Screen at the same time!")
        exit()
    # 子进程，处理数据到es\kafka\screen
    elif options.es:
        if not options.index or not options.type:
            logger.critical("[-]Missing index or type name!")
        threadES = Process(target=processES, args=(queue, options.es, options.index, options.type))
        threadES.start()
    elif options.kafka:
        threadKafka = Process(target=processKafka, args=(queue, options.kafka, options.topic))
        threadKafka.start()
    elif options.screen:
        logger.info("[+]Out data to screen!")
        threadScreen = Process(target=processScreen, args=(queue,))
        threadScreen.start()
    elif not options.screen:
        logger.critical("[-]Missing variable:-e or -k or -s")
        exit()
    # 子线程，开启并监控TCPFLOW
    temp_dir = tempfile.mkdtemp()
    logger.info("[+]TempDir:%s" % temp_dir)
    threadPacp = threading.Thread(target=processPcap, args=(temp_dir, tcp_flow_path, tcpflow_args))
    threadPacp.start()
    # 主进程，监控文件并生成数据
    wm = pyinotify.WatchManager()
    wm.add_watch(temp_dir, pyinotify.ALL_EVENTS)
    eventHandler = MonitorFlow(queue)
    notifier = pyinotify.Notifier(wm, eventHandler)
    notifier.loop()


# 启动Tcpflow的进程
def processPcap(tem_dir, tcp_flow_path, tcpflow_args):
    if tcpflow_args:
        tcpflow_args = tcpflow_args.replace('"', '')
        logger.info("[+]TcpFlow Command:cd %s && %s -a -e http -Ft %s" % (tem_dir, tcp_flow_path, tcpflow_args))
    output = os.popen("(cd %s && %s -a -e http -Ft %s -S enable_report=NO)" % (tem_dir, tcp_flow_path, tcpflow_args))
    logger.info("[+]TcpFlow UP!")
    output.read()
    logger.info("[-]Error:TcpFlow Down!")


# 写入数据到ES的进程temDir
def processES(queue, es_host, index, type):
    es = ES(es_host)
    while True:
        record = queue.get()
        es.write_to_es(index, type, record)


# 写入数据到kafka的进程
def processKafka(queue, kafka_host, topic):
    kafka = Kafka(kafka_host)
    while True:
        record = json.dumps(queue.get())
        record=bytes(record, encoding="utf8")
        kafka.Send_to_kafka(record, topic)


# 输出数据到屏幕的进程
def processScreen(queue):
    while True:
        print(queue.get())


# 监控流文件，并提取数据
class MonitorFlow(pyinotify.ProcessEvent):
    def __init__(self, queue, pevent=None, **kargs):
        self.queue = queue
        self.pevent = pevent
        self.my_init(**kargs)

    def process_IN_MODIFY(self, event):
        data = []
        try:
            if event.pathname not in file_dict.keys():
                file_dict[event.pathname] = 0
            file = open(event.pathname, "rb")
            file.seek(file_dict[event.pathname], 0)
            firstLine = file.readline()
            file.seek(file_dict[event.pathname], 0)
            if firstLine[0:4] in (b"GET ", b"POST"):
                data = self.RequestHandler(file)
            elif firstLine[0:9] == b"HTTP/1.1 " and b" Connection " not in firstLine:
                data = self.ResponseHandler(file)
            file_dict[event.pathname] = file.tell()
        except (IOError, OSError):
            pass
        if data != []:
            # Get src_ip src_port dst_ip dst_port From filename
            # add to data
            filename = event.pathname.split("/")[-1]
            [flow_time, ip_port] = filename[0:54].split("T")[0:2]
            flow_time = int(flow_time)
            [src, dst] = ip_port.split("-")
            src = src.split(".")
            dst = dst.split(".")
            src_port = str(int(src[4]))
            dst_port = str(int(dst[4]))
            src_ip = "%s.%s.%s.%s" % (str(int(src[0])), str(int(src[1])), str(int(src[2])), str(int(src[3])))
            dst_ip = "%s.%s.%s.%s" % (str(int(dst[0])), str(int(dst[1])), str(int(dst[2])), str(int(dst[3])))
            data["src_ip"] = src_ip
            data["dst_ip"] = dst_ip
            data["src_port"] = src_port
            data["dst_port"] = dst_port
            data["flow_time"] = flow_time
            d = self.FillEmpty(data)
            self.queue.put(d)

    def process_IN_CLOSE_WRITE(self, event):
        try:
            print("file close ", event.pathname)
            del file_dict[event.pathname]
            os.remove(event.pathname)
        except FileNotFoundError:
            pass

    def process_IN_OPEN(self, event):
        file_dict[event.pathname] = 0

    # http请求文件处理
    def RequestHandler(self, file):
        post = False
        # Get data From File Content
        for line in file.readlines():
            if line[0:4] == b"GET ":
                d = {}
                d["http_type"] = "Request"
                d["method"] = "GET"
                d["uri"] = quote(line.split()[1])
            elif line[0:5] == b"POST ":
                d = {}
                d["http_type"] = "Request"
                d["method"] = b"POST"
                d["uri"] = quote(line.split()[1])
            elif line[0:6] == b"Host: ":
                d["host"] = quote(line[6:])
            elif line[0:12] == b"User-Agent: ":
                d["user_agent"] = quote(line[11:])
            elif line[0:8] == b"Cookie: ":
                d["cookie"] = quote(line[8:])
            elif line[0:9] == b"Referer: ":
                d["referer"] = quote(line[9:])
            elif line[0:16] == b"Content-Length: ":
                d["content_length"] = int(line[16:].strip())
            elif line[0:14] == b"Content-Type: ":
                d["content_type"] = quote(line[14:])
            elif line[0:18] == b"Content-Encoding: ":
                d["content_encoding"] = quote(line[18:])
            elif line == b"\r\n" or line == b"\n":
                if d["method"] == "GET":
                    pass  # data.append(d)
                elif d["method"] == b"POST" and not post:
                    post = True
                    d["data"] = ""
            else:
                if post:
                    if line=="" :#or line=="\r\n":
                        continue #break
                    else:
                        d["data"] += quote(line[:])  # .strip()
        return d

    def FillEmpty(self, data):
        # 对数据没有的字段补空
        fields = ['referer', 'http_type', 'host', 'cookie',
                  'flow_time', 'src_port', 'uri', 'src_ip',
                  'dst_port', 'dst_ip', 'method', 'user_agent',
                  "content_type", "content_length", "content_encoding", "status", "server",
                  "date", "data"]
        keys = data.keys()
        empty_field = list(set(fields) ^ set(keys))
        for e in empty_field:
            data[e] = ""
        return data

    # 响应数据文件处理
    def ResponseHandler(self, file):
        d = {}
        response = False
        while True:
            line = file.readline()
            if line[0:9] == b"HTTP/1.1 ":
                d["http_type"] = "Response"
                d["status"] = quote(line.split()[1])
            elif line[0:8] == b"Server: ":
                d["server"] = quote(line[8:])
            elif line[0:14] == b"Content-Type: ":
                d["content_type"] = quote(line[14:])
            elif line[0:16] == b"Content-Length: ":
                d["content_length"] = quote(line[16:])
            elif line[0:6] == b"Date: ":
                d["date"] = quote(line[6:])
            elif line[0:18] == b"Content-Encoding: ":
                d["content_encoding"] = quote(line[18:])
            elif (line == b"\r\n" or line == b"\n") and not response:
                response = True
                d["data"] = ""
                continue
            if response:
                if line[0:9] == b"HTTP/1.1 ":
                    break
                if line==b"" or line==b"\r\n":
                    break
                else:
                    d["data"] += quote(line[:])
        return d


class ES(object):
    def __init__(self, es_host):
        """init Elastisearch connection"""
        self.es_connect = Elasticsearch(hosts=es_host)
        logger.info("[+]Elasticsearch connection success!")

    def write_to_es(self, index_name, type_name, record):
        """create a new document """
        try:
            self.es_connect.index(index_name, type_name, record)
        except TransportError:
            logger.critical("[-]No elasticsearch Index:%s" % index_name)


class Kafka(object):
    def __init__(self, kafka_host):
        self.producer = KafkaProducer(bootstrap_servers=kafka_host)
        logger.info("[+]Kafka connection success!")

    def Send_to_kafka(self, record, topic):
        self.producer.send(topic, record)



if __name__ == "__main__":
    main()
