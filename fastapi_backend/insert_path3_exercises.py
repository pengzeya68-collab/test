#!/usr/bin/env python3
"""
学习路径3：Linux基础命令 - 50道精品题
基于Linux命令的真实课程内容出题
"""

import sqlite3

db_path = 'c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db'

# 学习路径3的50道精品题（基于Linux基础命令课程内容）
exercises_data = [
    # ============ 文件与目录操作（15题）============
    {
        "title": "在Linux中，用于列出目录内容的命令是？",
        "description": "在Linux中，用于列出目录内容的命令是？\n\nA. ls\nB. cd\nC. pwd\nD. mkdir",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "文件与目录操作"
    },
    {
        "title": "关于 `ls -l` 命令的输出，以下说法正确的是？（多选）",
        "description": "关于 `ls -l` 命令的输出，以下说法正确的是？（多选）\n\nA. 第一列表示文件类型和权限\nB. 第三列表示文件所有者\nC. 第五列表示文件大小（字节）\nD. 最后一列表示文件名",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "文件与目录操作"
    },
    {
        "title": "请判断：`cd ..` 命令用于进入当前目录的父目录。",
        "description": "请判断：`cd ..` 命令用于进入当前目录的父目录。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "文件与目录操作"
    },
    {
        "title": "在Linux中，用于创建新目录的命令是？",
        "description": "在Linux中，用于创建新目录的命令是？\n\nA. mkdir\nB. touch\nC. rm\nD. cp",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "文件与目录操作"
    },
    {
        "title": "关于 `cp` 命令，以下说法正确的是？（多选）",
        "description": "关于 `cp` 命令，以下说法正确的是？（多选）\n\nA. cp file1 file2 用于复制文件\nB. cp -r dir1 dir2 用于递归复制目录\nC. cp 只能复制文件，不能复制目录\nD. cp -i 会在覆盖前提示用户",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "文件与目录操作"
    },
    {
        "title": "请判断：`rm -rf /` 命令会递归删除根目录下的所有文件，且不会提示确认。",
        "description": "请判断：`rm -rf /` 命令会递归删除根目录下的所有文件，且不会提示确认。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "文件与目录操作"
    },
    {
        "title": "在Linux中，用于移动文件或重命名文件的命令是？",
        "description": "在Linux中，用于移动文件或重命名文件的命令是？\n\nA. mv\nB. cp\nC. ln\nD. cat",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "文件与目录操作"
    },
    {
        "title": "关于 `touch` 命令，以下说法正确的是？（多选）",
        "description": "关于 `touch` 命令，以下说法正确的是？（多选）\n\nA. 用于创建空文件\nB. 用于修改文件的时间戳\nC. 如果文件已存在，会清空文件内容\nD. 如果文件已存在，不会修改文件内容",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "文件与目录操作"
    },
    {
        "title": "请判断：`pwd` 命令用于显示当前工作目录的完整路径。",
        "description": "请判断：`pwd` 命令用于显示当前工作目录的完整路径。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "文件与目录操作"
    },
    {
        "title": "在Linux中，用于删除空目录的命令是？",
        "description": "在Linux中，用于删除空目录的命令是？\n\nA. rmdir\nB. rm -r\nC. rm\nD. mkdir -p",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "文件与目录操作"
    },
    {
        "title": "关于文件路径，以下说法正确的是？（多选）",
        "description": "关于文件路径，以下说法正确的是？（多选）\n\nA. 绝对路径以 / 开头，如 /home/user/file.txt\nB. 相对路径不以 / 开头，如 docs/file.txt\nC. . 表示当前目录\nD. .. 表示父目录",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "文件与目录操作"
    },
    {
        "title": "请判断：`cat file.txt` 命令会分页显示文件内容。",
        "description": "请判断：`cat file.txt` 命令会分页显示文件内容。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "文件与目录操作"
    },
    {
        "title": "在Linux中，用于分页显示文件内容的命令是？",
        "description": "在Linux中，用于分页显示文件内容的命令是？\n\nA. less\nB. cat\nC. echo\nD. ls",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "文件与目录操作"
    },
    {
        "title": "关于 `head` 和 `tail` 命令，以下说法正确的是？（多选）",
        "description": "关于 `head` 和 `tail` 命令，以下说法正确的是？（多选）\n\nA. head -n 10 file.txt 显示文件前10行\nB. tail -n 10 file.txt 显示文件后10行\nC. tail -f file.txt 会实时追踪文件末尾内容\nD. head 和 tail 默认显示10行",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "文件与目录操作"
    },
    {
        "title": "请判断：`ln -s target linkname` 用于创建符号链接（软链接）。",
        "description": "请判断：`ln -s target linkname` 用于创建符号链接（软链接）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "文件与目录操作"
    },
    {
        "title": "在Linux中，用于查找文件的命令是？",
        "description": "在Linux中，用于查找文件的命令是？\n\nA. find\nB. grep\nC. awk\nD. sed",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "文件与目录操作"
    },
    
    # ============ 文件权限管理（10题）============
    {
        "title": "在Linux中，用于修改文件权限的命令是？",
        "description": "在Linux中，用于修改文件权限的命令是？\n\nA. chmod\nB. chown\nC. chgrp\nD. umask",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "文件权限管理"
    },
    {
        "title": "关于Linux文件权限，以下说法正确的是？（多选）",
        "description": "关于Linux文件权限，以下说法正确的是？（多选）\n\nA. r (读) = 4, w (写) = 2, x (执行) = 1\nB. chmod 755 file.txt 表示所有者有读/写/执行权限，组用户和其他用户有读/执行权限\nC. 第一位表示文件类型，- 表示普通文件，d 表示目录\nD. chmod u+x file.txt 表示给所有者添加执行权限",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "文件权限管理"
    },
    {
        "title": "请判断：`chown user:group file.txt` 命令用于修改文件的所有者和所属组。",
        "description": "请判断：`chown user:group file.txt` 命令用于修改文件的所有者和所属组。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "文件权限管理"
    },
    {
        "title": "在Linux中，用于修改文件所属组的命令是？",
        "description": "在Linux中，用于修改文件所属组的命令是？\n\nA. chgrp\nB. chown\nC. chmod\nD. umask",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "文件权限管理"
    },
    {
        "title": "关于 `umask` 命令，以下说法正确的是？（多选）",
        "description": "关于 `umask` 命令，以下说法正确的是？（多选）\n\nA. umask 用于设置新建文件的默认权限掩码\nB. umask 022 表示新建文件权限为 644，新建目录权限为 755\nC. umask 的值是从 666（文件）或 777（目录）中减去的\nD. umask 0022 在bash中表示八进制数",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "文件权限管理"
    },
    {
        "title": "请判断：在Linux中，root用户不受文件权限的限制。",
        "description": "请判断：在Linux中，root用户不受文件权限的限制。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "文件权限管理"
    },
    {
        "title": "在Linux中，用于查看文件权限和属性的命令是？",
        "description": "在Linux中，用于查看文件权限和属性的命令是？\n\nA. ls -l\nB. pwd\nC. whoami\nD. id",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "文件权限管理"
    },
    {
        "title": "关于特殊权限位（SUID、SGID、Sticky Bit），以下说法正确的是？（多选）",
        "description": "关于特殊权限位（SUID、SGID、Sticky Bit），以下说法正确的是？（多选）\n\nA. SUID（4）表示执行时以文件所有者身份运行\nB. SGID（2）表示执行时以文件所属组身份运行\nC. Sticky Bit（1）用于目录，表示只有文件所有者能删除自己的文件\nD. chmod 4755 file 表示设置SUID位",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "文件权限管理"
    },
    {
        "title": "请判断：`chmod +x script.sh` 会给所有用户（所有者、组、其他）添加执行权限。",
        "description": "请判断：`chmod +x script.sh` 会给所有用户（所有者、组、其他）添加执行权限。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "文件权限管理"
    },
    {
        "title": "在Linux中，`drwxr-x---` 权限表示？",
        "description": "在Linux中，`drwxr-x---` 权限表示？\n\nA. 目录，所有者有读/写/执行权限，组用户有读/执行权限，其他用户无权限\nB. 文件，所有者有读/写/执行权限，组用户有读/执行权限，其他用户无权限\nC. 目录，所有者有读/写权限，组用户有读权限，其他用户无权限\nD. 文件，所有者有读/写权限，组用户有读/执行权限，其他用户有执行权限",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "文件权限管理"
    },
    
    # ============ 进程管理（10题）============
    {
        "title": "在Linux中，用于查看当前运行进程的命令是？",
        "description": "在Linux中，用于查看当前运行进程的命令是？\n\nA. ps\nB. top\nC. kill\nD. jobs",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "进程管理"
    },
    {
        "title": "关于 `ps` 命令，以下说法正确的是？（多选）",
        "description": "关于 `ps` 命令，以下说法正确的是？（多选）\n\nA. ps aux 显示所有用户的进程\nB. ps -ef 以完整格式显示所有进程\nC. ps aux | grep python 用于查找Python进程\nD. ps 命令只能由root用户执行",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "进程管理"
    },
    {
        "title": "请判断：`top` 命令用于实时显示系统中各个进程的资源占用状况。",
        "description": "请判断：`top` 命令用于实时显示系统中各个进程的资源占用状况。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "进程管理"
    },
    {
        "title": "在Linux中，用于终止进程的命令是？",
        "description": "在Linux中，用于终止进程的命令是？\n\nA. kill\nB. ps\nC. top\nD. nice",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "进程管理"
    },
    {
        "title": "关于 `kill` 命令，以下说法正确的是？（多选）",
        "description": "关于 `kill` 命令，以下说法正确的是？（多选）\n\nA. kill PID 默认发送 SIGTERM (15) 信号，允许进程优雅退出\nB. kill -9 PID 发送 SIGKILL 信号，强制终止进程\nC. kill -15 PID 和 kill PID 效果相同\nD. kill 命令只能终止自己的进程",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "进程管理"
    },
    {
        "title": "请判断：`kill -9 PID` 会强制终止进程，且进程无法捕获该信号。",
        "description": "请判断：`kill -9 PID` 会强制终止进程，且进程无法捕获该信号。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "进程管理"
    },
    {
        "title": "在Linux中，用于查看进程树结构的命令是？",
        "description": "在Linux中，用于查看进程树结构的命令是？\n\nA. pstree\nB. ps aux\nC. top\nD. htop",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "进程管理"
    },
    {
        "title": "关于进程优先级（nice值），以下说法正确的是？（多选）",
        "description": "关于进程优先级（nice值），以下说法正确的是？（多选）\n\nA. nice值范围从 -20（最高优先级）到 19（最低优先级）\nB. nice command 以指定的nice值启动进程\nC. renice 用于修改已运行进程的nice值\nD. 只有root用户能提高进程优先级（降低nice值）",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "进程管理"
    },
    {
        "title": "请判断：后台运行进程的方式是在命令末尾加上 `&` 符号。",
        "description": "请判断：后台运行进程的方式是在命令末尾加上 `&` 符号。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "进程管理"
    },
    {
        "title": "在Linux中，用于查看当前用户的作业（jobs）的命令是？",
        "description": "在Linux中，用于查看当前用户的作业（jobs）的命令是？\n\nA. jobs\nB. ps\nC. top\nD. bg",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "进程管理"
    },
    
    # ============ 系统管理（10题）============
    {
        "title": "在Linux中，用于查看系统磁盘使用情况的命令是？",
        "description": "在Linux中，用于查看系统磁盘使用情况的命令是？\n\nA. df -h\nB. du -sh\nC. fdisk -l\nD. mount",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "系统管理"
    },
    {
        "title": "关于 `du` 命令，以下说法正确的是？（多选）",
        "description": "关于 `du` 命令，以下说法正确的是？（多选）\n\nA. du -sh dir/ 显示目录总大小（人类可读格式）\nB. du -h --max-depth=1 dir/ 显示目录下一级子目录的大小\nC. du 命令用于查看磁盘分区使用情况\nD. du 命令只能由root用户执行",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "系统管理"
    },
    {
        "title": "请判断：`free -h` 命令用于以人类可读的格式显示系统内存使用情况。",
        "description": "请判断：`free -h` 命令用于以人类可读的格式显示系统内存使用情况。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "系统管理"
    },
    {
        "title": "在Linux中，用于查看系统启动时间的命令是？",
        "description": "在Linux中，用于查看系统启动时间的命令是？\n\nA. uptime\nB. who\nC. last\nD. dmesg",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "系统管理"
    },
    {
        "title": "关于系统日志，以下说法正确的是？（多选）",
        "description": "关于系统日志，以下说法正确的是？（多选）\n\nA. /var/log/messages 存储通用系统日志\nB. /var/log/syslog 存储系统日志（Ubuntu/Debian）\nC. journalctl 用于查看systemd日志\nD. dmesg 用于查看内核环形缓冲区日志",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "系统管理"
    },
    {
        "title": "请判断：`shutdown -h now` 命令用于立即关闭系统。",
        "description": "请判断：`shutdown -h now` 命令用于立即关闭系统。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "系统管理"
    },
    {
        "title": "在Linux中，用于重启系统的命令是？",
        "description": "在Linux中，用于重启系统的命令是？\n\nA. reboot\nB. shutdown -h now\nC. poweroff\nD. halt",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "系统管理"
    },
    {
        "title": "关于 `sudo` 命令，以下说法正确的是？（多选）",
        "description": "关于 `sudo` 命令，以下说法正确的是？（多选）\n\nA. sudo 允许普通用户以root身份执行命令\nB. /etc/sudoers 文件配置哪些用户可以使用sudo\nC. sudo -i 切换到root用户的交互式shell\nD. sudo 命令需要输入当前用户的密码（默认）",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "系统管理"
    },
    {
        "title": "请判断：`passwd` 命令用于修改用户密码，root用户可以修改任何用户的密码。",
        "description": "请判断：`passwd` 命令用于修改用户密码，root用户可以修改任何用户的密码。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "系统管理"
    },
    {
        "title": "在Linux中，用于查看当前登录用户列表的命令是？",
        "description": "在Linux中，用于查看当前登录用户列表的命令是？\n\nA. who\nB. whoami\nC. id\nD. users",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "系统管理"
    },
    
    # ============ 网络管理（5题）============
    {
        "title": "在Linux中，用于查看网络接口配置的命令是？",
        "description": "在Linux中，用于查看网络接口配置的命令是？\n\nA. ip addr\nB. ping\nC. netstat\nD. ss",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络管理"
    },
    {
        "title": "关于网络调试命令，以下说法正确的是？（多选）",
        "description": "关于网络调试命令，以下说法正确的是？（多选）\n\nA. ping 用于测试网络连通性\nB. netstat -tuln 显示所有监听端口\nC. ss -tuln 是netstat的现代替代品\nD. traceroute 用于追踪数据包路由路径",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "网络管理"
    },
    {
        "title": "请判断：`curl` 和 `wget` 命令都可以用于从网络下载文件。",
        "description": "请判断：`curl` 和 `wget` 命令都可以用于从网络下载文件。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "网络管理"
    },
    {
        "title": "在Linux中，用于测试端口连通性的命令是？",
        "description": "在Linux中，用于测试端口连通性的命令是？\n\nA. telnet 或 nc\nB. ping\nC. traceroute\nD. dig",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "网络管理"
    },
    {
        "title": "关于 `ssh` 命令，以下说法正确的是？（多选）",
        "description": "关于 `ssh` 命令，以下说法正确的是？（多选）\n\nA. ssh user@hostname 用于远程登录到Linux服务器\nB. ssh-keygen 用于生成SSH密钥对\nC. ssh-copy-id 用于将公钥复制到远程服务器\nD. SSH默认使用22端口",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "网络管理"
    },
]

def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 删除学习路径3的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 3")
    print("🗑️  已删除学习路径3（Linux基础命令）的旧习题")
    
    # 插入50道精品题
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex['exercise_type'] == 'code' else "中文"
            
            cursor.execute("""
                INSERT INTO exercises 
                (title, description, solution, exercise_type, difficulty, 
                 learning_path_id, category, is_public, language, 
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 3, ?, 1, ?, datetime('now'), datetime('now'))
            """, (
                ex['title'],
                ex['description'],
                ex['solution'],
                ex['exercise_type'],
                ex['difficulty'],
                ex['category'],
                lang
            ))
            inserted += 1
        except Exception as e:
            print(f"⚠️  插入失败: {e}")
            continue
    
    conn.commit()
    
    # 更新 learning_paths 的 exercise_count
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 3", (inserted,))
    conn.commit()
    
    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径3（Linux基础命令）")
    
    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 3")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径3现在有 {count} 道习题")
    
    conn.close()

if __name__ == "__main__":
    main()
