FROM continuumio/miniconda3

ENV CMAKE_POLICY_VERSION_MINIMUM=3.5

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    make \
    git \
    ffmpeg \
    espeak-ng \
    libespeak-ng1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Conda environment
COPY environment.yml .
RUN conda env create -f environment.yml && conda clean -afy



SHELL ["bash", "-c"]


ENTRYPOINT ["bash", "-c", "source /opt/conda/etc/profile.d/conda.sh && conda activate md_search && exec \"$@\"", "--"]
