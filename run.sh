#!/bin/bash
# Docker部署脚本 (linux环境下可以直接运行)
# 该脚本主要作用就是将代码打包为一个镜像，创建一个Docker容器并运行。

# 部署到本地服务器的方法（本地环境下需要安装Docker）：
# 1. 确保Docker服务已启动
# 2. 运行该脚本（该脚本会根据Dockerfile文件将工程代码文件打包为镜像（带有python环境的），然后上传到当前服务器的Docker仓库。然后创建一个容器并运行。）
# 3. 访问 http://localhost:39666 查看服务是否运行正常

# 部署到远程服务器的方法（远程服务器环境下需要安装Docker）：
# 1. 将本工程的代码上传到远程服务器（若远程服务器无python环境，则无法运行）
# 2. 在远程服务器上运行该脚本（该脚本会根据Dockerfile文件将工程代码文件打包为镜像（带有python环境的），然后上传到当前服务器的Docker仓库。然后创建一个容器并运行。）
# 3. 访问 http://localhost:39666 查看服务是否运行正常


# ==== 脚本使用方法 ==========
# 直接运行：./run.sh           默认会显示脚本的使用方法
# 执行部署：./run.sh deploy    会清理旧容器和旧镜像，然后重新构建镜像并运行容器
# 查看日志：./run.sh logs      会查看容器的日志输出
# 查看状态：./run.sh status    会查看容器的运行状态

# 若脚本不具有执行权限，使用以下命令设置
# chmod +x run.sh

# ============== 配置参数 ==============

# 配置参数（可修改）
IMAGE_NAME="xdj-newexam-service-fastapi-image"
CONTAINER_NAME="xdj-newexam-service-fastapi-container"
PORT=39666

# 日志函数
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}
log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}
log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}
log_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# 检查Dockerfile
check_dockerfile() {
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile不存在"
        return 1
    fi
    log_info "找到Dockerfile"
    return 0
}

# 检查Docker服务
check_docker() {
    if ! docker version > /dev/null 2>&1; then
        log_error "Docker服务未运行，请先启动Docker"
        return 1
    fi
    log_info "Docker服务运行正常"
    return 0
}

# 清理旧资源（旧容器和旧镜像）
cleanup_old_resources() {
    log_info "开始清理旧资源..."

    # 停止并删除旧容器
    log_info "停止旧容器..."
    docker stop "$CONTAINER_NAME" > /dev/null 2>&1
    log_info "删除旧容器..."
    docker rm "$CONTAINER_NAME" > /dev/null 2>&1

    # 删除旧镜像
    log_info "删除旧镜像..."
    docker rmi "$IMAGE_NAME" -f > /dev/null 2>&1

    log_success "旧资源清理完成"
    return 0
}

# 构建镜像
build_image() {
    check_dockerfile || return 1
    check_docker || return 1

    log_info "开始构建Docker镜像..."

    # 构建新镜像
    if docker build -t "$IMAGE_NAME" .; then
        log_success "镜像构建成功: $IMAGE_NAME"
        return 0
    else
        log_error "镜像构建失败"
        return 1
    fi
}

# 创建并运行容器
create_container() {
    check_docker || return 1

    log_info "创建并启动容器..."

    # 创建新容器
    if docker run -d --name "$CONTAINER_NAME" -p "$PORT:$PORT" --restart unless-stopped "$IMAGE_NAME"; then
        log_success "容器创建成功: $CONTAINER_NAME"
        log_info "应用地址: http://localhost:$PORT"
        return 0
    else
        log_error "容器创建失败"
        return 1
    fi
}

# 重启容器
restart_container() {
    check_docker || return 1

    log_info "重启容器..."

    if docker restart "$CONTAINER_NAME"; then
        log_success "容器重启成功: $CONTAINER_NAME"
        return 0
    else
        log_error "容器重启失败"
        return 1
    fi
}

# 停止容器
stop_container() {
    check_docker || return 1

    log_info "停止容器..."

    if docker stop "$CONTAINER_NAME"; then
        log_success "容器停止成功: $CONTAINER_NAME"
        return 0
    else
        log_error "容器停止失败"
        return 1
    fi
}

# 删除容器
remove_container() {
    check_docker || return 1

    # 先停止容器
    docker stop "$CONTAINER_NAME" > /dev/null 2>&1

    log_info "删除容器..."

    if docker rm "$CONTAINER_NAME"; then
        log_success "容器删除成功: $CONTAINER_NAME"
        return 0
    else
        log_error "容器删除失败"
        return 1
    fi
}

# 查看容器日志
view_logs() {
    check_docker || return 1

    local tail="${1:-100}"  # 默认显示最后100行

    log_info "查看容器日志 (最后${tail}行)..."

    if docker logs -f "$CONTAINER_NAME" --tail "$tail"; then
        return 0
    else
        log_error "查看日志失败，容器可能未运行"
        return 1
    fi
}

# 查看状态
check_status() {
    check_docker || return 1

    log_info "===== 镜像状态 ====="
    docker images "$IMAGE_NAME"

    log_info "===== 容器状态 ====="
    docker ps -a --filter "name=$CONTAINER_NAME"

    log_info "===== 应用日志 ====="
    docker logs "$CONTAINER_NAME" --tail 10 2>/dev/null || echo "容器未运行或没有日志"

    return 0
}

# 完整部署流程
deploy() {
    log_info "开始完整部署流程..."

    # 1. 清理旧资源（旧容器和旧镜像）
    cleanup_old_resources || return 1

    # 2. 构建新镜像
    build_image || return 1

    # 3. 创建新容器
    create_container || return 1

    log_info "等待应用启动..."
    sleep 3

    # 4. 检查状态
    check_status

    log_success "部署完成！"
    return 0
}

# 显示帮助
show_help() {
    echo "Docker部署脚本 (无Python依赖)"
    echo
    echo "用法: $0 [操作]"
    echo
    echo "操作:"
    echo "  deploy    完整部署 (清理旧资源 + 构建镜像 + 创建容器) [默认]"
    echo "  build     仅构建镜像 (会先清理旧镜像)"
    echo "  run       仅运行容器 (会先清理旧容器)"
    echo "  restart   重启容器"
    echo "  stop      停止容器"
    echo "  remove    删除容器"
    echo "  status    查看状态"
    echo "  logs      查看容器日志 (默认100行，可指定: logs 200)"
    echo "  help      显示帮助"
    echo
}

# 主函数
main() {
    # 检查是否为root用户
    if [ "$EUID" -ne 0 ] && ! groups | grep -q docker; then
        log_warning "警告: 当前用户不在docker组，可能需要使用sudo"
    fi

    # 解析参数 - 将默认操作改为help
    ACTION="${1:-help}"
    TAIL="${2:-100}"

    case "$ACTION" in
        deploy)
            deploy
            ;;
        build)
            cleanup_old_resources || return 1
            build_image
            ;;
        run)
            create_container
            ;;
        restart)
            restart_container
            ;;
        stop)
            stop_container
            ;;
        remove)
            remove_container
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs "$TAIL"
            ;;
        help)
            show_help
            ;;
        *)
            log_error "未知操作: $ACTION"
            show_help
            return 1
            ;;
    esac

    # 确保脚本执行完后不会自动关闭窗口
    if [ -t 0 ]; then
        # 如果是终端环境，提示按任意键继续
        read -n 1 -s -r -p "按任意键继续..."
        echo
    fi

    return $?
}

# 执行主函数
main "$@"