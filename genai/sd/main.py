import torch
import logging

from diffusers import StableDiffusionPipeline

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(torch)
    print(StableDiffusionPipeline)
