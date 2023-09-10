#!/bin/bash

#export callback_server_url=
#export callback_data=
#export callback_model=main

export PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.9,max_split_size_mb:512
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
export COMMANDLINE_ARGS="--xformers --no-hashing --enable-insecure-extension-access --share --cloudflared --no-half-vae --disable-safe-unpickle --disable-console-progressbars --ui-settings-file settings.json --skip-torch-cuda-test --opt-channelslast --upcast-sampling --opt-sdp-attention $@"
export CUDA_MODULE_LOADING=LAZY

TCMALLOC="$(PATH=/usr/sbin:$PATH ldconfig -p | grep -Po "libtcmalloc(_minimal|)\.so\.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

pip install "accelerate==0.21.0" > /dev/null
accelerate launch --num_cpu_threads_per_process=6 launch.py