FROM --platform=linux/amd64 ubuntu:22.04

# إعداد المتغيرات الأساسية
ENV DEBIAN_FRONTEND=noninteractive

# تحديث النظام وتثبيت الأدوات الأساسية في طبقة واحدة لتقليل حجم الصورة
RUN apt update -y && apt install -y \
    software-properties-common \
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
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt update -y \
    && rm -rf /var/lib/apt/lists/*

# تثبيت pip لبايثون 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 \
    && python3.11 -m pip install --upgrade pip setuptools wheel

# تثبيت مكتبة تيليثون
RUN python3.11 -m pip install --no-cache-dir telethon

# إعداد مجلد العمل
WORKDIR /root

# سحب الكود
RUN git clone https://github.com/2mrxe2/pro

# إعداد SSH
RUN mkdir -p /var/run/sshd \
    && echo "root:Ali71931@@" | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# فتح المنفذ
EXPOSE 22

# تشغيل SSH في الخلفية، وسنعتمد على دخولك اليدوي لتشغيل البوت
# قمنا بإضافة أمر إبقاء الحاوية حية
CMD ["/usr/sbin/sshd", "-D"]
