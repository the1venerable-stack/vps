FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update -y && apt install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt update -y && apt install -y \
    openssh-server \
    sudo \
    vim \
    net-tools \
    curl \
    wget \
    git \
    tzdata \
    ffmpeg \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    python3.11 -m pip install --upgrade pip setuptools wheel

# تم الإبقاء على مكتبة telethon فقط
RUN python3.11 -m pip install --no-cache-dir \
    telethon

WORKDIR /root
RUN git clone https://github.com/2mrxe2/pro

RUN mkdir /var/run/sshd
# تم تغيير كلمة السر إلى Ali71931@@
RUN echo "root:Ali71931@@" | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]

