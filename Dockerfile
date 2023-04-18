# Copyright(C) Venidera Research & Development, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Venidera Development Team <suporte@venidera.com>

FROM python:3.6-stretch
# Capturing default arguments
ARG API_PORT
ARG ROOT_DOMAIN
ARG COOKIE_SECRET
ARG MONGODB_URI
ARG CROSS_KEY
ARG GITHUB_BRANCH
ARG GITHUB_ACCESS_TOKEN
ARG TRELLOAPIKEY
ARG TRELLOAPITOKEN
ARG TRELLOAPISECRET
ARG TRELLOMANAGER
ARG TRELLOCALLBACK
# Setting environment variables
ENV API_PORT=${API_PORT}
ENV ROOT_DOMAIN=${ROOT_DOMAIN}
ENV COOKIE_SECRET=${COOKIE_SECRET}
ENV MONGODB_URI=${MONGODB_URI}
ENV CROSS_KEY=${CROSS_KEY}
ENV GITHUB_BRANCH=${GITHUB_BRANCH}
ENV GITHUB_ACCESS_TOKEN=${GITHUB_ACCESS_TOKEN}
ENV TRELLOAPIKEY=${TRELLOAPIKEY}
ENV TRELLOAPITOKEN=${TRELLOAPITOKEN}
ENV TRELLOAPISECRET=${TRELLOAPISECRET}
ENV TRELLOMANAGER=${TRELLOMANAGER}
ENV TRELLOCALLBACK=${TRELLOCALLBACK}

# Creating base image
RUN apt-get -y update --fix-missing && \
    # Installing common packages
    apt-get -y install \
    vim \
    git \
    bash \
    wget \
    curl \
    unzip \
    tzdata \
    openssl \
    locales \
    build-essential \
    net-tools \
    libpq-dev \
    musl-dev \
    libc-dev \
    pkg-config \
    python-dev \
    libffi-dev \
    libcurl4-openssl-dev \
    zlib1g \
    zlib1g-dev \
    liblapack-dev && \
    rm -rf /tmp/* /var/cache/apk/* && \
    # Setting portuguese language pack
    /usr/bin/localedef -i pt_BR -f UTF-8 pt_BR.UTF-8 && \
    # Defining portuguese as default languague
    export LANGUAGE=pt_BR.UTF-8 && \
    export LANG=pt_BR.UTF-8 && \
    export LC_ALL=pt_BR.UTF-8 && \
    # Upgrade everything
    apt-get -y dist-upgrade && \
    # Installing NodeJS and NPM
    curl -fsSL https://deb.nodesource.com/setup_14.x | bash - && \
    apt-get install -y nodejs && \
    # Cleaning everything
    apt-get -y autoremove && \
    apt-get -y autoclean
# Copying local repository
COPY . /proximidade-suporte
# Updating pip and installing public dependencies
RUN pip install --upgrade -r /proximidade-suporte/requirements.txt \
    pip \
    setuptools==58.4.0 \
    wheel \
    pymongo==3.12.1 \
    tornado==4.5.3 \
    motor==1.3.1 \
    pycurl \
    python-dateutil \
    pytz \
    unidecode \
    redis \
    bcrypt \
    apscheduler \
    tornadose \
    requests
# Fixing pymongo dependencies
RUN pip uninstall -y pymongo && pip uninstall -y bson && pip install pymongo==3.12.1 && \
    # Installing yarn
    npm install -g yarn && \
    # Checking if bower is used
    if [ -d "/proximidade-suporte/app/static" ]; then \
    # Chdir to static folder and installing all deps
    cd /proximidade-suporte/app/static && \
    yarn install; fi
# Exposing port
EXPOSE ${API_PORT}
# Creating working directory
WORKDIR /proximidade-suporte
# Running execution command
CMD ["/bin/bash", "-c", "python /proximidade-suporte/app/suporte.py --port=${API_PORT}"]
