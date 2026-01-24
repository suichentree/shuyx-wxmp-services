@echo off
REM Docker部署脚本 (Windows版本)

REM ==== 使用方法 ==========
REM 直接运行：run.bat（将显示帮助信息）
REM 执行部署：run.bat deploy
REM 查看日志：run.bat logs
REM 查看状态：run.bat status

REM ==== 使用方法 ==========

REM 配置参数（可修改）
set IMAGE_NAME=xdj-newexam-service-fastapi-image
set CONTAINER_NAME=xdj-newexam-service-fastapi-container
set PORT=39666

REM 日志函数
:log_info
    echo [INFO] %~1
    goto :eof

:log_success
    echo [SUCCESS] %~1
    goto :eof

:log_error
    echo [ERROR] %~1
    goto :eof

:log_warning
    echo [WARNING] %~1
    goto :eof

REM 检查Dockerfile
:check_dockerfile
    if not exist "Dockerfile" (
        call :log_error "Dockerfile不存在"
        exit /b 1
    )
    call :log_info "找到Dockerfile"
    goto :eof

REM 检查Docker服务
:check_docker
    docker version >nul 2>&1
    if %errorlevel% neq 0 (
        call :log_error "Docker服务未运行，请先启动Docker"
        exit /b 1
    )
    call :log_info "Docker服务运行正常"
    goto :eof

REM 清理旧资源（旧容器和旧镜像）
:cleanup_old_resources
    call :log_info "开始清理旧资源..."

    REM 停止并删除旧容器
    call :log_info "停止旧容器..."
    docker stop %CONTAINER_NAME% >nul 2>&1
    call :log_info "删除旧容器..."
    docker rm %CONTAINER_NAME% >nul 2>&1

    REM 删除旧镜像
    call :log_info "删除旧镜像..."
    docker rmi %IMAGE_NAME% -f >nul 2>&1

    call :log_success "旧资源清理完成"
    goto :eof

REM 构建镜像
:build_image
    call :check_dockerfile || exit /b 1
    call :check_docker || exit /b 1

    call :log_info "开始构建Docker镜像..."

    REM 构建新镜像
    docker build -t %IMAGE_NAME% .
    if %errorlevel% neq 0 (
        call :log_error "镜像构建失败"
        exit /b 1
    )

    call :log_success "镜像构建成功: %IMAGE_NAME%"
    goto :eof

REM 创建并运行容器
:create_container
    call :check_docker || exit /b 1

    call :log_info "创建并启动容器..."

    REM 创建新容器
    docker run -d --name %CONTAINER_NAME% -p %PORT%:%PORT% --restart unless-stopped %IMAGE_NAME%
    if %errorlevel% neq 0 (
        call :log_error "容器创建失败"
        exit /b 1
    )

    call :log_success "容器创建成功: %CONTAINER_NAME%"
    call :log_info "应用地址: http://localhost:%PORT%"
    goto :eof

REM 重启容器
:restart_container
    call :check_docker || exit /b 1

    call :log_info "重启容器..."

    docker restart %CONTAINER_NAME%
    if %errorlevel% neq 0 (
        call :log_error "容器重启失败"
        exit /b 1
    )

    call :log_success "容器重启成功: %CONTAINER_NAME%"
    goto :eof

REM 停止容器
:stop_container
    call :check_docker || exit /b 1

    call :log_info "停止容器..."

    docker stop %CONTAINER_NAME%
    if %errorlevel% neq 0 (
        call :log_error "容器停止失败"
        exit /b 1
    )

    call :log_success "容器停止成功: %CONTAINER_NAME%"
    goto :eof

REM 删除容器
:remove_container
    call :check_docker || exit /b 1

    REM 先停止容器
    docker stop %CONTAINER_NAME% >nul 2>&1

    call :log_info "删除容器..."

    docker rm %CONTAINER_NAME%
    if %errorlevel% neq 0 (
        call :log_error "容器删除失败"
        exit /b 1
    )

    call :log_success "容器删除成功: %CONTAINER_NAME%"
    goto :eof

REM 查看容器日志
:view_logs
    call :check_docker || exit /b 1

    set "tail=%~1"
    if "%tail%"=="" set "tail=100" REM 默认显示最后100行

    call :log_info "查看容器日志 (最后%tail%行)..."

    docker logs -f %CONTAINER_NAME% --tail %tail%
    if %errorlevel% neq 0 (
        call :log_error "查看日志失败，容器可能未运行"
        exit /b 1
    )

    goto :eof

REM 查看状态
:check_status
    call :check_docker || exit /b 1

    call :log_info "===== 镜像状态 ====="
    docker images %IMAGE_NAME%

    call :log_info "===== 容器状态 ====="
    docker ps -a --filter "name=%CONTAINER_NAME%"

    call :log_info "===== 应用日志 ====="
    docker logs %CONTAINER_NAME% --tail 10 2>nul || echo 容器未运行或没有日志

    goto :eof

REM 完整部署流程
:deploy
    call :log_info "开始完整部署流程..."

    REM 1. 清理旧资源（旧容器和旧镜像）
    call :cleanup_old_resources || exit /b 1

    REM 2. 构建新镜像
    call :build_image || exit /b 1

    REM 3. 创建新容器
    call :create_container || exit /b 1

    call :log_info "等待应用启动..."
    timeout /t 3 /nobreak >nul

    REM 4. 检查状态
    call :check_status

    call :log_success "部署完成！"
    goto :eof

REM 显示帮助
:show_help
    echo Docker部署脚本 (Windows版本)
    echo.
    echo 用法: %~nx0 [操作]
    echo.
    echo 操作:
    echo   deploy    完整部署 (清理旧资源 + 构建镜像 + 创建容器)
    echo   build     仅构建镜像 (会先清理旧镜像)
    echo   run       仅运行容器 (会先清理旧容器)
    echo   restart   重启容器
    echo   stop      停止容器
    echo   remove    删除容器
    echo   status    查看状态
    echo   logs      查看容器日志 (默认100行，可指定: logs 200)
    echo   help      显示帮助 [默认]
    echo.
    goto :eof

REM 主函数
set "ACTION=%~1"
if "%ACTION%"=="" set "ACTION=help"
set "TAIL=%~2"
if "%TAIL%"=="" set "TAIL=100"

if /i "%ACTION%"=="deploy" (
    call :deploy
) else if /i "%ACTION%"=="build" (
    call :cleanup_old_resources || exit /b 1
    call :build_image
) else if /i "%ACTION%"=="run" (
    call :create_container
) else if /i "%ACTION%"=="restart" (
    call :restart_container
) else if /i "%ACTION%"=="stop" (
    call :stop_container
) else if /i "%ACTION%"=="remove" (
    call :remove_container
) else if /i "%ACTION%"=="status" (
    call :check_status
) else if /i "%ACTION%"=="logs" (
    call :view_logs "%TAIL%"
) else if /i "%ACTION%"=="help" (
    call :show_help
) else (
    call :log_error "未知操作: %ACTION%"
    call :show_help
    exit /b 1
)

REM 确保脚本执行完后不会自动关闭窗口
pause

exit /b %errorlevel%