using System;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Generic;

/// <summary>
/// Redis PubSub C DLL的C#包装类
/// 使用P/Invoke调用C DLL函数
/// </summary>
public class RedisPubSubClient : IDisposable
{
    /// <summary>
    /// 回调函数委托
    /// </summary>
    public delegate void PubSubCallback(string channel, string message);

    // ==================== P/Invoke声明 ====================

    /// <summary>
    /// 回调函数的C函数签名
    /// </summary>
    private delegate void NativePubSubCallback(IntPtr channel, IntPtr message);

    /// <summary>
    /// int redis_init(const char* hostname, int port)
    /// </summary>
    [DllImport("redis_pubsub.dll", CallingConvention = CallingConvention.Cdecl)]
    private static extern int redis_init([MarshalAs(UnmanagedType.LPStr)] string hostname, int port);

    /// <summary>
    /// int redis_close()
    /// </summary>
    [DllImport("redis_pubsub.dll", CallingConvention = CallingConvention.Cdecl)]
    private static extern int redis_close();

    /// <summary>
    /// int redis_publish(const char* channel, const char* message)
    /// </summary>
    [DllImport("redis_pubsub.dll", CallingConvention = CallingConvention.Cdecl)]
    private static extern int redis_publish(
        [MarshalAs(UnmanagedType.LPStr)] string channel,
        [MarshalAs(UnmanagedType.LPStr)] string message);

    /// <summary>
    /// int redis_subscribe(const char* channel, PubSubCallback callback)
    /// </summary>
    [DllImport("redis_pubsub.dll", CallingConvention = CallingConvention.Cdecl)]
    private static extern int redis_subscribe(
        [MarshalAs(UnmanagedType.LPStr)] string channel,
        NativePubSubCallback callback);

    // ==================== 成员变量 ====================

    private bool _connected = false;
    private Dictionary<string, PubSubCallback> _callbacks = new();
    private Dictionary<string, NativePubSubCallback> _nativeCallbacks = new();
    private readonly object _lockObj = new object();

    // ==================== 公共方法 ====================

    /// <summary>
    /// 连接到Redis服务器
    /// </summary>
    public bool Connect(string hostname = "127.0.0.1", int port = 6379)
    {
        lock (_lockObj)
        {
            try
            {
                int result = redis_init(hostname, port);
                if (result == 0)
                {
                    _connected = true;
                    Console.WriteLine($"[✓] Connected to Redis {hostname}:{port}");
                    return true;
                }
                else
                {
                    Console.WriteLine($"[✗] Connection failed with code {result}");
                    return false;
                }
            }
            catch (DllNotFoundException ex)
            {
                Console.WriteLine($"[✗] DLL not found: {ex.Message}");
                return false;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[✗] Connection error: {ex.Message}");
                return false;
            }
        }
    }

    /// <summary>
    /// 断开与Redis的连接
    /// </summary>
    public bool Disconnect()
    {
        lock (_lockObj)
        {
            try
            {
                int result = redis_close();
                _connected = false;
                _callbacks.Clear();
                _nativeCallbacks.Clear();
                Console.WriteLine("[✓] Disconnected from Redis");
                return result == 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[✗] Disconnection error: {ex.Message}");
                return false;
            }
        }
    }

