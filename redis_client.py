
# -*- coding: utf-8 -*-
"""
Redis PubSub C DLL Python包装类

提供高级接口封装C DLL的Redis发布/订阅功能
"""

import ctypes
import os
import sys
import time
from ctypes import c_char_p, c_int, CFUNCTYPE
from threading import Thread, Event, Lock
from typing import Callable, Dict, Any, Optional
import traceback


class RedisPubSubDLL:
    """Redis PubSub C DLL包装类"""
    
    # 回调函数类型
    _PubSubCallback = CFUNCTYPE(None, c_char_p, c_char_p)
    
    def __init__(self, dll_path: str = None):
        """
        初始化Redis PubSub客户端
        
        Args:
            dll_path: DLL文件路径，默认为build/libredis_pubsub.dll
        
        Raises:
            FileNotFoundError: DLL文件不存在
            OSError: DLL加载失败
        """
        self._dll = None
        self._callbacks: Dict[str, Callable] = {}
        self._dll_callbacks: Dict[str, self._PubSubCallback] = {}
        self._lock = Lock()
        self._connected = False
        self._dll_path = dll_path or self._get_default_dll_path()
        
        self._load_dll()
        self._setup_functions()
    
    def _get_default_dll_path(self) -> str:
        """获取默认DLL路径 (MSVC编译版本)"""
        # 优先使用MSVC编译的版本
        possible_paths = [
            # Release版本 (MSVC)
            os.path.join(os.path.dirname(__file__), "build/Release/redis_pubsub.dll"),
            # 备用路径
            os.path.join(os.path.dirname(__file__), "build/Release/redis_pubsub.dll"),
        ]
        
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                return abs_path
        
        # 如果都不存在，返回第一个路径并让加载函数报错
        return os.path.abspath(possible_paths[0])
    
    def _load_dll(self):
        """加载DLL文件"""
        # print(f"[INFO] Loading DLL from: {self._dll_path}")
        
        # 转换为绝对路径
        abs_dll_path = os.path.abspath(self._dll_path)
        
        if not os.path.exists(abs_dll_path):
            print(f"[ERROR] DLL not found: {abs_dll_path}")
            raise FileNotFoundError(f"DLL not found: {abs_dll_path}")
        
        try:
            # 添加DLL目录到搜索路径
            build_dir = os.path.dirname(abs_dll_path)
            if hasattr(os, 'add_dll_directory') and build_dir and os.path.isabs(build_dir):
                try:
                    os.add_dll_directory(build_dir)
                    print(f"[INFO] Added DLL search path: {build_dir}")
                except OSError as e:
                    print(f"[WARNING] Failed to add DLL directory: {e}")
            
            self._dll = ctypes.CDLL(abs_dll_path)
            # print("[OK] DLL loaded successfully")
        except OSError as e:
            print(f"[ERROR] Failed to load DLL: {e}")
            raise
    
    def _setup_functions(self):
        """设置DLL函数签名"""
        if not self._dll:
            raise RuntimeError("DLL not loaded")
        
        # redis_init(const char* hostname, int port) -> int
        self._redis_init = self._dll.redis_init
        self._redis_init.argtypes = [c_char_p, c_int]
        self._redis_init.restype = c_int
        
        # redis_close() -> int
        self._redis_close = self._dll.redis_close
        self._redis_close.argtypes = []
        self._redis_close.restype = c_int
        
        # redis_publish(const char* channel, const char* message) -> int
        self._redis_publish = self._dll.redis_publish
        self._redis_publish.argtypes = [c_char_p, c_char_p]
        self._redis_publish.restype = c_int
        
        # redis_subscribe(const char* channel, PubSubCallback callback) -> int
        self._redis_subscribe = self._dll.redis_subscribe
        self._redis_subscribe.argtypes = [c_char_p, self._PubSubCallback]
        self._redis_subscribe.restype = c_int
    
    def connect(self, hostname: str = "127.0.0.1", port: int = 6379) -> bool:
        """
        连接到Redis服务器
        
        Args:
            hostname: Redis主机名，默认127.0.0.1
            port: Redis端口，默认6379
        
        Returns:
            True表示连接成功，False表示失败
        """
        try:
            with self._lock:
                result = self._redis_init(hostname.encode('utf-8'), port)
                if result == 0:
                    self._connected = True
                    # print(f"[OK] Connected to Redis {hostname}:{port}")
                    return True
                else:
                    print(f"[ERROR] Connection failed with code {result}")
                    return False
        except Exception as e:
            print(f"[ERROR] Connection error: {e}")
            traceback.print_exc()
            return False
    
    def disconnect(self) -> bool:
        """
        断开与Redis的连接
        
        Returns:
            True表示断开成功
        """
        try:
            with self._lock:
                result = self._redis_close()
                self._connected = False
                self._callbacks.clear()
                self._dll_callbacks.clear()
                # print("[OK] Disconnected from Redis")
                return result == 0
        except Exception as e:
            print(f"[ERROR] Disconnection error: {e}")
            return False
    
    def publish(self, channel: str, message: str) -> int:
        """
        发布消息到指定频道
        
        Args:
            channel: 频道名称
            message: 消息内容
        
        Returns:
            接收消息的订阅者数量，-1表示发送失败
        """
        if not self._connected:
            print("[ERROR] Not connected to Redis")
            return -1
        
        try:
            with self._lock:
                result = self._redis_publish(
                    channel.encode('utf-8'),
                    message.encode('utf-8')
                )
                # print(f"[PUBLISH] Channel: {channel} | Message: {message}")
                # print(f"           Subscribers: {result}")
                return result
        except Exception as e:
            print(f"[ERROR] Publish error: {e}")
            traceback.print_exc()
            return -1
    
    def subscribe(self, channel: str, callback: Callable[[str, str], None]) -> bool:
        """
        订阅频道
        
        Args:
            channel: 频道名称
            callback: 回调函数，签名为 callback(channel: str, message: str) -> None
        
        Returns:
            True表示订阅成功
        """
        if not self._connected:
            print("[ERROR] Not connected to Redis")
            return False
        
        if not callable(callback):
            print("[ERROR] Callback must be callable")
            return False
        
        try:
            with self._lock:
                # 创建C回调函数
                def c_callback(channel_ptr, message_ptr):
                    try:
                        channel_str = channel_ptr.decode('utf-8') if isinstance(channel_ptr, bytes) else channel_ptr
                        message_str = message_ptr.decode('utf-8') if isinstance(message_ptr, bytes) else message_ptr
                        # print(f"\n[CALLBACK] Received from '{channel_str}':")
                        # print(f"           Message: {message_str}")
                        callback(channel_str, message_str)
                    except Exception as e:
                        print(f"[ERROR] Callback error: {e}")
                        traceback.print_exc()
                
                # 保存Python回调
                self._callbacks[channel] = callback
                
                # 创建并保存C回调（必须保持引用）
                dll_callback = self._PubSubCallback(c_callback)
                self._dll_callbacks[channel] = dll_callback
                
                # 调用DLL订阅函数
                result = self._redis_subscribe(channel.encode('utf-8'), dll_callback)
                
                if result == 0:
                    # print(f"[OK] Subscribed to channel: {channel}")
                    return True
                else:
                    print(f"[ERROR] Subscribe failed with code {result}")
                    del self._callbacks[channel]
                    del self._dll_callbacks[channel]
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Subscribe error: {e}")
            traceback.print_exc()
            return False
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    def get_subscribed_channels(self) -> list:
        """获取已订阅的频道列表"""
        return list(self._callbacks.keys())
    
    def wait(self, duration: float = 1.0):
        """
        等待指定时间（用于处理回调）
        
        Args:
            duration: 等待时间（秒）
        """
        time.sleep(duration)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  Redis PubSub类使用演示")
    print("=" * 60)
    print()
    
    # 方法1：使用上下文管理器（推荐）
    try:
        with RedisPubSubDLL() as client:
            # 连接
            if not client.connect():
                print("Failed to connect")
                sys.exit(1)
            
            # 定义回调函数
            def on_message_1(channel: str, message: str):
                print(f"         [Handler 1] Got message: {message}")
            
            def on_message_2(channel: str, message: str):
                print(f"         [Handler 2] Got message: {message}")
            
            # 订阅频道
            client.subscribe("mychannel", on_message_1)
            client.subscribe("events", on_message_2)
            
            print(f"\nSubscribed channels: {client.get_subscribed_channels()}\n")
            
            # 等待订阅线程启动
            client.wait(1)
            
            # 发布消息
            print("[TEST] Publishing messages...")
            client.publish("mychannel", "Hello World 1")
            client.wait(0.5)
            
            client.publish("mychannel", "Hello World 2")
            client.wait(0.5)
            
            client.publish("events", "Event 1")
            client.wait(0.5)
            
            client.publish("events", "Event 2")
            client.wait(2)
            
            print("\n[OK] Test completed")
    
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        sys.exit(1)
