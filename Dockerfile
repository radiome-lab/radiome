FROM neurodebian:xenial-non-free
MAINTAINER The C-PAC Team <cnl@childmind.org>

RUN apt-get update

# Install the validator
RUN apt-get install -y curl && \
     curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
     apt-get install -y nodejs
RUN npm install -g bids-validator

# Install Ubuntu dependencies and utilities
RUN apt-get install -y \
      build-essential \
      cmake \
      git \
      graphviz \
      graphviz-dev \
      gsl-bin \
      libcanberra-gtk-module \
      libexpat1-dev \
      libgiftiio-dev \
      libglib2.0-dev \
      libglu1-mesa \
      libglu1-mesa-dev \
      libjpeg-progs \
      libgl1-mesa-dri \
      libglw1-mesa \
      libxml2 \
      libxml2-dev \
      libxext-dev \
      libxft2 \
      libxft-dev \
      libxi-dev \
      libxmu-headers \
      libxmu-dev \
      libxpm-dev \
      libxslt1-dev \
      m4 \
      make \
      mesa-common-dev \
      mesa-utils \
      netpbm \
      pkg-config \
      tcsh \
      unzip \
      vim \
      xvfb \
      xauth \
      zlib1g-dev

# Install 16.04 dependencies
RUN apt-get install -y \
      dh-autoreconf \
      libgsl-dev \
      libmotif-dev \
      libtool \
      libx11-dev \
      libxext-dev \
      x11proto-xext-dev \
      x11proto-print-dev \
      xutils-dev

# Compiles libxp- this is necessary for some newer versions of Ubuntu
# where the is no Debian package available.
RUN git clone git://anongit.freedesktop.org/xorg/lib/libXp /tmp/libXp && \
    cd /tmp/libXp && \
    ./autogen.sh && \
    ./configure && \
    make && \
    make install && \
    cd - && \
    rm -rf /tmp/libXp


COPY required_afni_pkgs.txt /opt/required_afni_pkgs.txt
# Install AFNI tools
RUN libs_path=/usr/lib/x86_64-linux-gnu && \
    if [ -f $libs_path/libgsl.so.19 ]; then \
        ln $libs_path/libgsl.so.19 $libs_path/libgsl.so.0; \
    fi && \
    mkdir -p /opt/afni && \
    curl -sO http://s3.amazonaws.com/fcp-indi/resources/linux_openmp_64.zip && \
    unzip -j linux_openmp_64.zip $(cat /opt/required_afni_pkgs.txt) -d /opt/afni && \
    rm -rf linux_openmp_64.zip

ENV PATH=/opt/afni:$PATH

# install ANTs
ENV PATH=/usr/lib/ants:$PATH
RUN apt-get install -y ants

# Install and setup Miniconda
ENV PATH=/usr/local/miniconda/bin:$PATH
RUN curl -sO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda3-latest-Linux-x86_64.sh

RUN conda init
RUN conda update -n base -c defaults conda

# Install radiome on base environment
COPY . /code
WORKDIR /code
RUN pip install -e '.'
RUN pip install git+https://github.com/puorc/radiome-initial.git
RUN pip install git+https://github.com/puorc/radiome-afni-skullstrip.git
#RUN chmod +x /code/radiome/cli.py
#ENTRYPOINT ['/code/radiome/cli.py']
