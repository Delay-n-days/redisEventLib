#include "redis_pubsub.h"
#include "hiredis/hiredis.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <process.h>

/* 全局变量 */
static redisContext *g_context = NULL;
static redisContext *g_sub_context = NULL;
static HANDLE g_thread = NULL;
static int g_running = 0;
static PubSubCallback g_callbacks[100];  /* 最多支持100个频道 */
static char g_channels[100][256];
static int g_callback_count = 0;
static CRITICAL_SECTION g_lock;

/* 前向声明 */
static unsigned int __stdcall subscription_thread(void *arg);

/* ==================== 初始化和关闭 ==================== */

REDIS_PUBSUB_API int redis_init(const char* hostname, int port) {
    InitializeCriticalSection(&g_lock);
    
    /* 创建发布连接 */
    g_context = redisConnect(hostname, port);
    if (g_context == NULL || g_context->err) {
        fprintf(stderr, "[ERROR] Failed to connect to Redis (publish): %s\n", 
                g_context ? g_context->errstr : "malloc failure");
        if (g_context) redisFree(g_context);
        return -1;
    }
    
    /* 创建订阅连接 */
    g_sub_context = redisConnect(hostname, port);
    if (g_sub_context == NULL || g_sub_context->err) {
        fprintf(stderr, "[ERROR] Failed to connect to Redis (subscribe): %s\n",
                g_sub_context ? g_sub_context->errstr : "malloc failure");
        if (g_sub_context) redisFree(g_sub_context);
        redisFree(g_context);
        return -1;
    }
    
    g_running = 1;
    g_callback_count = 0;
    
    // fprintf(stdout, "[INFO] Redis connected: %s:%d\n", hostname, port);
    return 0;
}

REDIS_PUBSUB_API int redis_close() {
    EnterCriticalSection(&g_lock);
    
    g_running = 0;
    
    if (g_sub_context) {
        redisFree(g_sub_context);
        g_sub_context = NULL;
    }
    
    if (g_context) {
        redisFree(g_context);
        g_context = NULL;
    }
    
    g_callback_count = 0;
    
    LeaveCriticalSection(&g_lock);
    DeleteCriticalSection(&g_lock);
    
    // fprintf(stdout, "[INFO] Redis disconnected\n");
    return 0;
}

/* ==================== 发布消息 ==================== */

REDIS_PUBSUB_API int redis_publish(const char* channel, const char* message) {
    if (!g_context) {
        fprintf(stderr, "[ERROR] Redis not initialized\n");
        return -1;
    }
    
    if (!channel || !message) {
        fprintf(stderr, "[ERROR] Invalid channel or message\n");
        return -1;
    }
    
    EnterCriticalSection(&g_lock);
    
    redisReply *reply = redisCommand(g_context, "PUBLISH %s %s", channel, message);
    
    if (!reply) {
        fprintf(stderr, "[ERROR] Failed to publish: %s\n", g_context->errstr);
        LeaveCriticalSection(&g_lock);
        return -1;
    }
    
    long long subscribers = reply->integer;
    freeReplyObject(reply);
    
    // fprintf(stdout, "[PUBLISH] Channel: %s | Message: %s | Subscribers: %lld\n", 
            // channel, message, subscribers);
    
    LeaveCriticalSection(&g_lock);
    return (int)subscribers;
}

/* ==================== 订阅消息 ==================== */

REDIS_PUBSUB_API int redis_subscribe(const char* channel, PubSubCallback callback) {
    if (!g_context || !g_sub_context) {
        fprintf(stderr, "[ERROR] Redis not initialized\n");
        return -1;
    }
    
    if (!channel || !callback) {
        fprintf(stderr, "[ERROR] Invalid channel or callback\n");
        return -1;
    }
    
    EnterCriticalSection(&g_lock);
    
    if (g_callback_count >= 100) {
        fprintf(stderr, "[ERROR] Max channels (100) exceeded\n");
        LeaveCriticalSection(&g_lock);
        return -1;
    }
    
    /* 保存回调函数 */
    strcpy_s(g_channels[g_callback_count], sizeof(g_channels[g_callback_count]), channel);
    g_callbacks[g_callback_count] = callback;
    g_callback_count++;
    
    /* 执行SUBSCRIBE命令 */
    if (redisCommand(g_sub_context, "SUBSCRIBE %s", channel) == NULL) {
        fprintf(stderr, "[ERROR] Failed to subscribe: %s\n", g_sub_context->errstr);
        g_callback_count--;
        LeaveCriticalSection(&g_lock);
        return -1;
    }
    
    // fprintf(stdout, "[SUBSCRIBE] Subscribed to channel: %s\n", channel);
    
    /* 如果是第一个订阅，启动处理线程 */
    if (g_callback_count == 1) {
        g_thread = (HANDLE)_beginthreadex(NULL, 0, subscription_thread, NULL, 0, NULL);
        if (!g_thread) {
            fprintf(stderr, "[ERROR] Failed to create subscription thread\n");
            g_callback_count--;
            LeaveCriticalSection(&g_lock);
            return -1;
        }
    }
    
    LeaveCriticalSection(&g_lock);
    return 0;
}

/* ==================== 订阅处理线程 ==================== */

static unsigned int __stdcall subscription_thread(void *arg) {
    // fprintf(stdout, "[INFO] Subscription thread started\n");
    
    while (g_running && g_sub_context) {
        redisReply *reply = NULL;
        
        if (redisGetReply(g_sub_context, (void**)&reply) != REDIS_OK) {
            if (g_running) {
                fprintf(stderr, "[ERROR] Connection lost in subscription thread\n");
            }
            break;
        }
        
        if (!reply) {
            continue;
        }
        
        /* 处理消息回复 */
        if (reply->type == REDIS_REPLY_ARRAY && reply->elements == 3) {
            if (strcmp(reply->element[0]->str, "message") == 0) {
                const char *channel = reply->element[1]->str;
                const char *message = reply->element[2]->str;
                
                // fprintf(stdout, "[MESSAGE] Channel: %s | Message: %s\n", channel, message);
                
                /* 查找并调用对应的回调函数 */
                EnterCriticalSection(&g_lock);
                for (int i = 0; i < g_callback_count; i++) {
                    if (strcmp(g_channels[i], channel) == 0 && g_callbacks[i]) {
                        g_callbacks[i](channel, message);
                        break;
                    }
                }
                LeaveCriticalSection(&g_lock);
            }
        }
        
        freeReplyObject(reply);
    }
    
    // fprintf(stdout, "[INFO] Subscription thread ended\n");
    return 0;
}

/* ==================== 处理消息（可选） ==================== */

REDIS_PUBSUB_API int redis_process_messages(int timeout_ms) {
    if (!g_sub_context) {
        fprintf(stderr, "[ERROR] Redis not initialized\n");
        return -1;
    }
    
    /* 这个函数可以用于非阻塞式处理 */
    /* 当前实现使用独立线程处理 */
    Sleep(timeout_ms);
    return 0;
}
