from __future__ import print_function
import json,sys
def main():
    print ("main...........")
    with open("AppConfig.json") as configFile:
        config=json.loads(configFile.read())
    if len(sys.argv)==2:
        if sys.argv[1] == "FromKafkaToHdfsJob":
            from Jobs.FromKafkaToHdfsJob import FromKafkaToHdfsJob as Job
        elif sys.argv[1] == "HmmTrainJob":
            from Jobs.HmmTrainJob import HmmTrainJob as Job
        elif sys.argv[1] == "HmmDetectionJob":
            from Jobs.HmmDetectionJob import HmmDetectionJob as Job
        else:
            sys.exit("Main argv Error! nu such task")
    else:
        sys.exit("Main argv Error!")
    job = Job(config)
    job.startJob()
if __name__=="__main__":
    main()
