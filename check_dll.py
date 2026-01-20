#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查DLL依赖"""

import ctypes
import os

dll_path = r"E:\clang\redisEventLib\build\libredis_pubsub.dll"

# 启用错误显示
import sys
import ctypes.util

print(f"DLL path: {dll_path}")
print(f"DLL exists: {os.path.exists(dll_path)}")

# 尝试获取详细的加载错误信息
try:
    # 设置错误模式以获取更详细的错误信息
    import ctypes.wintypes
    
    kernel32 = ctypes.windll.kernel32
    
    # SetErrorMode: 设置错误处理模式
    # 0x0001 - 系统不会显示关键错误的处理程序
    # 返回前一个标志
    old_mode = kernel32.SetErrorMode(0)
    
    try:
        # LoadLibraryEx with LOAD_LIBRARY_SEARCH_DEFAULT_DIRS | LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR
        handle = kernel32.LoadLibraryExW(dll_path, None, 0)
        if handle:
            print("Successfully loaded DLL!")
            kernel32.FreeLibrary(handle)
        else:
            error = kernel32.GetLastError()
            print(f"LoadLibraryEx failed with error: {error}")
            print("Trying to interpret error...")
            
            # 常见错误：
            # 2 - 找不到文件
            # 126 - 找不到指定的模块
            # 127 - 找不到程序入口点
            
            if error == 2:
                print("  -> 找不到DLL文件")
            elif error == 126:
                print("  -> 找不到指定的模块（可能是依赖项）")
            elif error == 127:
                print("  -> 找不到程序入口点")
            else:
                print(f"  -> 未知错误代码: {error}")
    finally:
        kernel32.SetErrorMode(old_mode)
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
