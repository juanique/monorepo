import logging

import os
import sys

logging.basicConfig(level=logging.INFO)
logging.info("logging is working")
from pathlib import Path

import torch
import random
from torch import autocast
from diffusers import StableDiffusionPipeline

SD_1_4 = "CompVis/stable-diffusion-v1-4"


def generate(pipeline, prompt, outputdir="/outputs", negative=""):
    pipeline.to("cuda")
    # pipeline.enable_sequential_cpu_offload()

    with autocast("cuda"):
        output = pipeline(prompt, negative_prompt=negative)
        image = output.images[0]
        file = prompt.replace(" ", "_").replace(",", "")[0:15] + str(random.randint(0, 10000))
        filename = f"{outputdir}/{file}.png"
        image.save(filename)
        print(filename)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage <script> 'prompt'")
        os.exit(1)

    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        print("Missing env HUGGINGFACE_TOKEN")

    prompt = sys.argv[1]
    print("Generating", prompt)
    Path("/outputs").mkdir(parents=True, exist_ok=True)
    pipe = StableDiffusionPipeline.from_pretrained(SD_1_4, use_auth_token=token)
    generate(pipe, prompt)

    print(torch)
    print(StableDiffusionPipeline)
