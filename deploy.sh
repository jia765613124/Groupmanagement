#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查必要的文件
check_files() {
    local required_files=(
        "compose.yml"
        "compose.override.yml"
        "compose.prod.yml"
        ".env"
        ".env.development"
        "Dockerfile"
        ".python-version"
        "alembic.ini"
        "pyproject.toml"
        "uv.lock"
    )
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "缺少必要文件: $file"
            exit 1
        fi
    done
}

# 打包项目
package_project() {
    print_message "开始打包项目..."
    
    # 创建临时目录
    local temp_dir="deploy_temp"
    mkdir -p "$temp_dir"
    
    # 复制配置文件
    print_message "复制配置文件..."
    cp compose.yml "$temp_dir/"
    cp compose.override.yml "$temp_dir/"
    cp compose.prod.yml "$temp_dir/"
    cp .env.development "$temp_dir/"
    cp Dockerfile "$temp_dir/"
    cp .python-version "$temp_dir/"
    cp alembic.ini "$temp_dir/"
    cp pyproject.toml "$temp_dir/"
    cp uv.lock "$temp_dir/"
    
    # 复制必要目录
    print_message "复制 api 目录..."
    cp -r api "$temp_dir/"
    
    print_message "复制 bot 目录..."
    cp -r bot "$temp_dir/"
    
    print_message "复制 migrations 目录..."
    cp -r migrations "$temp_dir/"
    
    # 检查sessions目录是否存在，如果存在则复制
    if [ -d "sessions" ]; then
        print_message "复制 sessions 目录..."
        cp -r sessions "$temp_dir/"
    else
        print_warning "sessions 目录不存在，跳过复制"
    fi
    
    # 创建部署脚本
    cat > "$temp_dir/deploy.sh" << 'EOF'
#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}[INFO]${NC} 开始部署..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查宿主机的 MySQL 和 Redis 是否运行
if ! systemctl is-active --quiet mysql; then
    echo -e "${RED}[ERROR]${NC} MySQL 服务未运行，请先启动 MySQL"
    exit 1
fi

if ! systemctl is-active --quiet redis; then
    echo -e "${RED}[ERROR]${NC} Redis 服务未运行，请先启动 Redis"
    exit 1
fi

# 停止并删除旧容器
docker-compose down

# 启动新容器
docker-compose up -d

# 检查容器是否成功启动
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[INFO]${NC} 部署完成！"
    echo -e "${GREEN}[INFO]${NC} 服务运行在端口 6600"
else
    echo -e "${RED}[ERROR]${NC} 部署失败，请检查日志"
    exit 1
fi
EOF
    
    chmod +x "$temp_dir/deploy.sh"
    
    # 进入临时目录，将内容移动到当前目录
    cd "$temp_dir"
    
    # 创建压缩包（从临时目录内部打包，这样解压后直接是文件，没有外层目录）
    tar -czf ../GroupManagement.tar.gz ./*
    
    # 返回原目录
    cd ..
    
    # 清理临时目录
    rm -rf "$temp_dir"
    
    print_message "打包完成！文件: GroupManagement.tar.gz"
    print_message "使用方法："
    print_message "1. 解压文件：tar -xzf GroupManagement.tar.gz"
    print_message "2. 执行部署：./deploy.sh"
}

# 主函数
main() {
    check_files
    package_project
}

# 执行主函数
main "$@"

chmod +x deploy.sh 