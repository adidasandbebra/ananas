@echo off

del "%HOMEPATH%\AppData\Local\Temp\gradio\*.*" /s /q >nul 2>&1

set csu=
set cd={"server_id": 0, "type": ""}
set cm=main

set COMMANDLINE_ARGS=--listen --xformers --no-hashing --enable-insecure-extension-access --share --cloudflared --no-half-vae --disable-safe-unpickle --disable-console-progressbars --ui-settings-file settings.json --skip-torch-cuda-test --opt-channelslast --upcast-sampling --opt-sdp-attention
set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.9,max_split_size_mb:512
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
set CUDA_MODULE_LOADING=LAZY

pip install "accelerate==0.21.0" >nul
"C:\Program Files\Python310\Scripts\accelerate.exe" launch --num_cpu_threads_per_process=6 launch.py
pause