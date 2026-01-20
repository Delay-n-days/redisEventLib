#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的Redis PubSub Python演示
同时测试redis_client.py类和原始ctypes调用
"""

from redis_client import RedisPubSubDLL
import time

print("=" * 60)
print("  Redis PubSub Python完整演示")
print("=" * 60)
print()

# 使用类包装方式
print("[TEST 1] 使用RedisPubSubDLL类")
print("-" * 60)

try:
    # 创建客户端实例
    client = RedisPubSubDLL("./redis_pubsub.dll")
    
    # 连接到Redis
    if not client.connect(hostname='127.0.0.1', port=6379):
        print("[ERROR] Failed to connect")
        exit(1)
    
    # 定义回调函数
    received_messages = []
    
    def on_mychannel(channel, message):
        print(f"[CALLBACK mychannel] {channel} -> {message}")
        received_messages.append((channel, message))
    
    def on_events(channel, message):
        print(f"[CALLBACK events] {channel} -> {message}")
        received_messages.append((channel, message))
    
    # 订阅频道
    print("\n订阅频道...")
    client.subscribe('mychannel', on_mychannel)
    client.subscribe('events', on_events)
    
    print(f"已订阅: {client.get_subscribed_channels()}\n")
    
    # 等待订阅线程启动
    client.wait(1)
    
    # 发布消息
    print("发布消息...")
    client.publish('mychannel', 'Test message 1')
    client.wait(0.5)
    
    client.publish('mychannel', 'Test message 2')
    client.wait(0.5)
    
    client.publish('events', 'Event message 1')
    client.wait(0.5)
    
    client.publish('events', 'Event message 2')
    client.wait(2)
    
    # 显示结果
    print("\n" + "=" * 60)
    print(f"收到消息数: {len(received_messages)}")
    for i, (ch, msg) in enumerate(received_messages, 1):
        print(f"  [{i}] {ch}: {msg}")
    
    # 关闭连接
    client.disconnect()
    
    if len(received_messages) >= 4:
        print("\n✓ 测试成功!")
    else:
        print(f"\n✗ 测试失败: 期望>=4条消息，实际{len(received_messages)}条")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
