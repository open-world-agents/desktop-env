ARG CUDA_VERSION=cu12

FROM openmmlab/lmdeploy:latest-cu12 AS cu12
ENV CUDA_VERSION_SHORT=cu123

FROM ${CUDA_VERSION} AS final

RUN python3 -m pip install timm

RUN python3 -m pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.6.3/flash_attn-2.6.3+${CUDA_VERSION_SHORT}torch2.3cxx11abiFALSE-cp310-cp310-linux_x86_64.whl