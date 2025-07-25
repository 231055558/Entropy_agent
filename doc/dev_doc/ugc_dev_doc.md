# **EchoFlow-Agent 系统设计文档: Part 2 - 统一通信网关 (UCG) 深度设计规范**

## 1. UCG 角色与核心职责

**定位**: UCG是EchoFlow系统的**唯一、标准化、安全**的入口和出口。它不是一个简单的反向代理，而是一个有状态、有逻辑的智能网关。

**核心职责**:
1.  **协议终结与转换 (Protocol Termination & Translation)**: 终结来自外部的多种协议（HTTPS, WSS），并将其转换为系统内部统一的事件模型。
2.  **身份认证与会话管理 (Authentication & Session Management)**: 验证所有传入请求的合法性，并维护用户会话状态。
3.  **标准化与路由 (Standardization & Routing)**: 将所有异构的输入数据封装成标准的**SEO (Standard Event Object)**，并将其路由到**快速反射通道 (FRC)**。
4.  **实时流媒体处理 (Real-time Stream Handling)**: 高效处理WebSocket上的双向实时音视频流。
5.  **文件上传协调 (File Upload Coordination)**: 作为客户端与文件存储服务(FSS)之间的协调者。
6.  **响应分发 (Response Dispatching)**: 将来自**输出管理器 (OM)** 的响应，准确地分发回正确的客户端和会话。

## 2. 技术栈选型

*   **框架**: **FastAPI**。原因：原生异步、高性能、类型驱动、自动文档。
*   **Web服务器**: **Uvicorn**。原因：ASGI标准实现，速度极快。
*   **数据模型**: **Pydantic**。原因：与FastAPI深度集成，提供强大的数据验证和序列化。
*   **认证**: **JWT (JSON Web Tokens)**。原因：无状态、可扩展、适合分布式系统。
*   **WebSocket库**: FastAPI内置的`WebSocket`支持，底层由`websockets`库驱动。

## 3. API 端点与端口设计规范

UCG将监听在单个端口上（标准HTTPS为`443`，开发时可用`8000`等），通过不同的路径(Path)来区分服务。

### 3.1. HTTP/S 端点 (用于非实时通信)

#### **`POST /v1/auth/token`**
*   **功能**: 用户登录，获取访问令牌。
*   **请求体**: `{"username": "...", "password": "..."}` 或其他认证凭据。
*   **响应体**: `{"access_token": "your.jwt.token", "token_type": "bearer"}`
*   **实现**: 使用FastAPI的OAuth2PasswordBearer / JWT实现。

#### **`POST /v1/messages`**
*   **功能**: 发送非实时的、标准化的消息（如文本、文件关联信息）。
*   **认证**: 需要有效的JWT Bearer Token。
*   **请求体**: 标准化的**SEO**对象（或其简化版，UCG负责补全）。
*   **响应**: `{"status": "received", "event_id": "..."}`。这是一个快速确认，真正的响应将通过其他通道（如WSS推送或Webhook）返回。

#### **`POST /v1/files/presign`**
*   **功能**: 为文件上传请求一个预签名的URL。
*   **认证**: 需要有效的JWT。
*   **请求体**: `{"filename": "report.pdf", "mime_type": "application/pdf"}`
*   **响应体**: `{"file_id": "...", "upload_url": "https://s3.presigned.url/..."}`

### 3.2. WebSocket Secure (WSS) 端点 (用于实时通信)

#### **`WSS /v1/ws/interactive`**
*   **功能**: 建立一个全双工的实时交互通道，用于实时语音对话。
*   **连接协议**:
    1.  客户端发起WSS连接请求，并在URL查询参数或初始消息中附带JWT。例如: `wss://echo.flow/v1/ws/interactive?token=your.jwt.token`。
    2.  服务器验证JWT，成功则建立连接，失败则关闭连接。
    3.  连接建立后，客户端和服务器通过**统一的JSON消息格式**进行通信。

