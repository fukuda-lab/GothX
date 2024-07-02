# last version vulnerable to CVE-2023-25194
FROM confluentinc/cp-kafka-connect:7.3.1

ARG URL_KAFKA_CONNECT_MQTT=https://github.com/lensesio/stream-reactor/releases/download/3.0.1/kafka-connect-mqtt-3.0.1-2.5.0-all.tar.gz

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN mkdir -p /usr/share/java/stream-reactor \
 && ( curl -sL $URL_KAFKA_CONNECT_MQTT | \
      tar xzf - -C /usr/share/java/stream-reactor )

ENV CONNECT_BOOTSTRAP_SERVERS=placeholder_ip_kafka:9092
ENV CONNECT_REST_ADVERTISED_HOST_NAME=connect
ENV CONNECT_REST_PORT=8083
ENV CONNECT_GROUP_ID=compose-connect-group
ENV CONNECT_CONFIG_STORAGE_REPLICATION_FACTOR=1
ENV CONNECT_CONFIG_STORAGE_TOPIC=docker-connect-configs
ENV CONNECT_KEY_CONVERTER=org.apache.kafka.connect.json.JsonConverter
ENV CONNECT_OFFSET_STORAGE_REPLICATION_FACTOR=1
ENV CONNECT_OFFSET_STORAGE_TOPIC=docker-connect-offsets
ENV CONNECT_STATUS_STORAGE_REPLICATION_FACTOR=1
ENV CONNECT_STATUS_STORAGE_TOPIC=docker-connect-status
ENV CONNECT_VALUE_CONVERTER=org.apache.kafka.connect.json.JsonConverter
ENV CONNECT_PLUGIN_PATH=/usr/share/java
ENV CONNECT_INTERNAL_KEY_CONVERTER=org.apache.kafka.connect.json.JsonConverter
ENV CONNECT_INTERNAL_VALUE_CONVERTER=org.apache.kafka.connect.json.JsonConverter
ENV CONNECT_ZOOKEEPER_CONNECT=placeholder_ip_zookeeper:2181
ENV CONNECT_OFFSET_FLUSH_INTERVAL_MS=10000
ENV CONNECT_LOG4J_LOGGERS=org.apache.kafka.connect=DEBUG

USER root
RUN dnf install -y findutils \
    make \
    gcc \
    libssh \
    libssh-devel \
    openssh-clients \
    unzip && dnf clean all

RUN usermod -aG root appuser
# make vulnerable to CVE-2023-25194
# set system property org.apache.commons.collections.enableUnsafeSerialization=true
RUN sed -i '/export CLASSPATH/ i\EXTRA_ARGS=\"$EXTRA_ARGS -Dorg.apache.commons.collections.enableUnsafeSerialization=true\"' /bin/connect-distributed
