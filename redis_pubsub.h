#ifndef REDIS_PUBSUB_H
#define REDIS_PUBSUB_H

#ifdef _WIN32
    #define REDIS_PUBSUB_API __declspec(dllexport)
#else
    #define REDIS_PUBSUB_API
#endif

/* 回调函数类型定义 */
typedef void (*PubSubCallback)(const char* channel, const char* message);

/* 初始化连接 */
REDIS_PUBSUB_API int redis_init(const char* hostname, int port);

/* 关闭连接 */
REDIS_PUBSUB_API int redis_close();

/* 发布消息 */
REDIS_PUBSUB_API int redis_publish(const char* channel, const char* message);

/* 订阅频道（异步） */
REDIS_PUBSUB_API int redis_subscribe(const char* channel, PubSubCallback callback);

/* 处理订阅消息（需要在主线程调用） */
REDIS_PUBSUB_API int redis_process_messages(int timeout_ms);

#endif /* REDIS_PUBSUB_H */
