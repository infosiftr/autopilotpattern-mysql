FROM percona:5.6

ENV CONTAINERPILOT_VER 3.1.0
ENV CONTAINERPILOT /etc/containerpilot.json5

# By keeping a lot of discrete steps in a single RUN we can clean up after
# ourselves in the same layer. This is gross but it saves ~100MB in the image
RUN set -ex \
    && export buildDeps='python-dev gcc unzip' \
    && export runDeps='python curl libffi-dev libssl-dev percona-xtrabackup ca-certificates' \
    && apt-get update \
    && apt-get install -y $buildDeps $runDeps --no-install-recommends \
    # \
    # get Python drivers MySQL, Consul, and Manta \
    # \
    && curl -Lvo /tmp/mysql-connector.deb http://dev.mysql.com/get/Downloads/Connector-Python/mysql-connector-python_2.1.3-1debian8.2_all.deb \
    && dpkg -i /tmp/mysql-connector.deb \
    && curl -v -Lo /tmp/mysql-utils.deb http://dev.mysql.com/get/Downloads/MySQLGUITools/mysql-utilities_1.5.6-1debian8_all.deb \
    && dpkg -i /tmp/mysql-utils.deb \
    && curl -Lvo get-pip.py https://bootstrap.pypa.io/get-pip.py \
    && python get-pip.py \
    && pip install \
       python-Consul==0.7.0 \
       manta==2.5.0 \
       mock==2.0.0 \
       json5==0.2.4 \
    # \
    # Add Consul from https://releases.hashicorp.com/consul \
    # \
    && export CHECKSUM=c8859a0a34c50115cdff147f998b2b63226f5f052e50f342209142420d1c2668 \
    && curl -Lvo /tmp/consul.zip https://releases.hashicorp.com/consul/0.8.4/consul_0.8.4_linux_amd64.zip \
    && echo "${CHECKSUM}  /tmp/consul.zip" | sha256sum -c \
    && unzip /tmp/consul.zip -d /usr/local/bin \
    && rm /tmp/consul.zip \
    && mkdir /config \
    # \
    # Add ContainerPilot and set its configuration file path \
    # \
    && export CONTAINERPILOT_CHECKSUM=d06e289e6e0ca82156d77cea36ff0f0246fcca60 \
    && curl -Lvo /tmp/containerpilot.tar.gz "https://github.com/joyent/containerpilot/releases/download/${CONTAINERPILOT_VER}/containerpilot-${CONTAINERPILOT_VER}.tar.gz" \
    && echo "${CONTAINERPILOT_CHECKSUM}  /tmp/containerpilot.tar.gz" | sha1sum -c \
    && tar zxf /tmp/containerpilot.tar.gz -C /usr/local/bin \
    && rm /tmp/containerpilot.tar.gz \
    # \
    # clean up to minimize image layer size \
    # \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove $buildDeps \
    && rm /tmp/mysql-connector.deb \
    && rm /tmp/mysql-utils.deb \
    && rm /get-pip.py \
    && rm /docker-entrypoint.sh


# configure ContainerPilot and MySQL
COPY etc/* /etc/
COPY bin/manager /usr/local/bin/manager
COPY bin/test.py /usr/local/bin/test.py
COPY bin/manage.py /usr/local/bin/manage.py

# override the parent entrypoint
ENTRYPOINT []
CMD ["/usr/local/bin/containerpilot"]
