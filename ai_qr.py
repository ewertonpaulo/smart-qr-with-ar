import sys

from PIL import Image

def generate_artistic_qr(content: str, prompt: str, negative_prompt: str) -> Image.Image:
    try:
        import torch
        from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, DPMSolverMultistepScheduler
        from utils.qr_utils import generate_qr_image
        from qrcode.constants import ERROR_CORRECT_H
    except ImportError:
        print("Erro: Dependências não encontradas.", file=sys.stderr)
        return None

    qr_image = generate_qr_image(content, border=1, error_correction=ERROR_CORRECT_H)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    print(f"Usando dispositivo: {device.upper()}")

    controlnet = ControlNetModel.from_pretrained("DionTimmer/controlnet_qrcode-control_v1p_sd15", torch_dtype=torch_dtype).to(device)
    pipe = StableDiffusionControlNetPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", controlnet=controlnet, torch_dtype=torch_dtype, safety_checker=None).to(device)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras=True)

    try:
        pipe.enable_xformers_memory_efficient_attention()
    except ImportError:
        print("xFormers não encontrado. Para uma geração mais rápida em GPUs NVIDIA, instale com: pip install xformers")

    print("Gerando imagem com IA...")
    generated_image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=qr_image,
        width=768,
        height=768,
        guidance_scale=7.5,
        controlnet_conditioning_scale=1.5,
        num_inference_steps=30,
    ).images[0]

    return generated_image