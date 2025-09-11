# asr_local_stream_v4.8_final_final.py

import asyncio
import logging
import os
import sys
import sounddevice as sd
import numpy as np
from dotenv import load_dotenv

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveOptions,
    LiveTranscriptionEvents,
)

load_dotenv()
API_KEY = os.getenv("DEEPGRAM_API_KEY")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.int16

class ASRClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Deepgram API Key is required.")
        
        config = DeepgramClientOptions(api_key=api_key, verbose=logging.WARNING)
        self.deepgram = DeepgramClient(config=config)
        self.audio_queue = asyncio.Queue()
        self.is_speaking = False
        self.connection = None

    def _audio_callback(self, indata, frames, time, status):
        if status: logging.warning(f"Audio status error: {status}")
        try: self.audio_queue.put_nowait(indata.copy())
        except asyncio.QueueFull: logging.warning("Audio queue is full, dropping a frame.")

    async def _start_microphone(self):
        logging.info("Starting microphone...")
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, callback=self._audio_callback):
            while self.is_speaking: await asyncio.sleep(0.1)
        logging.info("Microphone stopped.")

    async def _send_audio_from_queue(self):
        sent_chunks = 0
        try:
            while self.is_speaking:
                try:
                    chunk = await asyncio.wait_for(self.audio_queue.get(), timeout=1.0)
                    if self.connection:
                        await self.connection.send(chunk.tobytes())
                        sent_chunks += 1
                        if sent_chunks == 1:
                            logging.info(">>> 第一个音频块已成功发送！现在Deepgram正在处理...")
                except asyncio.TimeoutError: continue
        except Exception as e: logging.error(f"Error sending audio: {e}", exc_info=True)

    async def transcribe(self):
        try:
            self.connection = self.deepgram.listen.asyncwebsocket.v("1")
            
            # --- 关键修正：将回调函数绑定到类的实例方法 ---
            self.connection.on(LiveTranscriptionEvents.Open, self.on_open)
            self.connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
            self.connection.on(LiveTranscriptionEvents.Error, self.on_error)
            self.connection.on(LiveTranscriptionEvents.Close, self.on_close)
            self.connection.on(LiveTranscriptionEvents.UtteranceEnd, self.on_utterance_end)
            self.connection.on(LiveTranscriptionEvents.SpeechStarted, self.on_speech_started)

            options = LiveOptions(
                model="nova-2-general", language="zh-CN", encoding="linear16",
                sample_rate=SAMPLE_RATE, channels=CHANNELS, punctuate=True,
                smart_format=True, interim_results=True, utterance_end_ms="1000",
                vad_events=True,
            )

            await self.connection.start(options)
            self.is_speaking = True
            
            mic_task = asyncio.create_task(self._start_microphone())
            sender_task = asyncio.create_task(self._send_audio_from_queue())
            
            await asyncio.gather(mic_task, sender_task)

        except Exception as e: logging.error(f"Could not start transcription: {e}", exc_info=True)
        finally:
            if self.connection: await self.connection.finish()
            self.is_speaking = False
            logging.info("Transcription process finished.")
    
    # --- 最终修正版的回调函数签名 ---
    # 它们是普通的实例方法，接收self，并且能够接收SDK传来的额外参数
    
    async def on_open(self, dg_connection, open, **kwargs):
        logging.info(f"Connection Open: {open}")

    async def on_error(self, dg_connection, error, **kwargs):
        logging.error(f"Deepgram error: {error}")

    async def on_close(self, dg_connection, close, **kwargs):
        logging.info(f"Connection closed: {close}")

    async def on_speech_started(self, dg_connection, speech_started, **kwargs):
        logging.info("--- VAD: 检测到语音开始 ---")

    async def on_utterance_end(self, dg_connection, utterance_end, **kwargs):
        sys.stdout.write("\n")
        logging.info("--- VAD: 检测到一句话结束 ---")

    async def on_message(self, dg_connection, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if len(transcript) == 0: return
            
        if result.is_final:
            sys.stdout.write("\n")
            logging.info(f"[FINAL]: {transcript}")
        else:
            sys.stdout.write(f"        (Interim): {transcript.ljust(60)}" + '\r')
            sys.stdout.flush()

    def stop(self):
        logging.info("Stop requested.")
        self.is_speaking = False

async def main():
    if not API_KEY: logging.error("DEEPGRAM_API_KEY not set in .env file."); return

    client = ASRClient(API_KEY)
    transcribe_task = asyncio.create_task(client.transcribe())

    print("\n--- 启动实时语音识别测试 v4 (最终回调函数修正) ---")
    print("--- 按下 Enter 键停止程序 ---\n")
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, input)
    
    client.stop()
    await transcribe_task
    print("\nProgram finished.")

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\nProgram interrupted by user.")