#!/usr/bin/env python3
"""
FRC模型推理测试程序
测试Llama-3.1-8B-Instruct模型的基本推理功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_model_inference():
    """测试模型推理功能"""
    
    # 模型文件路径
    model_path = project_root / "services" / "models" / "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"
    
    print(f"🔍 检查模型文件: {model_path}")
    
    if not model_path.exists():
        print(f"❌ 模型文件不存在: {model_path}")
        return False
    
    print(f"✅ 模型文件存在，大小: {model_path.stat().st_size / (1024**3):.2f} GB")
    
    try:
        # 导入llama-cpp-python
        print("📦 导入llama-cpp-python...")
        from llama_cpp import Llama
        print("✅ llama-cpp-python导入成功")
        
        # 初始化模型
        print("🚀 初始化Llama模型...")
        print("⚠️  注意: 模型加载可能需要几分钟时间...")
        
        llm = Llama(
            model_path=str(model_path),
            n_gpu_layers=35,  # 根据文档建议
            n_ctx=2048,       # 减少上下文长度以节省内存
            verbose=True,     # 显示详细日志
            n_threads=4       # 线程数
        )
        
        print("✅ 模型初始化成功!")
        
        # 进行简单推理测试
        print("\n🤖 开始推理测试...")
        
        test_prompt = "嘿李华现在几点钟"
        print(f"📝 输入提示: {test_prompt}")
        print("💭 生成回复中...")
        
        response = llm(
            test_prompt,
            max_tokens=100,
            temperature=0.7,
            echo=False,
            stop=["Human:", "Assistant:"]
        )
        
        generated_text = response['choices'][0]['text'].strip()
        
        print(f"\n🎯 模型回复: {generated_text}")
        print(f"\n📊 推理统计:")
        print(f"   - 生成token数: {response['usage']['completion_tokens']}")
        print(f"   - 输入token数: {response['usage']['prompt_tokens']}")
        print(f"   - 总token数: {response['usage']['total_tokens']}")
        
        print("\n✅ 模型推理测试成功!")
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请先安装llama-cpp-python:")
        print("   pip install llama-cpp-python")
        print("   或者如果需要CUDA支持:")
        print("   CMAKE_ARGS=\"-DLLAMA_CUBLAS=on\" FORCE_CMAKE=1 pip install llama-cpp-python")
        return False
        
    except Exception as e:
        print(f"❌ 推理测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 FRC模型推理测试程序")
    print("=" * 60)
    
    success = test_model_inference()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试完成 - 模型工作正常!")
    else:
        print("💥 测试失败 - 请检查错误信息")
    print("=" * 60)
