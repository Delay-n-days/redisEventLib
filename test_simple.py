
"""简单的DLL加载测试"""

import ctypes
import os
from pathlib import Path

print("当前目录:", os.getcwd())
print("当前文件:", __file__)

# 查找DLL
dll_path = Path(__file__).parent / "build/Release/redis_pubsub.dll"
print(f"DLL路径: {dll_path}")
print(f"DLL存在: {dll_path.exists()}")

if dll_path.exists():
    try:
        dll = ctypes.CDLL(str(dll_path))
        print("✓ DLL加载成功！")
        
        # 尝试调用一个函数
        redis_init = dll.redis_init
        redis_init.argtypes = [ctypes.c_char_p, ctypes.c_int]
        redis_init.restype = ctypes.c_int
        
        print("正在连接Redis...")
        result = redis_init(b"127.0.0.1", 6379)
        print(f"连接结果: {result}")
        
        if result == 0:
            print("✓ 成功连接到Redis!")
            
            # 关闭连接
            redis_close = dll.redis_close
            redis_close.argtypes = []
            redis_close.restype = ctypes.c_int
            result = redis_close()
            print(f"断开结果: {result}")
        else:
            print("✗ 连接失败")
            
    except Exception as e:
        print(f"✗ 加载DLL失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"✗ DLL文件不存在: {dll_path}")
