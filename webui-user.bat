@echo off

del "%HOMEPATH%\AppData\Local\Temp\gradio\*.*" /s /q >nul 2>&1

set callback_colab_url=
set callback_data={"server_id": 0, "type": ""}
set callback_model=main

set COMMANDLINE_ARGS=--listen --xformers --no-hashing --enable-insecure-extension-access --share --cloudflared --no-half-vae --disable-safe-unpickle --disable-console-progressbars --ui-settings-file settings.json --skip-torch-cuda-test --opt-channelslast --upcast-sampling
set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.75,max_split_size_mb:512
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
set ACCELERATE="True"

python launch.py
pause