    /// <summary>
    /// 发布消息到指定频道
    /// </summary>
    /// <returns>接收消息的订阅者数量，-1表示发送失败</returns>
    public int Publish(string channel, string message)
    {
        if (!_connected)
        {
            Console.WriteLine("[✗] Not connected to Redis");
            return -1;
        }

        try
        {
            lock (_lockObj)
            {
                int result = redis_publish(channel, message);
                Console.WriteLine($"[PUBLISH] Channel: {channel}");
                Console.WriteLine($"          Message: {message}");
                Console.WriteLine($"          Subscribers: {result}");
                return result;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[✗] Publish error: {ex.Message}");
            return -1;
        }
    }

    /// <summary>
    /// 订阅频道
    /// </summary>
    /// <returns>true表示订阅成功</returns>
    public bool Subscribe(string channel, PubSubCallback callback)
    {
        if (!_connected)
        {
            Console.WriteLine("[✗] Not connected to Redis");
            return false;
        }

        if (callback == null)
        {
            Console.WriteLine("[✗] Callback cannot be null");
            return false;
        }

        try
        {
            lock (_lockObj)
            {
                // 创建原生回调函数（使用GCHandle防止被垃圾回收）
                NativePubSubCallback nativeCallback = (channelPtr, messagePtr) =>
                {
                    try
                    {
                        string channelStr = Marshal.PtrToStringAnsi(channelPtr) ?? "";
                        string messageStr = Marshal.PtrToStringAnsi(messagePtr) ?? "";
                        Console.WriteLine($"\n[CALLBACK] Received from '{channelStr}':");
                        Console.WriteLine($"             Message: {messageStr}");
                        callback?.Invoke(channelStr, messageStr);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"[✗] Callback error: {ex.Message}");
                    }
                };

                // 保存回调函数引用
                _callbacks[channel] = callback;
                _nativeCallbacks[channel] = nativeCallback;

                // 调用DLL订阅函数
                int result = redis_subscribe(channel, nativeCallback);

                if (result == 0)
                {
                    Console.WriteLine($"[✓] Subscribed to channel: {channel}");
                    return true;
                }
                else
                {
                    Console.WriteLine($"[✗] Subscribe failed with code {result}");
                    _callbacks.Remove(channel);
                    _nativeCallbacks.Remove(channel);
                    return false;
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[✗] Subscribe error: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// 检查是否已连接
    /// </summary>
    public bool IsConnected => _connected;

    /// <summary>
    /// 获取已订阅的频道列表
    /// </summary>
    public string[] GetSubscribedChannels()
    {
        lock (_lockObj)
        {
            return _callbacks.Keys.ToArray();
        }
    }

    /// <summary>
    /// 等待指定时间
    /// </summary>
    public void Wait(int milliseconds = 1000)
    {
        Thread.Sleep(milliseconds);
    }

    /// <summary>
    /// 异步等待
    /// </summary>
    public async Task WaitAsync(int milliseconds = 1000)
    {
        await Task.Delay(milliseconds);
    }

    /// <summary>
    /// 释放资源
    /// </summary>
    public void Dispose()
    {
        if (_connected)
        {
            Disconnect();
        }
    }
}

// ==================== 测试程序 ====================

class Program
{
    static async Task Main(string[] args)
    {
        Console.WriteLine("========================================");
        Console.WriteLine("  Redis PubSub C# .NET 8 客户端演示");
        Console.WriteLine("========================================\n");

        using (var client = new RedisPubSubClient())
        {
            try
            {
                // 1. 连接到Redis
                Console.WriteLine("[TEST 1] Connecting to Redis...");
                if (!client.Connect("127.0.0.1", 6379))
                {
                    Console.WriteLine("[✗] Failed to connect, exiting...");
                    return;
                }
                Console.WriteLine();

                // 2. 定义回调函数
                void OnMessage1(string channel, string message)
                {
                    Console.WriteLine($"           [Handler 1] Message received: {message}");
                }

                void OnMessage2(string channel, string message)
                {
                    Console.WriteLine($"           [Handler 2] Message received: {message}");
                }

                // 3. 订阅频道
                Console.WriteLine("[TEST 2] Subscribing to channels...");
                client.Subscribe("mychannel", OnMessage1);
                client.Subscribe("events", OnMessage2);
                Console.WriteLine();

                Console.WriteLine($"[INFO] Subscribed channels: {string.Join(", ", client.GetSubscribedChannels())}\n");

                // 等待订阅线程启动
                await client.WaitAsync(1000);

                // 4. 发布测试消息
                Console.WriteLine("[TEST 3] Publishing messages...\n");

                client.Publish("mychannel", "Hello World 1");
                await client.WaitAsync(500);

                client.Publish("mychannel", "Hello World 2");
                await client.WaitAsync(500);

                client.Publish("events", "Event 1");
                await client.WaitAsync(500);

                client.Publish("events", "Event 2");
                await client.WaitAsync(2000);

                Console.WriteLine("\n[✓] Test completed successfully!");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[✗] Error: {ex.Message}");
                Console.WriteLine($"    {ex.StackTrace}");
            }
        }

        Console.WriteLine("\nPress any key to exit...");
        Console.ReadKey();
    }
}
