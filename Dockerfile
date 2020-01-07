FROM debian:buster-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates unzip git build-essential libxt-dev \
        libxft-dev libxpm-dev libxext-dev libxmu-dev \
        libpng-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN ln -s "$(ls -1 /usr/lib/x86_64-linux-gnu/libXpm.so* | head -n 1)" /usr/lib/x86_64-linux-gnu/libXp.so.6
RUN ln -s "$(ls -1 /usr/lib/x86_64-linux-gnu/libpng.so* | head -n 1)" /usr/lib/x86_64-linux-gnu/libpng12.so.0

# Install AFNI tools
RUN mkdir -p /opt/afni && \
    curl -O http://s3.amazonaws.com/fcp-indi/resources/linux_openmp_64.zip && \
    unzip -j linux_openmp_64.zip linux_openmp_64/3drefit linux_openmp_64/3dresample -d /opt/afni && \
    rm -rf linux_openmp_64.zip

ENV PATH=/opt/afni:$PATH

ENV PATH=/usr/local/miniconda/bin:$PATH
# Install and setup Miniconda
RUN curl -sO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda3-latest-Linux-x86_64.sh


RUN conda init
RUN conda update -n base -c defaults conda

# Install radiome on base environment
COPY . /code
WORKDIR /code
RUN pip install -e '.'