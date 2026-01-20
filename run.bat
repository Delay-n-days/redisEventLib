@echo off
REM Redis PubSub C# .NET 8 客户端 - 快速启动脚本

echo ========================================
echo  Redis PubSub C# .NET 8 客户端
echo ========================================
echo.

REM 检查是否已编译
if not exist "bin\Release\net8.0\RedisPubSubClient.exe" (
    echo [*] 程序未编译，正在编译...
    dotnet build -c Release
    if errorlevel 1 (
        echo [ERROR] 编译失败
        exit /b 1
    )
)

echo [*] 复制DLL文件...
copy /Y "build\Release\redis_pubsub.dll" "bin\Release\net8.0\" >nul
copy /Y "build\Release\hiredis.dll" "bin\Release\net8.0\" >nul

echo [*] 启动程序...
echo.

cd /d "bin\Release\net8.0"
RedisPubSubClient.exe

pause
