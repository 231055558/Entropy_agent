# services/frc/inference_engine.py

import logging
import time
from typing import List, Dict, Any, Iterator

# ... (之前的导入和日志配置保持不变) ...
try:
    import config
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    import config
    
from llama_cpp import Llama

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InferenceEngine:
    """
    一个封装了 llama-cpp-python 的高性能推理引擎。
    原生支持流式输出。
    """
    def __init__(self):
        # ... (__init__ 方法保持不变) ...
        logger.info("Initializing InferenceEngine...")
        load_start_time = time.time()
        
        if not config.MODEL_PATH.exists():
            error_msg = f"Model file not found at: {config.MODEL_PATH}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            self.llm = Llama(
                model_path=str(config.MODEL_PATH),
                n_gpu_layers=config.N_GPU_LAYERS,
                n_ctx=config.N_CTX,
                verbose=config.VERBOSE_LLAMA,
            )
            load_end_time = time.time()
            logger.info(f"LLM model loaded successfully in {load_end_time - load_start_time:.2f} seconds.")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}", exc_info=True)
            raise

    def create_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = config.DEFAULT_MAX_TOKENS,
        temperature: float = config.DEFAULT_TEMPERATURE,
        **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """
        【流式方法】接收messages列表，并以生成器的方式逐个yield出completion chunk。
        
        Args:
            messages: 对话历史列表。
            ... (其他参数) ...

        Yields:
            一个符合OpenAI流式格式的completion chunk字典。
        """
        logger.debug(f"Received stream completion request with {len(messages)} messages.")
        
        request_params = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,  # <--- 强制开启流式
            **kwargs
        }

        try:
            # create_chat_completion 在 stream=True 时返回一个生成器
            stream_generator = self.llm.create_chat_completion(**request_params)
            
            # 遍历这个生成器，并将每个chunk都yield出去
            for chunk in stream_generator:
                yield chunk
                
        except Exception as e:
            logger.error(f"Error during stream chat completion: {e}", exc_info=True)
            raise

    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        【非流式方法】为了兼容性和简单测试，保留一个非流式接口。
        它内部调用流式方法并将结果拼接起来。
        """
        chunks = []
        # 调用流式方法并收集所有chunks
        for chunk in self.create_chat_completion_stream(messages=messages, **kwargs):
            chunks.append(chunk)
        
        # 将流式结果重组成一个完整的非流式响应 (这部分逻辑比较复杂，可以简化)
        # 这里我们只做一个简单的示例，实际重组需要更多逻辑
        final_response = chunks[-1] if chunks else {}
        full_content = "".join([c['choices'][0]['delta'].get('content', '') for c in chunks])
        if 'choices' in final_response and len(final_response['choices']) > 0:
            final_response['choices'][0]['message'] = {'role': 'assistant', 'content': full_content}
        
        return final_response

# --- 更新后的单元测试部分 ---
def run_standalone_test():
    """
    更新后的独立测试，优先测试流式输出。
    """
    print("--- Running Standalone Test for InferenceEngine (Streaming) ---")
    
    try:
        engine = InferenceEngine()
        
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a short story about a robot who discovered music."}
        ]
        
        print(f"\nUser: {test_messages[-1]['content']}")
        print("\nAI (Streaming): ", end="", flush=True) # end="" 和 flush=True 是为了实现打字机效果
        
        # --- 测试流式方法 ---
        start_time = time.time()
        response_stream = engine.create_chat_completion_stream(messages=test_messages, max_tokens=100)
        
        full_response = []
        for chunk in response_stream:
            # 检查chunk中是否有内容
            delta_content = chunk['choices'][0]['delta'].get('content')
            if delta_content:
                print(delta_content, end="", flush=True)
                full_response.append(delta_content)
        
        end_time = time.time()
        print("\n--- Stream Finished ---")
        print(f"Streaming inference time: {end_time - start_time:.3f} seconds")
        
        # --- （可选）测试非流式方法 ---
        print("\n--- Testing Non-Streaming Method ---")
        start_time = time.time()
        completion = engine.create_chat_completion(messages=test_messages, max_tokens=100)
        end_time = time.time()
        response_text = completion['choices'][0]['message']['content']
        print(f"AI (Non-Streaming): {response_text}")
        print(f"Non-streaming inference time: {end_time - start_time:.3f} seconds")


    except Exception as e:
        print(f"\nAn error occurred during the test: {e}")

if __name__ == '__main__':
    run_standalone_test()