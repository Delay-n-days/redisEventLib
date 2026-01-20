
"""
Redis PubSub C DLL Python测试脚本 (MSVC版本)

使用ctypes调用MSVC编译的redis_pubsub.dll
"""

import ctypes
import os
import sys
import time
from ctypes import c_char_p, c_int, CFUNCTYPE
from pathlib import Path

# ==================== 加载DLL ====================

def find_dll():
    """查找DLL文件"""
    possible_paths = [
        # 当前目录
        Path("build/Release/redis_pubsub.dll"),
        # bin目录（发布后）
        Path("bin/Release/net8.0/redis_pubsub.dll"),
        # 相对路径
        Path(__file__).parent / "build/Release/redis_pubsub.dll",
        Path(__file__).parent / "bin/Release/net8.0/redis_pubsub.dll",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path.resolve())
    
    return None

dll_path = find_dll()
print(f"[INFO] Searching for redis_pubsub.dll...")

if not dll_path:
    print(f"[ERROR] DLL not found!")
    print(f"[INFO] Searched paths:")
    for path in [
        Path("build/Release/redis_pubsub.dll"),
        Path("bin/Release/net8.0/redis_pubsub.dll"),
    ]:
        print(f"       - {path.resolve()}")
    sys.exit(1)

print(f"[OK] Found DLL: {dll_path}")

try:
    # 尝试加载DLL
    redis_dll = ctypes.CDLL(dll_path)
    print(f"[OK] DLL loaded successfully")
except OSError as e:
    print(f"[ERROR] Failed to load DLL: {e}")
    sys.exit(1)

# ==================== 定义P/Invoke签名 ====================

# 回调函数类型
PubSubCallback = CFUNCTYPE(None, c_char_p, c_char_p)

# 定义DLL函数
redis_init = redis_dll.redis_init
redis_init.argtypes = [c_char_p, c_int]
redis_init.restype = c_int

redis_close = redis_dll.redis_close
redis_close.argtypes = []
redis_close.restype = c_int

redis_publish = redis_dll.redis_publish
redis_publish.argtypes = [c_char_p, c_char_p]
redis_publish.restype = c_int

redis_subscribe = redis_dll.redis_subscribe
redis_subscribe.argtypes = [c_char_p, PubSubCallback]
redis_subscribe.restype = c_int

# ==================== 回调函数 ====================

received_messages = []

def on_mychannel(channel, message):
    """mychannel频道回调"""
    channel_str = channel.decode('utf-8') if isinstance(channel, bytes) else channel
    message_str = message.decode('utf-8') if isinstance(message, bytes) else message
    
    print(f"\n[◇ CALLBACK] Received from '{channel_str}':")
    print(f"             Message: {message_str}")
    
    received_messages.append({
        'channel': channel_str,
        'message': message_str
    })

def on_events(channel, message):
    """events频道回调"""
    channel_str = channel.decode('utf-8') if isinstance(channel, bytes) else channel
    message_str = message.decode('utf-8') if isinstance(message, bytes) else message
    
    print(f"\n[◇ CALLBACK] Received from '{channel_str}':")
    print(f"             Message: {message_str}")
    
    received_messages.append({
        'channel': channel_str,
        'message': message_str
    })

# 保持回调引用
callback1 = PubSubCallback(on_mychannel)
callback2 = PubSubCallback(on_events)

# ==================== 测试函数 ====================

def run_test():
    """运行测试"""
    
    print("\n" + "=" * 60)
    print("  Redis PubSub Python测试 (MSVC DLL)")
    print("=" * 60 + "\n")
    
    # 1. 初始化连接
    print("[TEST 1] Initializing Redis connection...")
    result = redis_init(b"127.0.0.1", 6379)
    if result != 0:
        print(f"[ERROR] redis_init failed with code {result}")
        return False
    print("[OK] Connected to Redis\n")
    
    # 2. 订阅第一个频道
    print("[TEST 2] Subscribing to 'mychannel'...")
    result = redis_subscribe(b"mychannel", callback1)
    if result != 0:
        print(f"[ERROR] redis_subscribe failed with code {result}")
        redis_close()
        return False
    print("[OK] Subscribed\n")
    
    # 3. 订阅第二个频道
    print("[TEST 3] Subscribing to 'events'...")
    result = redis_subscribe(b"events", callback2)
    if result != 0:
        print(f"[ERROR] redis_subscribe failed with code {result}")
        redis_close()
        return False
    print("[OK] Subscribed\n")
    
    # 等待订阅线程启动
    time.sleep(1)
    
    # 4. 发布消息
    print("[TEST 4] Publishing messages...\n")
    
    messages = [
        (b"mychannel", b"Hello from Python - Message 1"),
        (b"mychannel", b"Hello from Python - Message 2"),
        (b"events", b"Python Event 1"),
        (b"events", b"Python Event 2"),
    ]
    
    for channel, message in messages:
        result = redis_publish(channel, message)
        print(f"[PUBLISH] Channel: {channel.decode()}")
        print(f"          Message: {message.decode()}")
        print(f"          Subscribers: {result}\n")
        time.sleep(0.5)
    
    # 等待回调处理
    time.sleep(2)
    
    # 5. 关闭连接
    print("[TEST 5] Closing connection...")
    result = redis_close()
    if result != 0:
        print(f"[ERROR] redis_close failed with code {result}")
        return False
    print("[OK] Connection closed\n")
    
    # 6. 显示结果
    print("=" * 60)
    print("  Test Results")
    print("=" * 60)
    print(f"\nTotal messages received: {len(received_messages)}\n")
    
    if received_messages:
        print("Received messages:")
        for i, msg in enumerate(received_messages, 1):
            print(f"  [{i}] Channel: {msg['channel']}")
            print(f"      Message: {msg['message']}")
    
    print()
    
    # 验证结果
    if len(received_messages) >= 4:
        print("=" * 60)
        print("  ✓ All tests passed!")
        print("=" * 60)
        return True
    else:
        print("=" * 60)
        print(f"  ✗ Test failed: Expected >= 4 messages, got {len(received_messages)}")
        print("=" * 60)
        return False

# ==================== 主程序 ====================

if __name__ == "__main__":
    try:
        success = run_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        try:
            redis_close()
        except:
            pass
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        try:
            redis_close()
        except:
            pass
        sys.exit(1)
