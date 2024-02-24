import ctypes
import sys
import os
import platform
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def _preload_cuda_deps(lib_folder: str, lib_name: str) -> None:
    """Preloads cuda deps if they could not be found otherwise."""
    logging.info("Preloading ", lib_folder)

    # Should only be called on Linux if default path resolution have failed
    assert platform.system() == "Linux", "Should only be called on Linux"
    import glob

    paths_to_search = [
        os.path.join("/usr/local/cuda-*/targets/*/lib", lib_name),
        os.path.join("/usr/lib64/", lib_name),
    ]
    for path in sys.path:
        paths_to_search.append(os.path.join(path, "nvidia", lib_folder, "lib", lib_name))

    lib_path = None
    for path in paths_to_search:
        candidate_lib_paths = glob.glob(path)
        if candidate_lib_paths and not lib_path:
            lib_path = candidate_lib_paths[0]
        if lib_path:
            break

    if not lib_path:
        paths = "\n".join(paths_to_search)
        raise ValueError(f"{lib_name} not found in {paths}")

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
    logging.basicConfig(level=logging.INFO)
    print(torch)
    print(StableDiffusionPipeline)
