#!/usr/bin/env python3
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_model_performance():
    model_path = project_root / "services" / "models" / "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"
    
    if not model_path.exists():
        print(f"模型文件不存在: {model_path}")
        return False
    
    from llama_cpp import Llama
    
    llm = Llama(
        model_path=str(model_path),
        n_gpu_layers=35,
        n_ctx=2048,
        verbose=False
    )
    
    test_questions = [
        "你好",
        "什么是AI？",
        "解释机器学习",
        "如何提高效率？",
        "推荐好书",
        "今天天气",
        "Python特点",
        "什么是深度学习？",
        "如何学习？",
        "区块链技术"
    ]
    
    inference_times = []
    
    for i in range(20):
        question = test_questions[i % len(test_questions)]
        messages = [
            {"role": "system", "content": "简洁回答。"},
            {"role": "user", "content": question}
        ]
        
        start_time = time.time()
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=50,
            temperature=0.7
        )
        end_time = time.time()
        
        inference_time = end_time - start_time
        inference_times.append(inference_time)
        
        print(f"第{i+1}次: {inference_time:.3f}秒")
    
    avg_time = sum(inference_times) / len(inference_times)
    print(f"\n平均时间: {avg_time:.3f}秒")
    print(f"最快: {min(inference_times):.3f}秒")
    print(f"最慢: {max(inference_times):.3f}秒")
    
    return True

if __name__ == "__main__":
    test_model_performance()