*   **双向JSON消息格式**:
    *   **客户端 -> 服务器 (C2S)**:
        ```json
        {
          "type": "audio_chunk" | "control",
          "payload": {
            // 如果type是audio_chunk, payload是Base64编码的PCM音频数据
            "data": "base64_encoded_pcm_chunk...", 
            
            // 如果type是control, payload是控制指令
            "action": "barge_in" | "end_of_speech" 
          }
        }
        ```
    *   **服务器 -> 客户端 (S2C)**:
        ```json
        {
          "type": "asr_transcript" | "tts_audio_chunk" | "system_event",
          "payload": {
            // ASR的中间/最终识别结果
            "text": "你好，今天天气...", 
            "is_final": false,
            
            // TTS合成的音频块
            "audio": "base64_encoded_tts_chunk...",
            
            // 系统事件，如“Agent正在思考中”
            "event_name": "agent_thinking"
          }
        }
        ```

## 4. 核心工作流详解

### 4.1. 实时语音对话流程 (在UCG视角)

1.  **连接建立**: 客户端携带JWT连接到`WSS /v1/ws/interactive`。UCG验证Token，创建一个会话状态对象，并建立与ASR服务（如Deepgram）的下游WSS连接。
2.  **上行音频流**: UCG接收到来自客户端的`audio_chunk`消息，解码Base64，然后**直接将原始PCM数据块转发**给ASR服务。
3.  **下行ASR流**: UCG接收到来自ASR服务的识别结果（JSON），将其封装成`asr_transcript` S2C消息，**转发**给客户端（用于UI实时上屏）。如果识别结果是`final`，则UCG将完整的文本封装成一个**SEO**，推送给内部的**FRC**。
4.  **FRC & OM 响应**: FRC快速处理并生成响应指令给OM。OM调用TTS服务，开始生成音频。
5.  **下行TTS流**: OM将TTS服务返回的音频块发送给UCG。UCG将其封装成`tts_audio_chunk` S2C消息，**转发**给客户端进行播放。
6.  **打断处理**: 如果UCG在转发TTS流的同时，收到了客户端发来的`barge_in`控制消息或新的`audio_chunk`，它会立即：
    *   停止向下游转发TTS音频块。
    *   向OM和FRC/DPC发送一个“中断”信号。
    *   开始处理新的上行音频流。

### 4.2. 文件上传与消息关联流程 (在UCG视角)

1.  **预签名请求**: 客户端`POST`到`/v1/files/presign`。UCG调用FSS（文件存储服务）的SDK，生成一个`file_id`和一个预签名上传URL，并将其返回给客户端。
2.  **客户端上传**: 客户端使用返回的URL直接将文件上传到FSS。**此过程流量不经过UCG**。
3.  **消息关联**: 客户端`POST`到`/v1/messages`，请求体中包含`file_id`和相关文本。
4.  **SEO创建与路由**: UCG接收到请求，验证JWT，然后创建一个包含文本和文件元数据的**SEO**对象，将其放入消息队列或直接调用FRC的处理函数。

## 5. 安全与性能考量

*   **认证**: 所有需要认证的端点都必须使用`FastAPI.Depends`注入一个依赖项，该依赖项负责解码和验证JWT。
*   **输入验证**: 永远不要信任任何客户端输入。利用Pydantic的强大验证能力，对所有请求体和查询参数进行严格的类型和格式校验。
*   **CORS (跨源资源共享)**: 配置FastAPI的`CORSMiddleware`，仅允许来自受信任域（如你的Web前端、App域名）的请求。
*   **速率限制 (Rate Limiting)**: 集成一个速率限制库（如`slowapi`），防止恶意用户通过大量请求耗尽服务器资源。
*   **并发管理**: FastAPI和Uvicorn天生就能很好地处理高并发。关键在于确保所有I/O密集型操作（如调用外部API、数据库查询）都是`async/await`的，永远不要在主事件循环中执行阻塞代码。
*   **配置管理**: 使用`.env`文件和Pydantic的`BaseSettings`来管理所有敏感配置（API密钥、数据库URL、JWT密钥），绝不硬编码在代码中。

通过这份深度设计，UCG不再是一个模糊的概念，而是一个结构清晰、职责明确、技术选型具体的工程蓝图。基于此，您和Cursor可以高效、准确地开始编码工作。