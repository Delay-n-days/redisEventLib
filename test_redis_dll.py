
# -*- coding: utf-8 -*-
"""
Redis PubSub C DLL Python测试脚本

接口说明：
1. redis_init(hostname, port) - 初始化Redis连接
2. redis_publish(channel, message) - 发布消息
3. redis_subscribe(channel, callback) - 订阅消息（回调函数）
4. redis_close() - 关闭连接
"""

import ctypes
import os
import time
import sys
from ctypes import c_char_p, c_int, CFUNCTYPE, POINTER
from threading import Thread, Event

# ==================== 加载DLL ====================

# 获取DLL路径
dll_path = os.path.join(os.path.dirname(__file__), "build", "libredis_pubsub.dll")
dll_path = os.path.abspath(dll_path)
print(f"[INFO] Loading DLL from: {dll_path}")

if not os.path.exists(dll_path):
    print(f"[ERROR] DLL not found: {dll_path}")
    print(f"[INFO] Current directory: {os.getcwd()}")
    print(f"[INFO] Available files in build:")
    build_dir = os.path.join(os.path.dirname(__file__), "build")
    if os.path.exists(build_dir):
        for f in os.listdir(build_dir):
            print(f"      {f}")
    sys.exit(1)

try:
    # 确保libhiredis.dll也在PATH中
    build_dir = os.path.dirname(dll_path)
    os.add_dll_directory(build_dir)
    
    redis_dll = ctypes.CDLL(dll_path)
    print("[OK] DLL loaded successfully")
except Exception as e:
    print(f"[ERROR] Failed to load DLL: {e}")
    print(f"[DEBUG] Exception type: {type(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==================== 定义回调函数类型 ====================

# 回调函数签名: void callback(const char* channel, const char* message)
PubSubCallback = CFUNCTYPE(None, c_char_p, c_char_p)

# ==================== 定义DLL函数 ====================

# int redis_init(const char* hostname, int port)
redis_init = redis_dll.redis_init
redis_init.argtypes = [c_char_p, c_int]
redis_init.restype = c_int

# int redis_close()
redis_close = redis_dll.redis_close
redis_close.argtypes = []
redis_close.restype = c_int

# int redis_publish(const char* channel, const char* message)
redis_publish = redis_dll.redis_publish
redis_publish.argtypes = [c_char_p, c_char_p]
redis_publish.restype = c_int

# int redis_subscribe(const char* channel, PubSubCallback callback)
redis_subscribe = redis_dll.redis_subscribe
redis_subscribe.argtypes = [c_char_p, PubSubCallback]
redis_subscribe.restype = c_int

# ==================== 回调函数实现 ====================

received_messages = []
stop_event = Event()

def callback_mychannel(channel, message):
    """mychannel 频道的回调函数"""
    channel_str = channel.decode('utf-8') if isinstance(channel, bytes) else channel
    message_str = message.decode('utf-8') if isinstance(message, bytes) else message
    
    print(f"\n[CALLBACK] mychannel received:")
    print(f"           Channel: {channel_str}")
    print(f"           Message: {message_str}")
    
    received_messages.append({
        'channel': channel_str,
        'message': message_str
    })

def callback_events(channel, message):
    """events 频道的回调函数"""
    channel_str = channel.decode('utf-8') if isinstance(channel, bytes) else channel
    message_str = message.decode('utf-8') if isinstance(message, bytes) else message
    
    print(f"\n[CALLBACK] events received:")
    print(f"           Channel: {channel_str}")
    print(f"           Message: {message_str}")
    
    received_messages.append({
        'channel': channel_str,
        'message': message_str
    })

# 创建回调对象（必须保持引用，否则会被垃圾回收）
callback1 = PubSubCallback(callback_mychannel)
callback2 = PubSubCallback(callback_events)

# ==================== 测试函数 ====================

def test_redis_pubsub():
    """测试Redis发布/订阅功能"""
    
    print("=" * 60)
    print("  Redis PubSub C DLL Python测试")
    print("=" * 60)
    print()
    
    # 1. 初始化连接
    print("[TEST 1] redis_init('127.0.0.1', 6379)")
    result = redis_init(b"127.0.0.1", 6379)
    if result != 0:
        print(f"[FAILED] redis_init returned {result}")
        return False
    print("[PASSED]\n")
    
    # 2. 订阅频道
    print("[TEST 2] redis_subscribe('mychannel', callback)")
    result = redis_subscribe(b"mychannel", callback1)
    if result != 0:
        print(f"[FAILED] redis_subscribe returned {result}")
        redis_close()
        return False
    print("[PASSED]\n")
    
    # 3. 订阅第二个频道
    print("[TEST 3] redis_subscribe('events', callback)")
    result = redis_subscribe(b"events", callback2)
    if result != 0:
        print(f"[FAILED] redis_subscribe returned {result}")
        redis_close()
        return False
    print("[PASSED]\n")
    
    # 等待订阅线程启动
    time.sleep(1)
    
    # 4. 发布消息到 mychannel
    print("[TEST 4] redis_publish('mychannel', 'Hello from Python - Message 1')")
    result = redis_publish(b"mychannel", b"Hello from Python - Message 1")
    print(f"         Subscribers count: {result}")
    print("[PASSED]\n")
    
    time.sleep(0.5)
    
    # 5. 发布多条消息到 mychannel
    print("[TEST 5] redis_publish('mychannel', 'Hello from Python - Message 2')")
    result = redis_publish(b"mychannel", b"Hello from Python - Message 2")
    print(f"         Subscribers count: {result}")
    print("[PASSED]\n")
    
    time.sleep(0.5)
    
    # 6. 发布消息到 events
    print("[TEST 6] redis_publish('events', 'Event: test_event_1')")
    result = redis_publish(b"events", b"Event: test_event_1")
    print(f"         Subscribers count: {result}")
    print("[PASSED]\n")
    
    time.sleep(0.5)
    
    # 7. 发布更多消息
    print("[TEST 7] redis_publish('events', 'Event: test_event_2')")
    result = redis_publish(b"events", b"Event: test_event_2")
    print(f"         Subscribers count: {result}")
    print("[PASSED]\n")
    
    # 等待回调执行
    time.sleep(2)
    
    # 8. 关闭连接
    print("[TEST 8] redis_close()")
    result = redis_close()
    if result != 0:
        print(f"[FAILED] redis_close returned {result}")
        return False
    print("[PASSED]\n")
    
    # 验证结果
    print("=" * 60)
    print("  测试结果")
    print("=" * 60)
    print(f"\n总收到消息数: {len(received_messages)}")
    print("\n接收到的消息列表:")
    for i, msg in enumerate(received_messages, 1):
        print(f"  [{i}] {msg['channel']}: {msg['message']}")
    
    print("\n" + "=" * 60)
    if len(received_messages) >= 4:
        print("  ✓ 测试通过！所有功能正常工作")
        print("=" * 60)
        return True
    else:
        print("  ✗ 测试失败！接收消息数不足")
        print("=" * 60)
        return False

# ==================== 主程序 ====================

if __name__ == "__main__":
    try:
        success = test_redis_pubsub()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        redis_close()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        redis_close()
        sys.exit(1)
