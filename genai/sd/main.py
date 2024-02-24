import ctypes
import sys
import os
import platform
from typing import Dict


def _preload_cuda_deps(lib_folder: str, lib_name: str) -> None:
    """Preloads cuda deps if they could not be found otherwise."""
    # Should only be called on Linux if default path resolution have failed
    assert platform.system() == "Linux", "Should only be called on Linux"
    import glob

    lib_path = None
    for path in sys.path:
        nvidia_path = os.path.join(path, "nvidia")
        if not os.path.exists(nvidia_path):
            continue
        candidate_lib_paths = glob.glob(os.path.join(nvidia_path, lib_folder, "lib", lib_name))
        if candidate_lib_paths and not lib_path:
            lib_path = candidate_lib_paths[0]
        if lib_path:
            break
    if not lib_path:
        raise ValueError(f"{lib_name} not found in the system path {sys.path}")
    ctypes.CDLL(lib_path)


def preload_cuda_deps() -> None:
    cuda_libs: Dict[str, str] = {
        "cublas": "libcublas.so.*[0-9]",
        "cudnn": "libcudnn.so.*[0-9]",
        "cuda_nvrtc": "libnvrtc.so.*[0-9].*[0-9]",
        "cuda_runtime": "libcudart.so.*[0-9].*[0-9]",
        "cuda_cupti": "libcupti.so.*[0-9].*[0-9]",
        "cufft": "libcufft.so.*[0-9]",
        "curand": "libcurand.so.*[0-9]",
        "cusolver": "libcusolver.so.*[0-9]",
        "cusparse": "libcusparse.so.*[0-9]",
        "nccl": "libnccl.so.*[0-9]",
        "nvtx": "libnvToolsExt.so.*[0-9]",
    }
    for lib_folder, lib_name in cuda_libs.items():
        _preload_cuda_deps(lib_folder, lib_name)


preload_cuda_deps()

import torch

from diffusers import StableDiffusionPipeline

if __name__ == "__main__":
    print(torch)
    print(StableDiffusionPipeline)
