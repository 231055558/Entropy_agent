# test_asr_robust.py

import asyncio
import os
import sounddevice as sd
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# --- 配置 ---
load_dotenv()
API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Deepgram推荐的音频格式
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"

# 创建一个异步事件，用于在主协程和回调之间同步
# (这个有点像线程编程里的Event，但用于asyncio)
mic_ready = asyncio.Event()

# --- 音频处理 ---
# 使用一个简单的异步队列
audio_queue = asyncio.Queue()

def audio_callback(indata, frames, time, status):
    """sounddevice的回调函数，在单独的线程中运行"""
    if status:
        print(f"Audio status error: {status}")
    try:
        # 将音频数据块放入队列
        audio_queue.put_nowait(indata.copy())
    except asyncio.QueueFull:
        # 如果队列满了，可以忽略或者打印一个警告
        pass

async def mic_producer():
    """生产者：负责打开麦克风并持续捕获音频"""
    print("生产者：准备打开麦克风...")
    # 打开麦克风流
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        callback=audio_callback
    )
    with stream:
        print("麦克风已打开！现在可以开始说话了。")
        mic_ready.set()  # 发送信号，告诉消费者麦克风已就绪
        # 保持运行，让回调函数持续工作
        while True:
            await asyncio.sleep(1)

async def dg_consumer():
    """消费者：负责连接Deepgram并发送音频数据"""
    if not API_KEY:
        print("错误: DEEPGRAM_API_KEY 未设置。")
        return

    # 1. 初始化Deepgram客户端和连接
    deepgram = DeepgramClient(API_KEY)
    dg_connection = deepgram.listen.asynclive.v("1")

    # 2. 定义事件监听器
    async def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) > 0:
            print(f"Deepgram -> {sentence}")

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Error, lambda self, error, **kwargs: print(f"Deepgram Error: {error}"))

    # 3. 启动连接
    options = LiveOptions(model="nova-3", language="zh-CN", punctuate=True)
    try:
        await dg_connection.start(options)
        print("消费者：已成功连接到Deepgram。")

        # 4. 等待生产者（麦克风）就绪的信号
        print("消费者：正在等待麦克风就绪...")
        await mic_ready.wait()
        print("消费者：收到麦克风就绪信号，开始发送数据。")

        # 5. 从队列中取出数据并发送
        sent_chunks = 0
        while True:
            chunk = await audio_queue.get()
            await dg_connection.send(chunk.tobytes())
            sent_chunks += 1
            if sent_chunks == 1:
                print(">>> 已成功发送第一个音频块到Deepgram！")
            if sent_chunks % 100 == 0:
                print(f"    (已发送 {sent_chunks} 个块)")


    except Exception as e:
        print(f"消费者出现错误: {e}")
    finally:
        print("消费者：准备关闭连接。")
        await dg_connection.finish()

async def main():
    """主函数，同时运行生产者和消费者"""
    print("--- 开始健壮性测试 ---")
    print("按 Control+C 停止测试。")
    
    # 并发运行两个任务
    producer_task = asyncio.create_task(mic_producer())
    consumer_task = asyncio.create_task(dg_consumer())
    
    await asyncio.gather(producer_task, consumer_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户手动停止。")