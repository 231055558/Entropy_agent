#!/usr/bin/env python3
"""
FRC模型推理测试程序
测试Llama-3.1-8B-Instruct模型的基本推理功能和性能
"""

import sys
import time
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
            {"role": "user", "content": '你好'}
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

def test_model_performance():
    """测试模型推理性能 - 统计20次推理的时间并计算平均值"""
    
    # 模型文件路径
    model_path = project_root / "services" / "models" / "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"
    
    if not model_path.exists():
        print(f"模型文件不存在: {model_path}")
        return False
    
    try:
        # 导入llama-cpp-python
        from llama_cpp import Llama
        
        print("正在初始化模型...")
        # 初始化模型
        llm = Llama(
            model_path=str(model_path),
            n_gpu_layers=35,
            n_ctx=2048,
            verbose=False
        )
        print("模型初始化完成!")
        
        # 测试用的问题列表（可以使用不同的问题来模拟真实使用场景）
        test_questions = [
            "你好，请介绍一下自己",
            "什么是人工智能？",
            "请解释一下机器学习的基本概念",
            "如何提高工作效率？",
            "请推荐几本好书",
            "今天天气怎么样？",
            "请解释一下Python编程语言的特点",
            "什么是深度学习？",
            "如何学习新技能？",
            "请简单介绍一下区块链技术"
        ]
        
        # 存储每次推理的时间
        inference_times = []
        
        print("\n开始性能测试，共进行20次推理...")
        print("=" * 60)
        
        for i in range(20):
            # 循环使用测试问题
            question = test_questions[i % len(test_questions)]
            
            # 构建消息
            messages = [
                {"role": "system", "content": "你是一个有用的AI助手。请简洁回答问题。"},
                {"role": "user", "content": question}
            ]
            
            # 开始计时 - 从输入传入的瞬间开始
            start_time = time.time()
            
            # 执行推理
            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=100,
                temperature=0.7
            )
            
            # 结束计时 - 到得到输出传出的时刻为止
            end_time = time.time()
            
            # 计算此次推理时间
            inference_time = end_time - start_time
            inference_times.append(inference_time)
            
            # 获取生成的文本
            generated_text = response['choices'][0]['message']['content']
            
            # 输出此次测试的详细信息
            print(f"第 {i+1:2d} 次推理:")
            print(f"  问题: {question}")
            print(f"  回答: {generated_text[:50]}{'...' if len(generated_text) > 50 else ''}")
            print(f"  用时: {inference_time:.3f} 秒")
            print("-" * 60)
        
        # 计算统计信息
        avg_time = sum(inference_times) / len(inference_times)
        min_time = min(inference_times)
        max_time = max(inference_times)
        
        print("\n性能测试结果:")
        print("=" * 60)
        print(f"总推理次数: {len(inference_times)}")
        print(f"平均推理时间: {avg_time:.3f} 秒")
        print(f"最快推理时间: {min_time:.3f} 秒")
        print(f"最慢推理时间: {max_time:.3f} 秒")
        print(f"总计用时: {sum(inference_times):.3f} 秒")
        
        print("\n详细时间列表:")
        for i, t in enumerate(inference_times, 1):
            print(f"第 {i:2d} 次: {t:.3f} 秒")
        
        return True
        
    except Exception as e:
        print(f"性能测试错误: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='FRC模型测试程序')
    parser.add_argument('--performance', action='store_true', help='运行性能测试')
    parser.add_argument('--basic', action='store_true', help='运行基本功能测试')
    
    args = parser.parse_args()
    
    if args.performance:
        print("运行性能测试...")
        test_model_performance()
    elif args.basic:
        print("运行基本功能测试...")
        test_model()
    else:
        # 默认运行性能测试
        print("运行性能测试...")
        test_model_performance()
