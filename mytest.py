from redis_client import RedisPubSubDLL


client = RedisPubSubDLL("./redis_pubsub.dll")
client.connect(hostname='localhost', port=6379)
def callback_mychannel(channel, message):
    print(f"[CALLBACK] mychannel: {channel} -> {message}")
client.subscribe('mychannel', callback_mychannel)
client.publish('mychannel', 'Hello from mytest.py')
client.wait(1)  # 等待一段时间以确保消息被处理
client.disconnect()
