#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hiredis/hiredis.h"

int main(int argc, char *argv[]) {
    redisContext *c;
    redisReply *reply;
    const char *hostname = "127.0.0.1";
    int port = 6379;
    int msg_count = 0;
    
    printf("========== Redis Subscriber Demo ==========\n");
    printf("Connecting to Redis at %s:%d...\n", hostname, port);
    
    // 连接到Redis
    c = redisConnect(hostname, port);
    if (c == NULL || c->err) {
        if (c) {
            printf("ERROR: %s\n", c->errstr);
            redisFree(c);
        } else {
            printf("ERROR: Can't allocate redis context\n");
        }
        return 1;
    }
    
    printf("Connected successfully!\n\n");
    
    // 订阅频道
    printf("Subscribing to channel 'mychannel'...\n");
    printf("Waiting for messages (Ctrl+C to exit)...\n\n");
    
    // 执行SUBSCRIBE命令
    if (redisCommand(c, "SUBSCRIBE mychannel") == NULL) {
        printf("ERROR: Failed to subscribe\n");
        redisFree(c);
        return 1;
    }
    
    // 循环接收消息
    while (redisGetReply(c, (void**)&reply) == REDIS_OK) {
        if (reply == NULL) {
            printf("ERROR: Connection lost\n");
            break;
        }
        
        // 检查是否是消息回复
        if (reply->type == REDIS_REPLY_ARRAY && reply->elements == 3) {
            // reply->element[0] 是类型 ("message")
            // reply->element[1] 是频道名
            // reply->element[2] 是消息内容
            if (strcmp(reply->element[0]->str, "message") == 0) {
                msg_count++;
                printf("[Message #%d] From channel '%s':\n", msg_count, reply->element[1]->str);
                printf("             %s\n\n", reply->element[2]->str);
            }
        } 
        // 检查订阅确认
        else if (reply->type == REDIS_REPLY_ARRAY && reply->elements == 3) {
            if (strcmp(reply->element[0]->str, "subscribe") == 0) {
                printf("[Info] Subscribed to '%s' (total subscriptions: %lld)\n\n", 
                       reply->element[1]->str, reply->element[2]->integer);
            }
        }
        
        freeReplyObject(reply);
    }
    
    printf("\n✓ Subscription ended\n");
    
    redisFree(c);
    return 0;
}
