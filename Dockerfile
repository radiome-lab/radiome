FROM debian:buster-slim

RUN apt-get update && apt-get install -y curl unzip

RUN mkdir -p /opt/afni && \
    curl -O http://s3.amazonaws.com/fcp-indi/resources/linux_openmp_64.zip && \
    unzip -j linux_openmp_64.zip linux_openmp_64/3drefit linux_openmp_64/3dresample -d /opt/afni && \
    rm -rf linux_openmp_64.zip

RUN apt-get install -y build-essential libxt-dev libxft-dev libxpm-dev libxext-dev libxmu-dev libpng-dev
RUN ln -s $(/usr/lib/x86_64-linux-gnu/libXpm.so* | head -n 1) /usr/lib/x86_64-linux-gnu/libXp.so.6
RUN ln -s $(/usr/lib/x86_64-linux-gnu/libpng.so* | head -n 1) /usr/lib/x86_64-linux-gnu/libpng12.so.0

ENV PATH=/usr/local/miniconda/bin:$PATH

RUN curl -sO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda3-latest-Linux-x86_64.sh

RUN conda init
RUN conda update -n base -c defaults conda
RUN pip install virtualenv

RUN conda create -y --name py36 python=3.6
RUN conda create -y --name py37 python=3.7
RUN conda create -y --name py38 python=3.8

ENV PATH=/opt/afni:$PATH

COPY . /code
RUN cd /code && pip install -e '.[test]'
WORKDIR /code

ENTRYPOINT '/usr/local/miniconda/bin/tox'
CMD []