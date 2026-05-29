#!/usr/bin/env python3
"""
学习路径4：Python编程基础 - 50道精品题
基于Python编程的真实课程内容出题
"""

import sqlite3

db_path = "c:/Users/lenovo/Desktop/TestMasterProject/instance/testmaster.db"

# 学习路径4的50道精品题
exercises_data = [
    # ============ Python基础概念（10题）============
    {
        "title": "Python是一种什么样的编程语言？",
        "description": "Python是一种什么样的编程语言？\n\nA. 解释型、面向对象、动态数据类型的高级编程语言\nB. 编译型、面向过程、静态数据类型的高级编程语言\nC. 解释型、面向过程、静态数据类型的高级编程语言\nD. 编译型、面向对象、动态数据类型的高级编程语言",
        "solution": "A",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "Python基础概念",
    },
    {
        "title": "关于Python的特点，以下说法正确的是？（多选）",
        "description": "关于Python的特点，以下说法正确的是？（多选）\n\nA. 语法简洁清晰，易于学习和阅读\nB. 拥有丰富的第三方库，生态完善\nC. 跨平台，可在Windows、Linux、MacOS等系统上运行\nD. 执行速度比C/C++快",
        "solution": "A,B,C",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Python基础概念",
    },
    {
        "title": "请判断：Python是一种编译型语言，需要先将源代码编译成机器码才能运行。",
        "description": "请判断：Python是一种编译型语言，需要先将源代码编译成机器码才能运行。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "Python基础概念",
    },
    {
        "title": "关于Python的解释器，以下说法正确的是？",
        "description": "关于Python的解释器，以下说法正确的是？\n\nA. CPython是官方默认解释器，用C语言编写\nB. PyPy是官方默认解释器，执行速度最快\nC. Jython是运行在JVM（Java虚拟机）上的Python解释器\nD. IronPython是运行在.NET平台上的Python解释器",
        "solution": "A,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "Python基础概念",
    },
    {
        "title": "关于Python的版本，以下说法正确的是？",
        "description": "关于Python的版本，以下说法正确的是？\n\nA. Python 2.x和Python 3.x是不兼容的\nB. Python 2.x已经停止维护，推荐使用Python 3.x\nC. Python 3.x完全向前兼容Python 2.x\nD. Python 3.x的执行速度比Python 2.x快",
        "solution": "A,B",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Python基础概念",
    },
    {
        "title": "请判断：Python的源代码文件的扩展名是 `.py`，编译后的字节码文件扩展名是 `.pyc`。",
        "description": "请判断：Python的源代码文件的扩展名是 `.py`，编译后的字节码文件扩展名是 `.pyc`。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "Python基础概念",
    },
    {
        "title": "关于Python的标识符命名规则，以下说法正确的是？",
        "description": "关于Python的标识符命名规则，以下说法正确的是？\n\nA. 标识符可以以字母或下划线开头，但不能以数字开头\nB. 标识符区分大小写，例如 `var` 和 `Var` 是两个不同的标识符\nC. 标识符不能使用Python的关键字（如 if、for、while等）\nD. 标识符可以包含字母、数字、下划线，但不能包含其他特殊字符",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Python基础概念",
    },
    {
        "title": "关于Python的关键字，以下说法正确的是？（多选）",
        "description": "关于Python的关键字，以下说法正确的是？（多选）\n\nA. 可以使用 `keyword` 模块查看所有关键字\nB. Python有35个关键字（Python 3.9+）\nC. `if`、`else`、`elif` 是条件判断的关键字\nD. `for`、`while`、`break`、`continue` 是循环相关的关键字",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Python基础概念",
    },
    {
        "title": "请判断：Python中的单行注释以 `#` 开头，多行注释可以用三个单引号 `'''` 或三个双引号 `'''` 包裹。",
        "description": "请判断：Python中的单行注释以 `#` 开头，多行注释可以用三个单引号 `'''` 或三个双引号 `'''` 包裹。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "Python基础概念",
    },
    {
        "title": "关于Python的代码缩进，以下说法正确的是？",
        "description": "关于Python的代码缩进，以下说法正确的是？\n\nA. Python使用缩进来表示代码块，而不是使用花括号 {}\nB. 缩进可以使用空格或制表符（Tab），但不建议混用\nC. 官方推荐缩进使用4个空格\nD. 缩进是Python语法的一部分，不正确的缩进会导致语法错误",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "Python基础概念",
    },
    # ============ 变量与数据类型（15题）============
    {
        "title": "关于Python的变量，以下说法正确的是？",
        "description": "关于Python的变量，以下说法正确的是？\n\nA. Python中的变量不需要声明，直接赋值即可创建\nB. 变量赋值后可以再次赋值，且可以改变数据类型\nC. 变量只是对对象的引用（引用传递）\nD. 可以使用 `del` 语句删除变量",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "category": "变量与数据类型",
    },
    {
        "title": "关于Python的数值类型，以下说法正确的是？（多选）",
        "description": "关于Python的数值类型，以下说法正确的是？（多选）\n\nA. `int` 表示整数，可以是任意大小的整数（Python 3+）\nB. `float` 表示浮点数，使用64位双精度表示\nC. `complex` 表示复数，如 `3+4j`\nD. 可以使用 `type()` 函数查看变量的数据类型",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "变量与数据类型",
    },
    {
        "title": "请判断：在Python中，`/` 运算符用于整数除法（结果向下取整），`//` 运算符用于浮点数除法（结果保留小数）。",
        "description": "请判断：在Python中，`/` 运算符用于整数除法（结果向下取整），`//` 运算符用于浮点数除法（结果保留小数）。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "变量与数据类型",
    },
    {
        "title": "关于Python的字符串，以下说法正确的是？",
        "description": "关于Python的字符串，以下说法正确的是？\n\nA. 字符串可以用单引号、双引号或三引号定义\nB. 字符串是不可变类型（immutable），不能修改字符串中的某个字符\nC. 可以使用 `+` 运算符拼接字符串，使用 `*` 运算符重复字符串\nD. 可以使用切片（slice）访问字符串的子串，如 `s[1:3]`",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "变量与数据类型",
    },
    {
        "title": "关于Python的列表（List），以下说法正确的是？（多选）",
        "description": "关于Python的列表（List），以下说法正确的是？（多选）\n\nA. 列表是有序的可变序列，可以包含不同类型的元素\nB. 可以使用 `append()` 方法在列表末尾添加元素\nC. 可以使用 `insert()` 方法在指定位置插入元素\nD. 可以使用 `remove()` 方法删除第一个匹配的元素",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "变量与数据类型",
    },
    {
        "title": "请判断：Python中的元组（Tuple）和列表（List）一样，都是可变类型，可以修改其中的元素。",
        "description": "请判断：Python中的元组（Tuple）和列表（List）一样，都是可变类型，可以修改其中的元素。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "变量与数据类型",
    },
    {
        "title": "关于Python的字典（Dictionary），以下说法正确的是？",
        "description": "关于Python的字典（Dictionary），以下说法正确的是？\n\nA. 字典是无序的键值对集合，键必须是不可变类型\nB. 可以使用 `{}` 或 `dict()` 创建字典\nC. 可以使用 `keys()` 方法获取所有键，使用 `values()` 方法获取所有值\nD. 可以使用 `get()` 方法获取键对应的值，如果键不存在则返回None（不会抛出异常）",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "变量与数据类型",
    },
    {
        "title": "关于Python的集合（Set），以下说法正确的是？（多选）",
        "description": "关于Python的集合（Set），以下说法正确的是？（多选）\n\nA. 集合是无序的不重复元素集合\nB. 可以使用 `{}` 或 `set()` 创建集合\nC. 支持集合运算：并集（|）、交集（&）、差集（-）、对称差集（^）\nD. 可以使用 `add()` 方法添加元素，使用 `remove()` 方法删除元素",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "变量与数据类型",
    },
    {
        "title": "请判断：在Python中，空字符串 `''`、空列表 `[]`、空元组 `()`、空字典 `{}` 的布尔值都是 `False`。",
        "description": "请判断：在Python中，空字符串 `''`、空列表 `[]`、空元组 `()`、空字典 `{}` 的布尔值都是 `False`。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "变量与数据类型",
    },
    {
        "title": "关于Python的类型转换，以下说法正确的是？",
        "description": "关于Python的类型转换，以下说法正确的是？\n\nA. `int(x)` 可以将x转换为整数，`float(x)` 可以将x转换为浮点数\nB. `str(x)` 可以将x转换为字符串，`list(x)` 可以将可迭代对象x转换为列表\nC. `tuple(x)` 可以将可迭代对象x转换为元组，`set(x)` 可以将可迭代对象x转换为集合\nD. 类型转换可能会失败（抛出异常），如 `int('abc')`",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "变量与数据类型",
    },
    {
        "title": "关于Python的输入输出，以下说法正确的是？（多选）",
        "description": "关于Python的输入输出，以下说法正确的是？（多选）\n\nA. `input()` 函数用于从标准输入读取用户输入，返回类型是字符串\nB. `print()` 函数用于向标准输出打印内容，可以指定分隔符（sep）和结束符（end）\nC. 可以使用 f-string（格式化字符串字面值）进行字符串格式化，如 `f'Hello, {name}!'`\nD. 可以使用 `format()` 方法进行字符串格式化，如 `'Hello, {}!'.format(name)`",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "category": "变量与数据类型",
    },
    {
        "title": "请判断：Python中的 `is` 运算符用于比较两个变量的值是否相等，`==` 运算符用于比较两个变量是否指向同一个对象。",
        "description": "请判断：Python中的 `is` 运算符用于比较两个变量的值是否相等，`==` 运算符用于比较两个变量是否指向同一个对象。\n\nA. 正确\nB. 错误",
        "solution": "B",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "变量与数据类型",
    },
    {
        "title": "关于Python的运算符优先级，以下说法正确的是？",
        "description": "关于Python的运算符优先级，以下说法正确的是？\n\nA. 算术运算符 > 比较运算符 > 逻辑运算符 > 赋值运算符\nB. 可以使用圆括号 `()` 改变运算符的优先级\nC. `**`（幂运算）的优先级高于 `*`、`/`、`//`、`%`\nD. `not` 的优先级高于 `and`，`and` 的优先级高于 `or`",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "变量与数据类型",
    },
    {
        "title": "关于Python的赋值运算符，以下说法正确的是？（多选）",
        "description": "关于Python的赋值运算符，以下说法正确的是？（多选）\n\nA. 可以使用 `=` 进行简单赋值，使用 `+=`、`-=` 等进行复合赋值\nB. 可以使用 `:=` 海象运算符（Python 3.8+）在表达式中进行赋值\nC. 可以使用 `*` 和 `**` 进行可迭代对象拆包，如 `a, *b, c = [1, 2, 3, 4, 5]`\nD. 可以使用链式赋值，如 `a = b = c = 0`",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "变量与数据类型",
    },
    # ============ 控制流（10题）============
    {
        "title": "关于Python的条件判断，以下说法正确的是？",
        "description": "关于Python的条件判断，以下说法正确的是？\n\nA. `if` 语句用于条件判断，`elif` 用于else if，`else` 用于其他情况\nB. 条件判断可以嵌套，但不建议嵌套过深（可读性差）\nC. 可以使用三元运算符：`x if condition else y`\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "控制流",
    },
    {
        "title": "关于Python的循环，以下说法正确的是？（多选）",
        "description": "关于Python的循环，以下说法正确的是？（多选）\n\nA. `for` 循环用于遍历可迭代对象（如列表、元组、字符串、字典等）\nB. `while` 循环用于在条件为真时重复执行代码块\nC. 可以使用 `break` 语句提前退出循环，使用 `continue` 语句跳过本次循环\nD. 可以使用 `else` 子句：循环正常结束（没有被break中断）时执行",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "控制流",
    },
    {
        "title": "请判断：`range(5)` 生成的序列是 `[0, 1, 2, 3, 4]`，`range(1, 5)` 生成的序列是 `[1, 2, 3, 4]`，`range(1, 5, 2)` 生成的序列是 `[1, 3]`。",
        "description": "请判断：`range(5)` 生成的序列是 `[0, 1, 2, 3, 4]`，`range(1, 5)` 生成的序列是 `[1, 2, 3, 4]`，`range(1, 5, 2)` 生成的序列是 `[1, 3]`。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "控制流",
    },
    {
        "title": "关于Python的列表推导式，以下说法正确的是？",
        "description": "关于Python的列表推导式，以下说法正确的是？\n\nA. 列表推导式的语法是 `[expression for item in iterable if condition]`\nB. 可以使用列表推导式快速生成列表，代码更简洁\nC. 列表推导式可以有多个for循环，如 `[(x, y) for x in range(3) for y in range(3)]`\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "控制流",
    },
    {
        "title": "关于Python的生成器推导式，以下说法正确的是？（多选）",
        "description": "关于Python的生成器推导式，以下说法正确的是？（多选）\n\nA. 生成器推导式的语法是 `(expression for item in iterable if condition)`，使用圆括号\nB. 生成器推导式返回的是一个生成器对象，不会立即生成所有结果（节省内存）\nC. 可以使用 `next()` 函数或 `for` 循环获取生成器中的下一个值\nD. 生成器只能遍历一次，遍历完后需要重新创建",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "控制流",
    },
    {
        "title": "请判断：在Python中，可以使用 `pass` 语句作为占位符，表示什么也不做。",
        "description": "请判断：在Python中，可以使用 `pass` 语句作为占位符，表示什么也不做。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "控制流",
    },
    {
        "title": "关于Python的异常处理，以下说法正确的是？",
        "description": "关于Python的异常处理，以下说法正确的是？\n\nA. 可以使用 `try...except...else...finally` 结构捕获和处理异常\nB. `try` 块中放置可能出现异常的代码，`except` 块中放置异常处理代码\nC. `else` 块在 `try` 块没有抛出异常时执行，`finally` 块无论是否抛出异常都会执行\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "medium",
        "category": "控制流",
    },
    {
        "title": "关于Python的常见异常类型，以下说法正确的是？（多选）",
        "description": "关于Python的常见异常类型，以下说法正确的是？（多选）\n\nA. `SyntaxError`：语法错误，代码无法被解释器解析\nB. `IndentationError`：缩进错误，代码缩进不正确\nC. `NameError`：名称错误，使用了未定义的变量\nD. `TypeError`：类型错误，对不支持的操作类型使用了运算符或函数",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "控制流",
    },
    {
        "title": "请判断：可以使用 `raise` 语句主动抛出异常，使用 `assert` 语句进行断言（条件为假时抛出 `AssertionError`）。",
        "description": "请判断：可以使用 `raise` 语句主动抛出异常，使用 `assert` 语句进行断言（条件为假时抛出 `AssertionError`）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "控制流",
    },
    {
        "title": "关于Python的 `with` 语句，以下说法正确的是？",
        "description": "关于Python的 `with` 语句，以下说法正确的是？\n\nA. `with` 语句用于简化资源管理（如文件操作），会自动调用 `__enter__()` 和 `__exit__()` 方法\nB. 无论是否抛出异常，`with` 语句都会确保资源被正确释放\nC. 可以使用 `with open('file.txt', 'r') as f:` 打开文件，无需手动调用 `f.close()`\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "控制流",
    },
    # ============ 函数与模块（10题）============
    {
        "title": "关于Python的函数定义，以下说法正确的是？",
        "description": "关于Python的函数定义，以下说法正确的是？\n\nA. 使用 `def` 关键字定义函数，函数名后跟圆括号和冒号\nB. 函数可以没有参数，也可以有多个参数\nC. 函数可以返回一个值，也可以使用 `return` 返回多个值（实际上是返回一个元组）\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "easy",
        "category": "函数与模块",
    },
    {
        "title": "关于Python的函数参数，以下说法正确的是？（多选）",
        "description": "关于Python的函数参数，以下说法正确的是？（多选）\n\nA. 位置参数：按照参数位置依次传递，调用时顺序和数量必须匹配\nB. 关键字参数：按照参数名称传递，可以不按顺序，如 `func(b=2, a=1)`\nC. 默认参数：定义函数时给参数指定默认值，调用时可以不传递该参数\nD. 可变参数：`*args` 用于传递任意数量的位置参数，`**kwargs` 用于传递任意数量的关键字参数",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "函数与模块",
    },
    {
        "title": "请判断：在Python中，函数的参数有默认值的情况下，默认参数必须放在非默认参数的后面。",
        "description": "请判断：在Python中，函数的参数有默认值的情况下，默认参数必须放在非默认参数的后面。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "函数与模块",
    },
    {
        "title": "关于Python的变量作用域，以下说法正确的是？",
        "description": "关于Python的变量作用域，以下说法正确的是？\n\nA. 局部变量：在函数内部定义，只能在函数内部访问\nB. 全局变量：在函数外部定义，可以在整个程序中使用，函数内部使用 `global` 关键字可以修改全局变量\nC. 嵌套作用域：内部函数可以访问外部函数的变量，使用 `nonlocal` 关键字可以修改外部函数的变量\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "函数与模块",
    },
    {
        "title": "关于Python的模块和包，以下说法正确的是？（多选）",
        "description": "关于Python的模块和包，以下说法正确的是？（多选）\n\nA. 模块：一个 `.py` 文件就是一个模块\nB. 包：一个包含 `__init__.py` 文件的目录就是一个包（Python 3.3+可以没有 `__init__.py`）\nC. 可以使用 `import` 语句导入模块或包，使用 `from...import` 语句导入特定的函数或类\nD. 可以使用 `if __name__ == '__main__':` 判断模块是被导入还是直接运行",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "函数与模块",
    },
    {
        "title": "请判断：可以使用 `pip` 命令安装第三方包，使用 `pip list` 查看已安装的包，使用 `pip uninstall` 卸载包。",
        "description": "请判断：可以使用 `pip` 命令安装第三方包，使用 `pip list` 查看已安装的包，使用 `pip uninstall` 卸载包。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "easy",
        "category": "函数与模块",
    },
    {
        "title": "关于Python的递归函数，以下说法正确的是？",
        "description": "关于Python的递归函数，以下说法正确的是？\n\nA. 递归函数是指在函数内部调用函数本身\nB. 递归函数必须有递归出口（终止条件），否则会导致无限递归，最终抛出 `RecursionError`\nC. Python默认的最大递归深度是1000层，可以使用 `sys.setrecursionlimit()` 修改\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "函数与模块",
    },
    {
        "title": "关于Python的匿名函数（lambda），以下说法正确的是？（多选）",
        "description": "关于Python的匿名函数（lambda），以下说法正确的是？（多选）\n\nA. 使用 `lambda` 关键字定义匿名函数，语法是 `lambda 参数: 表达式`\nB. 匿名函数只能有一个表达式，不能包含复杂的逻辑\nC. 匿名函数可以作为参数传递给其他函数，常用于 `sorted()`、`map()`、`filter()` 等函数\nD. 匿名函数可以不使用 `return` 语句，表达式的值就是返回值",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "函数与模块",
    },
    {
        "title": "请判断：在Python中，函数也是对象，可以赋值给变量，可以作为参数传递给其他函数，也可以作为返回值。",
        "description": "请判断：在Python中，函数也是对象，可以赋值给变量，可以作为参数传递给其他函数，也可以作为返回值。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "函数与模块",
    },
    {
        "title": "关于Python的装饰器（Decorator），以下说法正确的是？",
        "description": "关于Python的装饰器（Decorator），以下说法正确的是？\n\nA. 装饰器是一种修改函数或类的行为的设计模式，可以在不修改原函数代码的情况下添加功能\nB. 装饰器使用 `@` 语法糖，如 `@decorator`\nC. 可以使用多个装饰器装饰同一个函数，执行顺序是从内到外（从下到上）\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "函数与模块",
    },
    # ============ 面向对象编程（5题）============
    {
        "title": "关于Python的类和对象，以下说法正确的是？（多选）",
        "description": "关于Python的类和对象，以下说法正确的是？（多选）\n\nA. 使用 `class` 关键字定义类，类名通常使用驼峰命名法（如 `MyClass`）\nB. 类是对象的模板，对象是类的实例\nC. 可以使用 `__init__(self)` 方法初始化对象（构造方法）\nD. 可以使用 `self` 关键字引用对象本身",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "medium",
        "category": "面向对象编程",
    },
    {
        "title": "请判断：Python中的继承可以分为单继承（`class Child(Parent):`）和多继承（`class Child(Parent1, Parent2):`）。",
        "description": "请判断：Python中的继承可以分为单继承（`class Child(Parent):`）和多继承（`class Child(Parent1, Parent2):`）。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "medium",
        "category": "面向对象编程",
    },
    {
        "title": "关于Python的方法重载和多态，以下说法正确的是？",
        "description": "关于Python的方法重载和多态，以下说法正确的是？\n\nA. Python不支持方法重载（overloading），但支持方法重写（overriding）\nB. 多态是指不同类的对象对同一消息做出不同的响应\nC. 可以使用 `super()` 函数调用父类的方法\nD. 以上说法都正确",
        "solution": "D",
        "exercise_type": "single_choice",
        "difficulty": "hard",
        "category": "面向对象编程",
    },
    {
        "title": "关于Python的特殊方法（魔术方法），以下说法正确的是？（多选）",
        "description": "关于Python的特殊方法（魔术方法），以下说法正确的是？（多选）\n\nA. 特殊方法是以双下划线开头和结尾的方法，如 `__init__()`、`__str__()`、`__repr__()`\nB. `__str__()` 方法用于返回对象的字符串表示（面向用户），`__repr__()` 方法用于返回对象的官方字符串表示（面向开发者）\nC. 可以重载运算符，如 `__add__()` 对应 `+` 运算符，`__len__()` 对应 `len()` 函数\nD. 以上说法都正确",
        "solution": "A,B,C,D",
        "exercise_type": "multiple_choice",
        "difficulty": "hard",
        "category": "面向对象编程",
    },
    {
        "title": "请判断：在Python中，可以使用 `@property` 装饰器将方法转换为属性，使用 `@method.setter` 装饰器定义属性的setter方法。",
        "description": "请判断：在Python中，可以使用 `@property` 装饰器将方法转换为属性，使用 `@method.setter` 装饰器定义属性的setter方法。\n\nA. 正确\nB. 错误",
        "solution": "A",
        "exercise_type": "true_false",
        "difficulty": "hard",
        "category": "面向对象编程",
    },
]


def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 删除学习路径4的旧习题
    cursor.execute("DELETE FROM exercises WHERE learning_path_id = 4")
    print("🗑️  已删除学习路径4（Python编程基础）的旧习题")

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
                VALUES (?, ?, ?, ?, ?, 4, ?, 1, ?, datetime('now'), datetime('now'))
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
    cursor.execute("UPDATE learning_paths SET exercise_count = ? WHERE id = 4", (inserted,))
    conn.commit()

    print(f"✅ 成功插入 {inserted} 道精品习题到学习路径4（Python编程基础）")

    # 验证
    cursor.execute("SELECT COUNT(*) FROM exercises WHERE learning_path_id = 4")
    count = cursor.fetchone()[0]
    print(f"📊 验证：学习路径4现在有 {count} 道习题")

    conn.close()


if __name__ == "__main__":
    main()
