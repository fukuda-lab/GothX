FROM confluentinc/cp-zookeeper:7.4.0

ENV ZOOKEEPER_CLIENT_PORT=2181
ENV ZOOKEEPER_TICK_TIME=2000

EXPOSE 2181

USER root
RUN echo "zookeeper" > /etc/hostname
USER appuser