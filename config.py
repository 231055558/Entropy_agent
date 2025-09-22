# config.py

import os
from pathlib import Path

# --- Project Root ---
# 定义项目的根目录，方便后续构建绝对路径
PROJECT_ROOT = Path(__file__).parent

# --- Model Configuration ---
# 使用PROJECT_ROOT来构建模型的绝对路径，这样无论在哪里运行脚本都不会出错
MODEL_PATH = PROJECT_ROOT / "models" / "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"

# --- Llama.cpp Configuration ---
# 关键参数，用于初始化模型
N_GPU_LAYERS = 35    # 根据你的GPU VRAM调整，35对8GB是很好的起点
N_CTX = 4096         # 模型的上下文长度
VERBOSE_LLAMA = False # 是否在llama_cpp加载时打印详细日志

# --- Inference Configuration ---
DEFAULT_MAX_TOKENS = 1024 # 流式输出可以设置更长的最大长度
DEFAULT_TEMPERATURE = 0.7
DEFAULT_STREAM = True # <--- 新增：默认开启流式输出