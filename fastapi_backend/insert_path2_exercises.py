#!/usr/bin/env python3
"""
学习路径2：SQL数据库基础 - 50道精品题
基于真实的SQL课程内容出题
"""

import sqlite3

db_path = 'c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db'

# 学习路径2的50道精品题（基于SQL数据库基础课程内容）
exercises_data = [
    # ============ SQL基础概念（10题）============
    {
        "title": "SQL（Structured Query Language）的主要作用是？",
        "description": "SQL（Structured Query Language）的主要作用是？\n\nA. 与关系型数据库进行交互的标准语言\nB. 编写操作系统\nC. 开发前端页面\nD. 设计网络协议",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "SQL基础概念"
    },
    {
        "title": "以下哪些是SQL的主要分类？（多选）",
        "description": "以下哪些是SQL的主要分类？（多选）\n\nA. DDL（数据定义语言）：CREATE、ALTER、DROP\nB. DML（数据操作语言）：SELECT、INSERT、UPDATE、DELETE\nC. DCL（数据控制语言）：GRANT、REVOKE\nD. DQL（数据查询语言）：SELECT",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "SQL基础概念"
    },
    {
        "title": '请判断：SQL是一种过程式语言，需要指定\u201c怎么做\u201d，而不仅仅是\u201c做什么\u201d。',
        "description": '请判断：SQL是一种过程式语言，需要指定\u201c怎么做\u201d，而不仅仅是\u201c做什么\u201d。\n\nA. 正确\nB. 错误',
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "SQL基础概念"
    },
    {
        "title": "关于关系型数据库，以下说法正确的是？",
        "description": "关于关系型数据库，以下说法正确的是？\n\nA. 数据以表格（Table）的形式组织，每个表由行和列组成\nB. 数据以树形结构组织\nC. 数据以键值对形式组织\nD. 数据以图结构组织",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "SQL基础概念"
    },
    {
        "title": "SQL语句中，用于查询数据的关键字是？",
        "description": "SQL语句中，用于查询数据的关键字是？\n\nA. SELECT\nB. INSERT\nC. UPDATE\nD. DELETE",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "SQL基础概念"
    },
    {
        "title": "关于DDL（数据定义语言），以下说法正确的是？（多选）",
        "description": "关于DDL（数据定义语言），以下说法正确的是？（多选）\n\nA. 用于定义和修改数据库结构\nB. 主要命令包括CREATE、ALTER、DROP\nC. 用于插入、更新、删除数据\nD. 用于查询数据",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "SQL基础概念"
    },
    {
        "title": '请判断：在关系型数据库中，表（Table）中的一行称为\u201c字段\u201d，一列称为\u201c记录\u201d。',
        "description": '请判断：在关系型数据库中，表（Table）中的一行称为\u201c字段\u201d，一列称为\u201c记录\u201d。\n\nA. 正确\nB. 错误',
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "SQL基础概念"
    },
    {
        "title": "关于主键（Primary Key），以下说法错误的是？",
        "description": "关于主键（Primary Key），以下说法错误的是？\n\nA. 主键可以重复\nB. 主键唯一标识表中的每一行\nC. 主键不能为NULL\nD. 一个表只能有一个主键",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "SQL基础概念"
    },
    {
        "title": "关于外键（Foreign Key），以下说法正确的是？（多选）",
        "description": "关于外键（Foreign Key），以下说法正确的是？（多选）\n\nA. 用于建立和维护两个表之间的关系\nB. 外键的值必须存在于主表的主键中\nC. 外键可以为NULL\nD. 一个表只能有一个外键",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "SQL基础概念"
    },
    {
        "title": "请判断：SQL语句不区分大小写，但字符串值区分大小写。",
        "description": "请判断：SQL语句不区分大小写，但字符串值区分大小写。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "SQL基础概念"
    },
    
    # ============ SELECT查询基础（15题）============
    {
        "title": "以下SQL查询语句正确的是？",
        "description": "以下SQL查询语句正确的是？\n\nA. SELECT * FROM users;\nB. SELECT FROM users;\nC. QUERY * FROM users;\nD. GET * FROM users;",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "SELECT查询基础"
    },
    {
        "title": "关于SELECT语句中的WHERE子句，以下说法正确的是？（多选）",
        "description": "关于SELECT语句中的WHERE子句，以下说法正确的是？（多选）\n\nA. 用于过滤记录，只返回满足条件的行\nB. 可以使用比较运算符（=, <, >, <>, <=, >=）\nC. 可以使用逻辑运算符（AND, OR, NOT）\nD. WHERE子句必须放在SELECT之后，ORDER BY之前",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "SELECT查询基础"
    },
    {
        "title": "请判断：SELECT * 会查询表中的所有列，但在生产环境中不推荐使用，因为性能较差。",
        "description": "请判断：SELECT * 会查询表中的所有列，但在生产环境中不推荐使用，因为性能较差。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "SELECT查询基础"
    },
    {
        "title": "以下查询语句中，用于排序的子句是？",
        "description": "以下查询语句中，用于排序的子句是？\n\nA. ORDER BY\nB. GROUP BY\nC. WHERE\nD. HAVING",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "SELECT查询基础"
    },
    {
        "title": "关于ORDER BY子句，以下说法正确的是？",
        "description": "关于ORDER BY子句，以下说法正确的是？\n\nA. ASC表示升序（默认），DESC表示降序\nB. ORDER BY只能按一个列排序\nC. ORDER BY必须放在WHERE子句之前\nD. ORDER BY只能用于数字列",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "SELECT查询基础"
    },
    {
        "title": "关于LIMIT子句，以下说法正确的是？（多选）",
        "description": "关于LIMIT子句，以下说法正确的是？（多选）\n\nA. 用于限制返回的记录数量\nB. LIMIT 10, 5 表示跳过前10条，返回接下来的5条\nC. MySQL中使用LIMIT，Oracle中使用ROWNUM\nD. LIMIT必须放在SQL语句的最后",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "SELECT查询基础"
    },
    {
        "title": "请判断：WHERE子句可以使用聚合函数（如COUNT、SUM、AVG等）作为条件。",
        "description": "请判断：WHERE子句可以使用聚合函数（如COUNT、SUM、AVG等）作为条件。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "SELECT查询基础"
    },
    {
        "title": "以下用于模糊查询的通配符，正确的是？",
        "description": "以下用于模糊查询的通配符，正确的是？\n\nA. % 表示任意长度的字符串，_ 表示单个字符\nB. * 表示任意长度的字符串，? 表示单个字符\nC. # 表示任意长度的字符串，@ 表示单个字符\nD. $ 表示任意长度的字符串，& 表示单个字符",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "SELECT查询基础"
    },
    {
        "title": "关于LIKE操作符，以下说法正确的是？（多选）",
        "description": "关于LIKE操作符，以下说法正确的是？（多选）\n\nA. LIKE 'a%' 匹配以'a'开头的字符串\nB. LIKE '%a' 匹配以'a'结尾的字符串\nC. LIKE '%a%' 匹配包含'a'的字符串\nD. LIKE '_a%' 匹配第二个字符是'a'的字符串",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "SELECT查询基础"
    },
    {
        "title": "请判断：在SQL中，NULL表示空字符串（''）。",
        "description": "请判断：在SQL中，NULL表示空字符串（''）。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "SELECT查询基础"
    },
    {
        "title": "以下用于判断NULL值的条件是？",
        "description": "以下用于判断NULL值的条件是？\n\nA. WHERE column IS NULL\nB. WHERE column = NULL\nC. WHERE column == NULL\nD. WHERE column EQUALS NULL",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "SELECT查询基础"
    },
    {
        "title": "关于BETWEEN操作符，以下说法正确的是？（多选）",
        "description": "关于BETWEEN操作符，以下说法正确的是？（多选）\n\nA. BETWEEN a AND b 包含边界值a和b\nB. BETWEEN适用于数字、文本、日期等类型\nC. BETWEEN等价于 >= a AND <= b\nD. BETWEEN只能用于数字类型",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "SELECT查询基础"
    },
    {
        "title": "请判断：IN操作符用于匹配多个值，等价于多个OR条件。",
        "description": "请判断：IN操作符用于匹配多个值，等价于多个OR条件。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "SELECT查询基础"
    },
    {
        "title": "以下SQL语句中，用于去除重复记录的关键字是？",
        "description": "以下SQL语句中，用于去除重复记录的关键字是？\n\nA. DISTINCT\nB. UNIQUE\nC. REMOVE\nD. DELETE",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "SELECT查询基础"
    },
    {
        "title": "关于别名（Alias），以下说法正确的是？",
        "description": "关于别名（Alias），以下说法正确的是？\n\nA. 可以使用AS关键字给表或列起别名，AS可以省略\nB. 别名必须使用AS关键字，不能省略\nC. 别名只能在SELECT子句中使用\nD. 别名不能用于计算字段",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "SELECT查询基础"
    },
    
    # ============ 聚合函数与分组（10题）============
    {
        "title": "以下哪些是SQL的聚合函数？（多选）",
        "description": "以下哪些是SQL的聚合函数？（多选）\n\nA. COUNT()：统计行数\nB. SUM()：计算总和\nC. AVG()：计算平均值\nD. MAX()/MIN()：返回最大/最小值",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "聚合函数与分组"
    },
    {
        "title": "请判断：COUNT(*) 和 COUNT(column) 的结果是一样的。",
        "description": "请判断：COUNT(*) 和 COUNT(column) 的结果是一样的。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "聚合函数与分组"
    },
    {
        "title": "关于GROUP BY子句，以下说法正确的是？",
        "description": "关于GROUP BY子句，以下说法正确的是？\n\nA. 用于按一个或多个列对结果集进行分组，常与聚合函数一起使用\nB. 用于过滤单个记录\nC. 用于排序结果集\nD. 用于限制返回的记录数量",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "聚合函数与分组"
    },
    {
        "title": "关于HAVING子句，以下说法正确的是？（多选）",
        "description": "关于HAVING子句，以下说法正确的是？（多选）\n\nA. 用于过滤分组后的结果，类似WHERE但用于聚合函数\nB. WHERE在分组前过滤，HAVING在分组后过滤\nC. HAVING必须和GROUP BY一起使用\nD. HAVING可以使用聚合函数作为条件",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "聚合函数与分组"
    },
    {
        "title": "请判断：WHERE和HAVING可以互换使用，没有区别。",
        "description": "请判断：WHERE和HAVING可以互换使用，没有区别。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "聚合函数与分组"
    },
    {
        "title": "以下SQL语句的执行顺序正确的是？",
        "description": "以下SQL语句的执行顺序正确的是？\n\nA. FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY -> LIMIT\nB. SELECT -> FROM -> WHERE -> GROUP BY -> HAVING -> ORDER BY -> LIMIT\nC. FROM -> SELECT -> WHERE -> GROUP BY -> HAVING -> ORDER BY -> LIMIT\nD. SELECT -> FROM -> WHERE -> HAVING -> GROUP BY -> ORDER BY -> LIMIT",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "聚合函数与分组"
    },
    {
        "title": "关于COUNT(*)和COUNT(1)，以下说法正确的是？（多选）",
        "description": "关于COUNT(*)和COUNT(1)，以下说法正确的是？（多选）\n\nA. COUNT(*) 统计所有行，包括NULL值\nB. COUNT(1) 统计所有行，性能通常比COUNT(*)好\nC. COUNT(column) 统计非NULL值的数量\nD. COUNT(DISTINCT column) 统计去重后的非NULL值数量",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "聚合函数与分组"
    },
    {
        "title": "请判断：在SELECT语句中，SELECT子句的执行顺序比WHERE子句晚。",
        "description": "请判断：在SELECT语句中，SELECT子句的执行顺序比WHERE子句晚。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "聚合函数与分组"
    },
    {
        "title": "关于SUM()和AVG()函数，以下说法正确的是？",
        "description": "关于SUM()和AVG()函数，以下说法正确的是？\n\nA. SUM()计算总和，AVG()计算平均值，都会忽略NULL值\nB. SUM()和AVG()都会将NULL值当作0计算\nC. SUM()可以用于文本类型，AVG()只能用于数字类型\nD. SUM()和AVG()都必须和GROUP BY一起使用",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "聚合函数与分组"
    },
    {
        "title": "关于GROUP BY，以下说法错误的是？",
        "description": "关于GROUP BY，以下说法错误的是？\n\nA. SELECT子句中的所有列都必须出现在GROUP BY中，除非它们是聚合函数的一部分\nB. GROUP BY只能按一个列分组\nC. GROUP BY可以与WHERE一起使用\nD. GROUP BY的结果通常是不确定的（除非使用ORDER BY）",
        "solution": "B",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "聚合函数与分组"
    },
    
    # ============ 表连接（JOIN）（10题）============
    {
        "title": "关于INNER JOIN，以下说法正确的是？",
        "description": "关于INNER JOIN，以下说法正确的是？\n\nA. 返回两个表中匹配的记录，即交集\nB. 返回左表的所有记录，即使右表没有匹配\nC. 返回右表的所有记录，即使左表没有匹配\nD. 返回两个表的所有记录，即并集",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "表连接（JOIN）"
    },
    {
        "title": "关于LEFT JOIN（或LEFT OUTER JOIN），以下说法正确的是？（多选）",
        "description": "关于LEFT JOIN（或LEFT OUTER JOIN），以下说法正确的是？（多选）\n\nA. 返回左表的所有记录，即使右表没有匹配\nB. 如果右表没有匹配，结果为NULL\nC. LEFT JOIN等价于RIGHT JOIN，只是方向不同\nD. LEFT JOIN可以省略OUTER关键字",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "表连接（JOIN）"
    },
    {
        "title": "请判断：FULL OUTER JOIN返回左表和右表的所有记录，即使没有匹配。",
        "description": "请判断：FULL OUTER JOIN返回左表和右表的所有记录，即使没有匹配。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "表连接（JOIN）"
    },
    {
        "title": "关于CROSS JOIN（笛卡尔积），以下说法正确的是？",
        "description": "关于CROSS JOIN（笛卡尔积），以下说法正确的是？\n\nA. 返回两个表中所有记录的组合，结果集大小 = 表1行数 × 表2行数\nB. 返回两个表中匹配的记录\nC. 返回左表的所有记录\nD. 返回右表的所有记录",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "表连接（JOIN）"
    },
    {
        "title": "关于SELF JOIN（自连接），以下说法正确的是？（多选）",
        "description": "关于SELF JOIN（自连接），以下说法正确的是？（多选）\n\nA. 一个表与自己连接，需要为表起不同的别名\nB. 常用于查询层级关系（如员工和经理在同一张表）\nC. SELF JOIN是SQL的关键字\nD. SELF JOIN本质上是INNER JOIN或LEFT JOIN的特殊用法",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "表连接（JOIN）"
    },
    {
        "title": "请判断：在SQL中，JOIN条件可以放在WHERE子句中，效果与ON子句完全相同。",
        "description": "请判断：在SQL中，JOIN条件可以放在WHERE子句中，效果与ON子句完全相同。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "表连接（JOIN）"
    },
    {
        "title": "关于多表连接，以下说法正确的是？",
        "description": "关于多表连接，以下说法正确的是？\n\nA. 可以连接多个表，但需要注意性能问题\nB. 最多只能连接2个表\nC. 连接表的顺序不影响结果\nD. 多表连接只能使用INNER JOIN",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "表连接（JOIN）"
    },
    {
        "title": "关于ON和WHERE在LEFT JOIN中的区别，以下说法正确的是？（多选）",
        "description": "关于ON和WHERE在LEFT JOIN中的区别，以下说法正确的是？（多选）\n\nA. ON中的条件在连接时生效，WHERE中的条件在连接后生效\nB. 如果条件放在WHERE中，可能会将LEFT JOIN变成INNER JOIN的效果\nC. ON和WHERE在LEFT JOIN中没有区别\nD. 通常建议将连接条件放在ON中，过滤条件放在WHERE中",
        "solution": "A,B,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "表连接（JOIN）"
    },
    {
        "title": "请判断：RIGHT JOIN可以完全用LEFT JOIN替代，只需要交换表的顺序。",
        "description": "请判断：RIGHT JOIN可以完全用LEFT JOIN替代，只需要交换表的顺序。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "表连接（JOIN）"
    },
    {
        "title": "关于UNION和UNION ALL，以下说法正确的是？",
        "description": "关于UNION和UNION ALL，以下说法正确的是？\n\nA. UNION会去除重复记录，UNION ALL会保留所有记录（性能更好）\nB. UNION和UNION ALL都会去除重复记录\nC. UNION和UNION ALL都会保留所有记录\nD. UNION ALL会去除重复记录，UNION会保留所有记录",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "表连接（JOIN）"
    },
    
    # ============ 数据操作（INSERT/UPDATE/DELETE）（5题）============
    {
        "title": "关于INSERT语句，以下说法正确的是？（多选）",
        "description": "关于INSERT语句，以下说法正确的是？（多选）\n\nA. INSERT INTO table_name (column1, column2) VALUES (value1, value2)\nB. 如果为所有列插入值，可以省略列名\nC. 可以一次插入多行记录（INSERT INTO ... VALUES (...), (...), (...)）\nD. INSERT语句会返回插入的记录数",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "数据操作"
    },
    {
        "title": "关于UPDATE语句，以下说法正确的是？",
        "description": "关于UPDATE语句，以下说法正确的是？\n\nA. 必须使用WHERE子句指定条件，否则会更新所有记录\nB. 不需要WHERE子句，默认只更新第一行\nC. UPDATE语句不能更新多个列\nD. UPDATE语句会返回更新的记录数",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "数据操作"
    },
    {
        "title": "请判断：DELETE语句会删除表结构，TRUNCATE语句只删除数据但保留表结构。",
        "description": "请判断：DELETE语句会删除表结构，TRUNCATE语句只删除数据但保留表结构。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "数据操作"
    },
    {
        "title": "关于DELETE和TRUNCATE的区别，以下说法正确的是？（多选）",
        "description": "关于DELETE和TRUNCATE的区别，以下说法正确的是？（多选）\n\nA. DELETE是DML，可以带WHERE条件；TRUNCATE是DDL，不能带WHERE条件\nB. DELETE逐行删除，效率较低；TRUNCATE整体删除，效率较高\nC. DELETE会触发触发器；TRUNCATE不会触发触发器\nD. DELETE可以回滚；TRUNCATE不能回滚（在某些数据库中）",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "数据操作"
    },
    {
        "title": "请判断：在执行DELETE或UPDATE语句时，如果不加WHERE条件，会操作表中的所有记录。",
        "description": "请判断：在执行DELETE或UPDATE语句时，如果不加WHERE条件，会操作表中的所有记录。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "数据操作"
    },
]

def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 删除学习路径2的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 2")
    print(f"🗑️  已删除学习路径2（SQL数据库基础）的旧习题")
    
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
                VALUES (?, ?, ?, ?, ?, 2, ?, 1, ?, datetime('now'), datetime('now'))
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 2", (inserted,))
    conn.commit()
    
    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径2（SQL数据库基础）")
    
    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 2")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径2现在有 {count} 道习题")
    
    conn.close()

if __name__ == "__main__":
    main()
