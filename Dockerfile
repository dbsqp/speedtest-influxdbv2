ARG ARCH=

# Pull base image
FROM ubuntu:latest


# Labels
LABEL MAINTAINER="https://github.com/dbsqp/"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    tzdata \
    debian-archive-keyring

# Note fails for ARM, have removed arm build target from yml file
# possible route to direct download:
#ARG TARGETPLATFORM
#RUN echo "I'm building for $TARGETPLATFORM"
#RUN if [ "$TARGETPLATFORM" = "linux/amd64" ]; then echo "THIS IS AMD64 = x86"; fi
#https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz
#RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then echo "THIS IS ARM64 = ARM"; fi
#https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-aarch64.tgz

RUN curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash && \
    sed 's/noble/jammy/g' /etc/apt/sources.list.d/ookla_speedtest-cli.list && \
    apt-get update && apt-get install speedtest


# Setup external package-sources
RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    python3-setuptools \
    python3-pip \
    python3-virtualenv \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* 

# do pip installs 
RUN pip3 install pytz influxdb-client requests
#datetime json os subprocess time socket sys
    
# Environment vars
ENV PYTHONIOENCODING=utf-8

# Copy files
ADD speedtest.py /
ADD get.sh /

# Run
CMD ["/bin/bash","/get.sh"]
