#!/usr/bin/env python3
"""
学习路径5：计算机基础与网络知识 - 50道精品题
基于计算机基础与网络知识的真实课程内容出题
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

# 学习路径5的50道精品题
exercises_data = [
    # ============ 计算机硬件基础（10题）============
    {
        "title": "关于CPU（中央处理器），以下说法正确的是？",
        "description": "关于CPU（中央处理器），以下说法正确的是？\n\nA. CPU由运算器（ALU）和控制器（CU）组成\nB. CPU可以直接访问硬盘上的数据\nC. CPU的主频越高，性能一定越好\nD. CPU不包含寄存器（Register）",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "计算机硬件基础",
    },
    {
        "title": "关于计算机存储层次，以下说法正确的是？（多选）",
        "description": "关于计算机存储层次，以下说法正确的是？（多选）\n\nA. 寄存器 > 缓存（Cache）> 内存 > 外存（硬盘/SSD）\nB. 速度越快，容量越小，单位成本越高\nC. 缓存（Cache）用于缓解CPU和内存之间的速度差异\nD. 虚拟内存是将硬盘空间作为内存使用",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "计算机硬件基础",
    },
    {
        "title": "请判断：RAM（随机存取存储器）是易失性存储，断电后数据丢失。",
        "description": "请判断：RAM（随机存取存储器）是易失性存储，断电后数据丢失。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "计算机硬件基础",
    },
    {
        "title": "关于ROM（只读存储器），以下说法正确的是？",
        "description": "关于ROM（只读存储器），以下说法正确的是？\n\nA. ROM中的 data 在断电后不会丢失\nB. ROM可以随意读写\nC. ROM的访问速度比RAM慢\nD. ROM用于存放大量用户数据",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "计算机硬件基础",
    },
    {
        "title": "关于硬盘和SSD，以下说法正确的是？（多选）",
        "description": "关于硬盘和SSD，以下说法正确的是？（多选）\n\nA. 硬盘（HDD）使用机械磁盘存储数据，SSD使用闪存（Flash）存储数据\nB. SSD的访问速度比硬盘快得多\nC. 硬盘的寿命比SSD长（写入次数限制）\nD. SSD工作时没有噪音，硬盘工作时可能有噪音",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "计算机硬件基础",
    },
    {
        "title": "请判断：GPU（图形处理器）是专门为图形渲染和并行计算设计的处理器。",
        "description": "请判断：GPU（图形处理器）是专门为图形渲染和并行计算设计的处理器。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "计算机硬件基础",
    },
    {
        "title": "关于主板，以下说法正确的是？",
        "description": "关于主板，以下说法正确的是？\n\nA. 主板是连接计算机各硬件组件的电路板\nB. 主板的芯片组（Chipset）不影响系统性能\nC. 主板上的BIOS/UEFI是用于管理硬件固件的程序\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "计算机硬件基础",
    },
    {
        "title": "关于计算机性能指标，以下说法正确的是？（多选）",
        "description": "关于计算机性能指标，以下说法正确的是？（多选）\n\nA. CPU主频（Clock Speed）表示CPU每秒钟执行的周期数\nB. 核心数（Cores）越多，多任务处理能力越强\nC. 内存带宽（Bandwidth）影响数据交换速度\nD. SSD的IOPS（每秒输入输出操作数）远高于硬盘",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "计算机硬件基础",
    },
    {
        "title": "请判断：32位操作系统的寻址空间最大是4GB，64位操作系统没有此限制。",
        "description": "请判断：32位操作系统的寻址空间最大是4GB，64位操作系统没有此限制。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "计算机硬件基础",
    },
    {
        "title": "关于指令集架构（ISA），以下说法正确的是？",
        "description": "关于指令集架构（ISA），以下说法正确的是？\n\nA. x86是复杂指令集（CISC）架构，ARM是精简指令集（RISC）架构\nB. x86架构主要用于移动设备，ARM架构主要用于桌面和服务器\nC. 指令集架构不影响软件的兼容性\nD. 以上说法都不正确",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "计算机硬件基础",
    },
    # ============ 操作系统基础（15题）============
    {
        "title": "关于操作系统（OS），以下说法正确的是？",
        "description": "关于操作系统（OS），以下说法正确的是？\n\nA. 操作系统是管理计算机硬件与软件资源的系统软件\nB. 操作系统不直接管理硬件资源\nC. 操作系统只提供图形用户界面\nD. 操作系统不是必需的，计算机可以没有操作系统",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "操作系统基础",
    },
    {
        "title": "关于进程（Process）和线程（Thread），以下说法正确的是？（多选）",
        "description": "关于进程（Process）和线程（Thread），以下说法正确的是？（多选）\n\nA. 进程是资源分配的基本单位，线程是CPU调度的基本单位\nB. 同一进程内的线程共享内存空间\nC. 不同进程之间的内存空间是隔离的\nD. 线程的开销比进程小",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "操作系统基础",
    },
    {
        "title": "请判断：操作系统的内核（Kernel）运行在用户态（User Mode），应用程序运行在内核态（Kernel Mode）。",
        "description": "请判断：操作系统的内核（Kernel）运行在用户态（User Mode），应用程序运行在内核态（Kernel Mode）。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "操作系统基础",
    },
    {
        "title": "关于进程调度算法，以下说法正确的是？",
        "description": "关于进程调度算法，以下说法正确的是？\n\nA. 时间片轮转（RR）算法为每个进程分配固定的CPU时间片\nB. 优先级调度算法中，优先级高的进程一定先执行（可能饥饿）\nC. 先来先服务（FCFS）算法的公平性最好\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "操作系统基础",
    },
    {
        "title": "关于内存管理，以下说法正确的是？（多选）",
        "description": "关于内存管理，以下说法正确的是？（多选）\n\nA. 虚拟内存（Virtual Memory）使得程序可以使用比物理内存更大的地址空间\nB. 分页（Paging）和分段（Segmentation）是两种内存管理技术\nC. 页面置换算法（如LRU）用于选择换出哪个内存页面\nD. 内存泄漏（Memory Leak）是指程序申请的内存没有释放",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "操作系统基础",
    },
    {
        "title": "请判断：死锁（Deadlock）的四个必要条件是：互斥、占有并等待、不可抢占、循环等待。",
        "description": "请判断：死锁（Deadlock）的四个必要条件是：互斥、占有并等待、不可抢占、循环等待。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "操作系统基础",
    },
    {
        "title": "关于文件系统，以下说法正确的是？",
        "description": "关于文件系统，以下说法正确的是？\n\nA. 文件系统用于组织和管理磁盘上的文件\nB. NTFS（Windows）支持文件权限管理，FAT32不支持\nC. 索引节点（inode）是Unix/Linux文件系统中用于存储文件元数据的数据结构\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "操作系统基础",
    },
    {
        "title": "关于常见的操作系统，以下说法正确的是？（多选）",
        "description": "关于常见的操作系统，以下说法正确的是？（多选）\n\nA. Windows是图形用户界面（GUI）的操作系统\nB. Linux是开源的操作系统，常用于服务器和嵌入式设备\nC. macOS是苹果公司开发的基于Unix的操作系统\nD. Android是基于Linux内核的移动操作系统",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "操作系统基础",
    },
    {
        "title": "请判断：系统调用（System Call）是操作系统提供给应用程序的编程接口（API）。",
        "description": "请判断：系统调用（System Call）是操作系统提供给应用程序的编程接口（API）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "操作系统基础",
    },
    {
        "title": "关于虚拟内存的工作原理，以下说法正确的是？",
        "description": "关于虚拟内存的工作原理，以下说法正确的是？\n\nA. 当物理内存不足时，操作系统将部分内存页面换出到磁盘（交换空间）\nB. 缺页中断（Page Fault）是当程序访问不在内存中的页面时发出的中断\nC. 工作集（Working Set）是指进程在一段时间内频繁访问的页面集合\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "操作系统基础",
    },
    {
        "title": "关于进程间通信（IPC），以下说法正确的是？（多选）",
        "description": "关于进程间通信（IPC），以下说法正确的是？（多选）\n\nA. 管道（Pipe）用于有亲缘关系的进程之间通信\nB. 消息队列（Message Queue）允许进程异步通信\nC. 共享内存（Shared Memory）是最快的IPC方式\nD. 套接字（Socket）可用于不同机器之间的进程通信",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "操作系统基础",
    },
    {
        "title": "请判断：分时操作系统（Time-Sharing OS）允许多个用户同时通过终端使用同一台计算机。",
        "description": "请判断：分时操作系统（Time-Sharing OS）允许多个用户同时通过终端使用同一台计算机。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "操作系统基础",
    },
    {
        "title": "关于实时操作系统（RTOS），以下说法正确的是？",
        "description": "关于实时操作系统（RTOS），以下说法正确的是？\n\nA. 实时操作系统要求在严格的时间限制内完成任务\nB. 实时操作系统的响应时间是可以预测的\nC. 嵌入式系统和工业控制系统常使用实时操作系统\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "操作系统基础",
    },
    {
        "title": "关于Shell（命令行解释器），以下说法正确的是？（多选）",
        "description": "关于Shell（命令行解释器），以下说法正确的是？（多选）\n\nA. Shell是用于解释用户输入的命令并调用相应程序的程序\nB. Bash（Bourne Again Shell）是Linux系统中最常用的Shell\nC. Windows中的CMD和PowerShell都是Shell\nD. Shell脚本可以用于自动化系统管理任务",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "操作系统基础",
    },
    # ============ 网络基础（15题）============
    {
        "title": "关于OSI七层模型，以下说法正确的是？",
        "description": "关于OSI七层模型，以下说法正确的是？\n\nA. 从下到上：物理层、数据链路层、网络层、传输层、会话层、表示层、应用层\nB. 从下到上：物理层、数据链路层、网络层、传输层、会话层、表示层、应用层\nC. OSI模型是互联网的实际标准，所有网络协议都遵循它\nD. 以上说法都不正确",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "关于TCP/IP四层模型，以下说法正确的是？（多选）",
        "description": "关于TCP/IP四层模型，以下说法正确的是？（多选）\n\nA. 网络接口层（Network Interface Layer）对应OSI的物理层和数据链路层\nB. 网际层（Internet Layer）对应OSI的网络层，主要协议是IP\nC. 传输层（Transport Layer）对应OSI的传输层，主要协议是TCP和UDP\nD. 应用层（Application Layer）对应OSI的会话层、表示层和应用层",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "请判断：IP地址是用于标识网络中的设备的逻辑地址。",
        "description": "请判断：IP地址是用于标识网络中的设备的逻辑地址。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "网络基础",
    },
    {
        "title": "关于IPv4地址，以下说法正确的是？",
        "description": "关于IPv4地址，以下说法正确的是？\n\nA. IPv4地址由32位二进制数组成，通常表示为点分十进制\nB. IPv4地址分为A、B、C、D、E五类，其中C类地址用于大型网络\nC. 子网掩码（Subnet Mask）用于区分IP地址中的网络部分和主机部分\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "关于公有IP和私有IP，以下说法正确的是？（多选）",
        "description": "关于公有IP和私有IP，以下说法正确的是？（多选）\n\nA. 私有IP只能在局域网（LAN）内使用，不能直接在互联网上使用\nB. 常见的私有IP地址段：10.0.0.0/8、172.16.0.0/12、192.168.0.0/16\nC. NAT（网络地址转换）技术用于将私有IP转换为公有IP\nD. 公有IP是全球唯一的，私有IP在 different LAN中可以重复",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "请判断：DHCP（动态主机配置协议）用于自动为网络中的设备分配IP地址、子网掩码、默认网关等网络配置。",
        "description": "请判断：DHCP（动态主机配置协议）用于自动为网络中的设备分配IP地址、子网掩码、默认网关等网络配置。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "关于DNS（域名系统），以下说法正确的是？",
        "description": "关于DNS（域名系统），以下说法正确的是？\n\nA. DNS用于将域名解析为IP地址\nB. DNS使用TCP协议，端口号是53\nC. DNS服务器是层级结构的\nD. 以上说法都不正确",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "关于TCP和UDP的区别，以下说法正确的是？（多选）",
        "description": "关于TCP和UDP的区别，以下说法正确的是？（多选）\n\nA. TCP是面向连接的、可靠的、有序的、重量级的协议\nB. UDP是无连接的、不可靠的、无序的、轻量级的协议\nC. TCP适用于文件传输、邮件传输等可靠传输场景\nD. UDP适用于视频流、在线游戏等对实时性要求高的场景",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "请判断：TCP的三次握手（Three-Way Handshake）过程是：SYN → SYN-ACK → ACK。",
        "description": "请判断：TCP的三次握手（Three-Way Handshake）过程是：SYN → SYN-ACK → ACK。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "网络基础",
    },
    {
        "title": "关于HTTP和HTTPS，以下说法正确的是？",
        "description": "关于HTTP和HTTPS，以下说法正确的是？\n\nA. HTTPS是HTTP的安全版本，使用TLS/SSL加密通信内容\nB. HTTP默认使用80端口，HTTPS默认使用443端口\nC. HTTPS可以防止中间人攻击（MITM）\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "关于常见的网络命令，以下说法正确的是？（多选）",
        "description": "关于常见的网络命令，以下说法正确的是？（多选）\n\nA. ping命令用于测试网络连通性\nB. ipconfig/ifconfig命令用于查看和配置网络接口\nC. tracert命令用于追踪数据包从源到目的地的路径\nD. netstat命令用于查看网络连接状态和统计信息",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "请判断：MAC地址是网络接口控制器（NIC）的物理地址，长度为48位，在全球范围内唯一。",
        "description": "请判断：MAC地址是网络接口控制器（NIC）的物理地址，长度为48位，在全球范围内唯一。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "关于网络拓扑结构，以下说法正确的是？",
        "description": "关于网络拓扑结构，以下说法正确的是？\n\nA. 星型拓扑：所有设备连接到中央设备（如交换机），中央设备故障时整个网络瘫痪\nB. 环型拓扑：所有设备形成闭合环路，一台设备故障时可能影响整个网络\nC. 总线型拓扑：所有设备共享一条通信线路，存在信号冲突问题\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络基础",
    },
    {
        "title": "关于网络设备，以下说法正确的是？（多选）",
        "description": "关于网络设备，以下说法正确的是？（多选）\n\nA. 集线器（Hub）是物理层设备，会将收到的数据广播给所有端口\nB. 交换机（Switch）是数据链路层设备，根据MAC地址表转发数据帧\nC. 路由器（Router）是网络层设备，根据IP地址路由数据包\nD. 防火墙（Firewall）用于保护网络安全，可以过滤进出网络的流量",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "网络基础",
    },
    # ============ 网络安全基础（10题）============
    {
        "title": "关于网络安全的基本概念，以下说法正确的是？",
        "description": "关于网络安全的基本概念，以下说法正确的是？\n\nA. 机密性（Confidentiality）：确保信息不被未授权的用户访问\nB. 完整性（Integrity）：确保信息在传输和存储过程中不被篡改\nC. 可用性（Availability）：确保授权用户可以及时访问信息和服务\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络安全基础",
    },
    {
        "title": "关于常见的网络攻击，以下说法正确的是？（多选）",
        "description": "关于常见的网络攻击，以下说法正确的是？（多选）\n\nA. DDoS（分布式拒绝服务）攻击通过大量恶意流量使目标系统无法正常服务\nB. SQL注入攻击通过在Web表单中输入恶意SQL代码来攻击数据库\nC. XSS（跨站脚本）攻击通过在网页中注入恶意脚本来攻击用户\nD. 钓鱼（Phishing）攻击通过伪造可信网站来骗取用户的敏感信息",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "网络安全基础",
    },
    {
        "title": "请判断：对称加密使用同一把密钥进行加密和解密，非对称加密使用公钥加密、私钥解密（或相反）。",
        "description": "请判断：对称加密使用同一把密钥进行加密和解密，非对称加密使用公钥加密、私钥解密（或相反）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "网络安全基础",
    },
    {
        "title": "关于防火墙，以下说法正确的是？",
        "description": "关于防火墙，以下说法正确的是？\n\nA. 防火墙用于隔离可信网络和不可信网络\nB. 包过滤防火墙工作在网络层，根据IP地址和端口号过滤流量\nC. 应用层防火墙可以检查应用层协议的内容\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络安全基础",
    },
    {
        "title": "关于VPN（虚拟专用网络），以下说法正确的是？（多选）",
        "description": "关于VPN（虚拟专用网络），以下说法正确的是？（多选）\n\nA. VPN用于在公共网络上建立加密的专用网络连接\nB. VPN可以保护数据在传输过程中的安全性\nC. 常见的VPN协议：PPTP、L2TP、IPSec、SSL VPN\nD. VPN可以用于远程访问公司内部网络资源",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "网络安全基础",
    },
    {
        "title": "请判断：数字证书（Digital Certificate）用于证明公钥的所有权，由可信的证书颁发机构（CA）签发。",
        "description": "请判断：数字证书（Digital Certificate）用于证明公钥的所有权，由可信的证书颁发机构（CA）签发。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "网络安全基础",
    },
    {
        "title": "关于常见的认证方式，以下说法正确的是？",
        "description": "关于常见的认证方式，以下说法正确的是？\n\nA. 单因素认证：只使用一种认证因素（如密码）\nB. 双因素认证（2FA）：使用两种认证因素（如密码+手机验证码）\nC. 多因素认证（MFA）：使用多种认证因素（如密码+指纹+USB密钥）\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络安全基础",
    },
    {
        "title": "关于密码安全，以下说法正确的是？（多选）",
        "description": "关于密码安全，以下说法正确的是？（多选）\n\nA. 强密码应该包含大小写字母、数字和特殊字符\nB. 密码应该定期更换\nC. 不要在多个网站使用相同的密码\nD. 可以使用密码管理器（Password Manager）来生成和存储强密码",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "category": "网络安全基础",
    },
    {
        "title": "请判断：哈希（Hash）函数是单向函数，可以将任意长度的数据映射为固定长度的哈希值，且无法通过哈希值反推出原始数据。",
        "description": "请判断：哈希（Hash）函数是单向函数，可以将任意长度的数据映射为固定长度的哈希值，且无法通过哈希值反推出原始数据。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "网络安全基础",
    },
    {
        "title": "关于常见的网络协议端口号，以下说法正确的是？",
        "description": "关于常见的网络协议端口号，以下说法正确的是？\n\nA. HTTP使用80端口，HTTPS使用443端口\nB. FTP使用20和21端口，SSH使用22端口\nC. Telnet使用23端口（明文传输，不安全）\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "网络安全基础",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除学习路径5的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 5")
    print("🗑️  已删除学习路径5（计算机基础与网络知识）的旧习题")

    # 插入50道精品题
    inserted = 0
    for ex in exercises_data:
        try:
            lang = "python" if ex["exercise_type"] == "code" else "中文"

            cursor.execute(
                """
                INSERT INTO exercises 
                (title, description, solution, exercise_type, difficulty, 
                 learning_path_id, category, is_public, language, 
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 5, ?, 1, ?, datetime('now'), datetime('now'))
            """,
                (
                    ex["title"],
                    ex["description"],
                    ex["solution"],
                    ex["exercise_type"],
                    ex["difficulty"],
                    ex["category"],
                    lang,
                ),
            )
            inserted += 1
        except Exception as e:
            print(f"⚠️  插入失败: {e}")
            continue

    conn.commit()

    # 更新 learning_paths 的 exercise_count
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 5", (inserted,))
    conn.commit()

    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径5（计算机基础与网络知识）")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 5")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径5现在有 {count} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
