#!/bin/bash

#export csu=
#export cd=
#export cm=main

export PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.9,max_split_size_mb:512
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
export COMMANDLINE_ARGS="--xformers --no-hashing --enable-insecure-extension-access --share --cloudflared --no-half-vae --disable-safe-unpickle --disable-console-progressbars --ui-settings-file settings.json --skip-torch-cuda-test --opt-channelslast --upcast-sampling --opt-sdp-attention $@"
export CUDA_MODULE_LOADING=LAZY

if [ -z $DISABLE_TUNNELS ]; then
  export COMMANDLINE_ARGS="--share --cloudflared $COMMANDLINE_ARGS"
fi

TCMALLOC="$(PATH=/usr/sbin:$PATH ldconfig -p | grep -Po "libtcmalloc(_minimal|)\.so\.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

if [ -x "$(command -v accelerate)" ]; then
  accelerate launch --num_cpu_threads_per_process=6 launch.py
else
  python launch.py
fi