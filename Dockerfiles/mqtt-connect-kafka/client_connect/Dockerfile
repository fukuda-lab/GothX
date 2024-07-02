FROM openjdk:11.0.16-slim

RUN apt-get update && \
   DEBIAN_FRONTEND=noninteractive \
   apt-get -y install curl nano procps && \
   apt-get clean

COPY JNDI-Exploit-Kit-1.0-SNAPSHOT-all.jar /tmp
COPY FileServer.java /tmp
COPY tools.zip /tmp

ENTRYPOINT ["bash"]
