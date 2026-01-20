# Redis PubSub C# .NET 8 客户端

## 文件结构

```
redisEventLib/
├── RedisPubSubClient.cs       # C#客户端源代码（单文件）
├── RedisPubSubClient.csproj   # .NET 8 项目文件
├── build/
│   ├── libredis_pubsub.dll    # 编译的C DLL
│   └── libhiredis.dll         # Redis客户端库DLL
└── hiredis/                   # hiredis源代码
```

## 环境要求

- **.NET 8 SDK** 或更高版本
  - 下载: https://dotnet.microsoft.com/download/dotnet/8.0

- **Redis 服务器**（运行在 127.0.0.1:6379）

## 编译和运行

### 方法1：使用dotnet run（推荐）

```powershell
cd e:\clang\redisEventLib
dotnet run --project RedisPubSubClient.csproj
```

### 方法2：编译后运行

```powershell
cd e:\clang\redisEventLib

# 编译
dotnet build -c Release

# 运行
cd bin/Release/net8.0
.\RedisPubSubClient.exe
```

### 方法3：发布为独立应用

```powershell
dotnet publish -c Release -o publish

cd publish
.\RedisPubSubClient.exe
```

## 代码使用示例

### 基本用法

```csharp
using (var client = new RedisPubSubClient())
{
    // 连接到Redis
    if (!client.Connect("127.0.0.1", 6379))
    {
        Console.WriteLine("连接失败");
        return;
    }
    
    // 定义回调函数
    void OnMessage(string channel, string message)
    {
        Console.WriteLine($"收到消息: {message}");
    }
    
    // 订阅频道
    client.Subscribe("mychannel", OnMessage);
    
    // 发布消息
    client.Publish("mychannel", "Hello Redis!");
    
    // 等待一段时间
    client.Wait(2000);
}
```

### 多频道订阅

```csharp
using (var client = new RedisPubSubClient())
{
    client.Connect();
    
    // 订阅多个频道
    client.Subscribe("notifications", (ch, msg) => 
    {
        Console.WriteLine($"[通知] {msg}");
    });
    
    client.Subscribe("alerts", (ch, msg) => 
    {
        Console.WriteLine($"[警报] {msg}");
    });
    
    // 发布消息
    client.Publish("notifications", "新通知来了");
    client.Publish("alerts", "系统警报");
    
    client.Wait(2000);
}
```

### 异步操作

```csharp
using (var client = new RedisPubSubClient())
{
    await client.ConnectAsync("127.0.0.1", 6379);
    
    client.Subscribe("events", OnEvent);
    
    // 异步等待
    await client.WaitAsync(3000);
}
```

## API 文档

### 主要方法

#### `bool Connect(string hostname = "127.0.0.1", int port = 6379)`
连接到Redis服务器
- **参数:**
  - `hostname`: Redis主机名（默认: 127.0.0.1）
  - `port`: Redis端口（默认: 6379）
- **返回:** 连接成功返回true，失败返回false

#### `bool Disconnect()`
断开与Redis的连接
- **返回:** 断开成功返回true

#### `int Publish(string channel, string message)`
发布消息到指定频道
- **参数:**
  - `channel`: 频道名称
  - `message`: 消息内容
- **返回:** 接收消息的订阅者数量，-1表示发送失败

#### `bool Subscribe(string channel, PubSubCallback callback)`
订阅指定频道
- **参数:**
  - `channel`: 频道名称
  - `callback`: 回调函数，签名: `(string channel, string message) => {}`
- **返回:** 订阅成功返回true

#### `bool IsConnected`
检查是否已连接到Redis

#### `string[] GetSubscribedChannels()`
获取已订阅的频道列表

#### `void Wait(int milliseconds = 1000)`
等待指定时间（同步）

#### `async Task WaitAsync(int milliseconds = 1000)`
异步等待指定时间

#### `void Dispose()`
释放资源（使用using语句自动调用）

## 常见问题

### 找不到DLL

**症状:** `DllNotFoundException: Unable to load DLL 'libredis_pubsub.dll'`

**解决:**
1. 确保DLL文件在build目录中
2. 确保.csproj中配置了DLL复制到输出目录
3. 运行: `dotnet build -c Release`

### 无法连接到Redis

**症状:** `Connection failed with code -1`

**解决:**
1. 确保Redis服务器正在运行
   ```powershell
   # Windows上安装并启动Redis
   redis-server.exe
   ```
2. 检查Redis地址和端口是否正确

### 回调未被调用

**症状:** 消息发布但没有收到回调

**解决:**
1. 确保订阅函数返回true（表示订阅成功）
2. 等待足够长的时间让线程处理消息
3. 检查是否有其他Redis客户端订阅了相同频道

## 性能提示

- 使用单个client实例处理多个频道，不要频繁创建/销毁
- 在高吞吐量场景下，使用连接池
- 回调函数应该快速返回，不应做阻塞操作

## 测试

运行内置测试程序：

```powershell
dotnet run --project RedisPubSubClient.csproj
```

预期输出：
```
========================================
  Redis PubSub C# .NET 8 客户端演示
========================================

[TEST 1] Connecting to Redis...
[✓] Connected to Redis 127.0.0.1:6379

[TEST 2] Subscribing to channels...
[✓] Subscribed to channel: mychannel
[✓] Subscribed to channel: events

[INFO] Subscribed channels: mychannel, events

[TEST 3] Publishing messages...

[PUBLISH] Channel: mychannel
          Message: Hello World 1
          Subscribers: 1

[◇ CALLBACK] Received from 'mychannel':
             Message: Hello World 1
           [Handler 1] Message received: Hello World 1

...

[✓] Test completed successfully!
```

## 许可证

MIT
