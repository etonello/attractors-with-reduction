FROM debian:sid-20230522-slim

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

ARG NB_USER=user
ARG NB_UID=1000
RUN useradd -u $NB_UID -m -d /home/user -s /bin/bash $NB_USER

WORKDIR /app

RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        bzip2 \
        ca-certificates \
        wget \
        openjdk-11-jre-headless \
        && \
    apt clean -y && \
    rm -rf /var/lib/apt/lists/*

#
# base conda environment
#
RUN CONDA_VERSION="py310_23.3.1-0" && \
    echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-${CONDA_VERSION}-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    conda config --add channels colomoto && \
    conda config --add channels conda-forge && \
    conda install --no-update-deps -y \
        -c colomoto/label/fake \
        openjdk \
        pyqt && \
    find /opt/conda -name '*.a' -delete &&\
    conda clean -y --all && rm -rf /opt/conda/pkgs

RUN conda install -y \
        nomkl \
        clingo \
        pyeda \
        colomoto_jupyter \
    && conda clean -y --all && rm -rf /opt/conda/pkgs

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        unzip && \
    apt clean -y && \
    rm -rf /var/lib/apt/lists/*

RUN wget --quiet https://github.com/Z3Prover/z3/releases/download/z3-4.12.2/z3-4.12.2-x64-glibc-2.31.zip -O z3.zip &&\
    unzip z3.zip && \
    mv z3*/bin/libz3*.so /usr/lib/ && \
    rm -rf z3*

COPY . .
USER user
ENTRYPOINT ["python", "/app/attractor_computation.py"]
