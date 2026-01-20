# Redis 发布/订阅演示程序

## 文件结构

```
redisEventLib/
├── hiredis/              # hiredis库源代码
│   └── build/            # 编译输出（libhiredis.dll）
├── publisher.c           # 发布者源代码
├── subscriber.c          # 订阅者源代码
├── CMakeLists.txt        # 示例程序编译配置
└── build/                # 编译输出目录
    ├── publisher.exe     # 发布者可执行文件
    ├── subscriber.exe    # 订阅者可执行文件
    └── libhiredis.dll    # hiredis动态库
```

## 使用方法

### 前提条件

1. **Redis服务器** - 需要运行在 `127.0.0.1:6379`
   - 如果没有安装，可以使用 WSL、Docker 或直接下载 Redis Windows 版本
   - Redis官方下载：https://github.com/microsoftarchive/redis/releases

### 运行演示

**终端1 - 启动订阅者（先启动）**

```powershell
cd e:\clang\redisEventLib\build
.\subscriber.exe
```

输出示例：
```
========== Redis Subscriber Demo ==========
Connecting to Redis at 127.0.0.1:6379...
Connected successfully!

Subscribing to channel 'mychannel'...
Waiting for messages (Ctrl+C to exit)...

[Info] Subscribed to 'mychannel' (total subscriptions: 1)

```

**终端2 - 启动发布者**

```powershell
cd e:\clang\redisEventLib\build
.\publisher.exe
```

输出示例：
```
========== Redis Publisher Demo ==========
Connecting to Redis at 127.0.0.1:6379...
Connected successfully!

Publishing messages...
[Published] Channel: mychannel | Message: Hello from publisher - Message 1
            Subscribers received: 1
[Published] Channel: mychannel | Message: Hello from publisher - Message 2
            Subscribers received: 1
[Published] Channel: mychannel | Message: Hello from publisher - Message 3
            Subscribers received: 1
[Published] Channel: mychannel | Message: Hello from publisher - Message 4
            Subscribers received: 1
[Published] Channel: mychannel | Message: Hello from publisher - Message 5
            Subscribers received: 1

✓ All messages published!
```

**订阅者接收到消息**

```
[Message #1] From channel 'mychannel':
             Hello from publisher - Message 1

[Message #2] From channel 'mychannel':
             Hello from publisher - Message 2

[Message #3] From channel 'mychannel':
             Hello from publisher - Message 3

[Message #4] From channel 'mychannel':
             Hello from publisher - Message 4

[Message #5] From channel 'mychannel':
             Hello from publisher - Message 5
```

## 代码关键部分解析

### 连接到Redis
```c
redisContext *c = redisConnect("127.0.0.1", 6379);
```

### 发布消息
```c
redisReply *reply = redisCommand(c, "PUBLISH mychannel %s", message);
printf("Subscribers received: %lld\n", reply->integer);  // 接收消息的订阅者数量
```

### 订阅频道
```c
redisCommand(c, "SUBSCRIBE mychannel");
while (redisGetReply(c, (void**)&reply) == REDIS_OK) {
    if (reply->type == REDIS_REPLY_ARRAY && reply->elements == 3) {
        if (strcmp(reply->element[0]->str, "message") == 0) {
            printf("Channel: %s, Message: %s\n", 
                   reply->element[1]->str, 
                   reply->element[2]->str);
        }
    }
}
```

## 常见问题

### 无法连接到Redis

```
ERROR: Can't connect to the server: 127.0.0.1:6379
```

**解决方案：** 确保Redis服务器正在运行
- Windows上安装并启动Redis：`redis-server.exe`
- 或使用Docker：`docker run -d -p 6379:6379 redis`
- 或使用WSL运行Redis

### 多订阅者测试

可以在多个终端启动多个 `subscriber.exe`，然后运行 `publisher.exe`，所有订阅者都会收到消息。

## 修改配置

要修改连接地址或端口，编辑源文件中的：

**publisher.c:**
```c
const char *hostname = "127.0.0.1";
int port = 6379;
```

**subscriber.c:**
```c
const char *hostname = "127.0.0.1";
int port = 6379;
```

然后重新编译：
```powershell
cd e:\clang\redisEventLib\build
cmake --build . --config Release
```

## 进阶：修改消息数量

编辑 `publisher.c` 中的循环次数（当前是5条消息）：
```c
for (int i = 0; i < 5; i++) {  // 修改这个数字
    // ...
}
```

## 清理编译

```powershell
cd e:\clang\redisEventLib
Remove-Item -Recurse -Force build
```

---

## C# .NET 8 客户端

如果你想使用C#来调用Redis PubSub DLL，请查看 [README_CSHARP.md](README_CSHARP.md)

### 快速开始

```bash
dotnet run --project RedisPubSubClient.csproj
```

### C# 使用示例

```csharp
using (var client = new RedisPubSubClient())
{
    client.Connect("127.0.0.1", 6379);
    
    // 订阅频道
    client.Subscribe("mychannel", (channel, message) => 
    {
        Console.WriteLine($"收到消息: {message}");
    });
    
    // 发布消息
    client.Publish("mychannel", "Hello Redis!");
    
    client.Wait(2000);
}
```
