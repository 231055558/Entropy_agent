# main.py

# 1. 从 fastapi 库中导入 FastAPI 类
from fastapi import FastAPI

# 2. 创建一个 FastAPI 的“实例”，我们给它取名叫 app
#    这个 app 就是我们整个Web应用的核心
app = FastAPI(
    title="EchoFlow Unified Communication Gateway (UCG)",
    description="The single entry point for all EchoFlow services.",
    version="1.0.0",
)

# 3. 定义一个“路径操作” (Path Operation)
#    @app.get("/") 是一个“装饰器 (decorator)”，它告诉FastAPI：
#    当有用户通过 GET 方法访问网站的根路径("/")时，
#    请执行紧跟在它下面的这个函数。
@app.get("/")
def read_root():
    """
    This is the root endpoint of the UCG.
    It can be used for health checks.
    """
    # 4. 函数的返回值就是API的响应内容。
    #    FastAPI会自动把它转换成JSON格式。
    return {"message": "Hello, UCG! The gateway is running."}