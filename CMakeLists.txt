cmake_minimum_required(VERSION 3.0)
project(redis_pubsub C)

set(CMAKE_C_STANDARD 99)

# 设置hiredis路径
set(HIREDIS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/hiredis")
set(HIREDIS_INCLUDE_DIR "${HIREDIS_DIR}")
set(HIREDIS_LIB_DIR "${HIREDIS_DIR}/build/Release")

# 包含hiredis头文件
include_directories(${HIREDIS_INCLUDE_DIR})

# =============== 生成redis_pubsub DLL ===============
add_library(redis_pubsub SHARED redis_pubsub.c)
target_link_directories(redis_pubsub PRIVATE ${HIREDIS_LIB_DIR})
target_link_libraries(redis_pubsub hiredis ws2_32)

# 设置导出符号
set_target_properties(redis_pubsub PROPERTIES
    WINDOWS_EXPORT_ALL_SYMBOLS ON
)

# 复制依赖DLL
add_custom_command(TARGET redis_pubsub POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
    "${HIREDIS_LIB_DIR}/hiredis.dll"
    "$<TARGET_FILE_DIR:redis_pubsub>/hiredis.dll"
    COMMENT "Copying hiredis DLL..."
)

# =============== 发布者和订阅者程序 ===============
add_executable(publisher publisher.c)
target_link_directories(publisher PRIVATE ${HIREDIS_LIB_DIR})
target_link_libraries(publisher hiredis ws2_32)

add_executable(subscriber subscriber.c)
target_link_directories(subscriber PRIVATE ${HIREDIS_LIB_DIR})
target_link_libraries(subscriber hiredis ws2_32)

add_custom_command(TARGET publisher POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
    "${HIREDIS_LIB_DIR}/hiredis.dll"
    "$<TARGET_FILE_DIR:publisher>/hiredis.dll"
    COMMENT "Copying hiredis DLL..."
)

add_custom_command(TARGET subscriber POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
    "${HIREDIS_LIB_DIR}/hiredis.dll"
    "$<TARGET_FILE_DIR:subscriber>/hiredis.dll"
    COMMENT "Copying hiredis DLL..."
)

message(STATUS "Redis PubSub DLL configured")
message(STATUS "Hiredis lib dir: ${HIREDIS_LIB_DIR}")
