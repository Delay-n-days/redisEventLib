#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "hiredis/hiredis.h"

int main(int argc, char *argv[]) {
    redisContext *c;
    redisReply *reply;
    const char *hostname = "127.0.0.1";
    int port = 6379;
    
    printf("========== Redis Publisher Demo ==========\n");
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
    
    // 发布消息
    printf("Publishing messages...\n");
    
    for (int i = 0; i < 5; i++) {
        char message[256];
        snprintf(message, sizeof(message), "Hello from publisher - Message %d", i + 1);
        
        // PUBLISH channel message
        reply = redisCommand(c, "PUBLISH mychannel %s", message);
        
        if (reply != NULL) {
            printf("[Published] Channel: mychannel | Message: %s\n", message);
            printf("            Subscribers received: %lld\n", reply->integer);
            freeReplyObject(reply);
        }
        
        sleep(2);  // 每2秒发送一条
    }
    
    printf("\n✓ All messages published!\n");
    
    redisFree(c);
    return 0;
}
