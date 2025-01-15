import json
import subprocess
import uuid
from pathlib import Path
from typing import Dict

import modal

flux = (  # Download image layers to run FLUX_Q8.gguf model
    modal.Image.debian_slim(  #this starts with a basic and supported python version
        python_version="3.10"
    )
    .apt_install("git")  # install git
    .apt_install("nano")  # install to have a minimal text editor if we wanted to change something minimal
    .pip_install("comfy-cli")  # install comfy-cli
    .run_commands(  # use comfy-cli to install the ComfyUI repo and its dependencies
        "comfy --skip-prompt install --nvidia",
    )
    .run_commands(# download the GGUF Q8 model
    "comfy --skip-prompt model download --url https://huggingface.co/city96/FLUX.1-dev-gguf/resolve/main/flux1-dev-Q4_K_S.gguf  --relative-path models/unet",
    )
    .run_commands( # gguf node required for q8 model
        "comfy node install https://github.com/city96/ComfyUI-GGUF"
    )
    .run_commands(  # download the vae model required to use with the gguf model
        "comfy --skip-prompt model download --url https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors --relative-path models/vae"
    )
    .run_commands(  # download the cliper model required to use with GGUF model
        "comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors --relative-path models/clip",
        "comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors --relative-path models/clip",
    )
    .run_commands(  # download the lora anime -- optional you can disbale
        "comfy --skip-prompt model download --url https://civitai.com/models/640247/mjanimefluxlora?modelVersionId=716064 --relative-path models/loras --set-civitai-api-token [USE YOUR CIVITAI TOKEN]"
    )
    # put down here additional layers to your likings below
    .run_commands( # XLabs ControlNet node 
        "comfy node install https://github.com/XLabs-AI/x-flux-comfyui"
    )
    
    .run_commands( #xlab loras --optional
        "comfy --skip-prompt model download --url https://huggingface.co/Danrisi/UltraRealistic_LoraProject_V2/resolve/main/UltraRealPhoto.safetensors --relative-path models/loras",
        "comfy --skip-prompt model download --url https://huggingface.co/Maycol56v/Body_flux_fix/resolve/main/Eli.safetensors --relative-path models/loras",
        
    )
    
    .run_commands( #CR APPLY lora stack -- useful node -- optional
        "comfy node install https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes"
    )

)

app = modal.App(name="flux-comfyui", image=flux)
@app.function(
    allow_concurrent_inputs=10,
    concurrency_limit=1,
    container_idle_timeout=30,
    timeout=3200,
    gpu="a10g", # here you can change the gpu, i recommend either a10g or T4
)
@modal.web_server(8000, startup_timeout=60)
def ui():
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)
