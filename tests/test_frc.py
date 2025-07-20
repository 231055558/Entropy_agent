#!/usr/bin/env python3
"""
FRC模型推理测试程序
测试Llama-3.1-8B-Instruct模型的基本推理功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_model():
    """测试模型推理功能"""
    
    # 模型文件路径
    model_path = project_root / "services" / "models" / "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"
    
    if not model_path.exists():
        print(f"模型文件不存在: {model_path}")
        return False
    
    try:
        # 导入llama-cpp-python
        from llama_cpp import Llama
        
        # 初始化模型
        llm = Llama(
            model_path=str(model_path),
            n_gpu_layers=35,
            n_ctx=2048,
            verbose=False
        )
        
        # 使用正确的Llama-3.1 Chat格式
        messages = [
            {"role": "system", "content": "你是一个有用的AI助手。"},
            {"role": "user", "content": "你好啊，你是谁"}
        ]
        
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        generated_text = response['choices'][0]['message']['content']
        print(f"输入: 你好啊，你是谁")
        print(f"输出: {generated_text}")
        print("测试成功!")
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    test_model()
