ARG UBUNTU_RELEASE=22.04
FROM --platform=linux/amd64 condaforge/mambaforge:latest
WORKDIR /app
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

MAINTAINER Laurent Gautier <lgautier@gmail.com>

ARG DEBIAN_FRONTEND=noninteractive
ENV CRAN_MIRROR=https://cloud.r-project.org \
    CRAN_MIRROR_TAG=-cran40

ARG RPY2_VERSION=RELEASE_3_5_6
ARG RPY2_CFFI_MODE=BOTH

ENV PATH /opt/conda/bin:$PATH

RUN apt-get update
RUN apt-get -y install g++


RUN apt-get update --yes
RUN apt-get upgrade --yes
RUN apt install -y --no-install-recommends \
    software-properties-common \
    dirmngr \
    lsb-release \
    wget

RUN wget -qO- "${CRAN_MIRROR}"/bin/linux/ubuntu/marutter_pubkey.asc \
    | tee -a /etc/apt/trusted.gpg.d/cran_ubuntu_key.asc

RUN add-apt-repository "deb ${CRAN_MIRROR}/bin/linux/ubuntu/ $(lsb_release -c -s)${CRAN_MIRROR_TAG}/"

RUN apt-get update -qq
RUN apt-get install -y \
        aptdaemon \
        ed \
        git \
	mercurial \
	libcairo-dev \
	libedit-dev \
	libnlopt-dev \
	libxml2-dev


RUN apt-get install -y	r-base \
	r-base-dev

COPY env.yml /app
RUN conda env create -f env.yml

RUN rm -rf /var/lib/apt/lists/*

# RUN wget -P /usr/local "https://go.dev/dl/go1.22.3.linux-amd64.tar.gz" && tar -C /usr/local -xzf /usr/local/go1.22.3.linux-amd64.tar.gz

# RUN apt install golang-go && go version
# RUN echo export PATH=$HOME/go/bin:/usr/local/go/bin:$PATH >> ~/.profile
# RUN source ~/.profile && go version


# RUN go install github.com/hscells/bigbro/cmd/bigbro@latest
# Activate the Conda environment
SHELL ["conda", "run", "-n", "tool_ui", "/bin/bash", "-c"]

ENV PATH=$PATH:/opt/java/jdk-15.0.2/bin

COPY . /app

RUN chmod +x -R /app/

RUN wget https://go.dev/dl/go1.22.3.linux-amd64.tar.gz -O go.tar.gz
RUN tar -xzvf go.tar.gz -C /usr/local
ENV PATH=$PATH:/usr/local/go/bin 
# RUN go version
RUN go install github.com/hscells/bigbro/cmd/bigbro@latest
ENV PATH=/root/go/bin:$PATH



