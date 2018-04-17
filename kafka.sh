docker rm -f zookeeper
docker run -d --name zookeeper --publish 2181:2181 \
	--volume /etc/localtime:/etc/localtime \
	zookeeper:latest

docker rm -f kafka
docker run -d --name kafka --publish 9092:9092 \
	--publish 6667:6667 \
	--link zookeeper \
	--env KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
	--env KAFKA_ADVERTISED_HOST_NAME=192.168.30.83 \
	--env KAFKA_ADVERTISED_PORT=9092 \
	--volume /etc/localtime:/etc/localtime \
	wurstmeister/kafka:latest

# docker exec -it kafka /opt/kafka_2.12-1.0.1/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic http_test --from-beginning
