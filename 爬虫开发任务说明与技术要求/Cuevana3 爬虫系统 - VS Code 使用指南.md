# Cuevana3 爬虫系统 - VS Code 使用指南

## 🚀 快速开始

### 1. 安装 VS Code

如果您还没有安装 VS Code：
1. 访问：https://code.visualstudio.com/
2. 下载并安装适合您系统的版本

### 2. 打开项目

**方法1：通过 VS Code 打开**
1. 启动 VS Code
2. 点击 "文件" → "打开文件夹"
3. 选择 `cuevana3_v2` 文件夹

**方法2：通过命令行打开**
```bash
cd /path/to/cuevana3_v2
code .
```

### 3. 安装推荐扩展

首次打开项目时，VS Code 会提示安装推荐的扩展：

**必需扩展：**
- ✅ **Python** (ms-python.python) - Python 语言支持
- ✅ **Pylance** (ms-python.vscode-pylance) - Python 智能提示
- ✅ **Python Debugger** (ms-python.debugpy) - Python 调试器

**推荐扩展：**
- 📊 **Rainbow CSV** - CSV 文件高亮显示
- 📝 **Markdown All in One** - Markdown 编辑增强
- 📝 **Markdown Preview Enhanced** - Markdown 预览增强
- 💻 **PowerShell** - Windows 脚本支持

点击 "安装全部" 即可一键安装。

### 4. 安装 Python 依赖

**方法1：使用 VS Code 任务**
1. 按 `Ctrl+Shift+P` (Mac: `Cmd+Shift+P`)
2. 输入 "Tasks: Run Task"
3. 选择 "📦 安装依赖"

**方法2：使用终端**
1. 在 VS Code 中打开终端：`` Ctrl+` ``
2. 运行：
```bash
pip install -r requirements.txt
```

---

## 🎯 使用 VS Code 运行爬虫

### 方法1：使用任务（推荐）⭐

VS Code 已经为您配置好了常用任务，无需手动输入命令！

#### 运行任务的步骤：

1. **打开任务菜单**
   - 按 `Ctrl+Shift+P` (Mac: `Cmd+Shift+P`)
   - 输入 "Tasks: Run Task"
   - 或者按 `Ctrl+Shift+B` 快速打开

2. **选择任务**
   - 🎬 爬取2025年电影
   - 🎬 爬取最近2年电影
   - 📺 爬取20部电视剧
   - 🔄 更新所有数据
   - 📊 查看统计信息
   - 💾 导出所有数据
   - ⚙️ 查看配置

3. **查看输出**
   - 任务会在新的终端面板中运行
   - 可以实时查看爬取进度

#### 任务列表说明

| 任务名称 | 功能 | 等效命令 |
|---------|------|---------|
| 🎬 爬取2025年电影 | 爬取2025年电影（最多5页） | `python main.py movies --year-start 2025 --max-pages 5` |
| 🎬 爬取最近2年电影 | 爬取2024-2025年电影 | `python main.py movies --year-start 2024 --year-end 2025` |
| 📺 爬取20部电视剧 | 爬取20部电视剧 | `python main.py tv --max-series 20 --max-pages 2` |
| 🔄 更新所有数据 | 更新电影和电视剧 | `python main.py update` |
| 📊 查看统计信息 | 显示数据库统计 | `python main.py stats` |
| 💾 导出所有数据 | 导出CSV文件 | `python main.py export --type all` |
| ⚙️ 查看配置 | 显示当前配置 | `python config_manager.py --show` |

### 方法2：使用调试器

VS Code 的调试功能可以让您逐步执行代码，查看变量值，非常适合开发和调试。

#### 使用调试器的步骤：

1. **打开调试面板**
   - 点击左侧的 "运行和调试" 图标
   - 或按 `Ctrl+Shift+D` (Mac: `Cmd+Shift+D`)

2. **选择调试配置**
   - 🎬 调试: 爬取电影
   - 📺 调试: 爬取电视剧
   - 🔄 调试: 更新所有数据
   - 📊 调试: 查看统计
   - 💾 调试: 导出数据
   - ⚙️ 调试: 配置管理
   - 🐍 调试: 当前文件

3. **开始调试**
   - 点击绿色的播放按钮
   - 或按 `F5`

4. **调试功能**
   - **断点**：点击行号左侧设置断点
   - **单步执行**：`F10` (逐过程) 或 `F11` (逐语句)
   - **继续执行**：`F5`
   - **查看变量**：在左侧面板查看变量值
   - **监视表达式**：添加自定义表达式监视

### 方法3：使用集成终端

如果您喜欢命令行方式：

1. **打开终端**
   - 按 `` Ctrl+` `` (反引号键)
   - 或者菜单：终端 → 新建终端

2. **运行命令**
```bash
# 爬取电影
python main.py movies --year-start 2025

# 爬取电视剧
python main.py tv --max-series 20

# 更新所有数据
python main.py update

# 查看统计
python main.py stats

# 导出数据
python main.py export --type all

# 配置管理
python config_manager.py --show
```

---

## ⚙️ 配置管理

### 在 VS Code 中管理配置

#### 1. 查看当前配置

**使用任务：**
1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. 选择 "⚙️ 查看配置"

**使用终端：**
```bash
python config_manager.py --show
```

#### 2. 修改配置

**方法1：直接编辑配置文件**
1. 在 VS Code 中打开 `config.ini`
2. 修改配置项
3. 保存文件 (`Ctrl+S`)

**示例配置：**
```ini
[Database]
database_path = D:\cuevana3_data\cuevana3.db

[Export]
export_directory = D:\cuevana3_data\exports
movies_filename = movies.csv
tv_series_filename = tv_series.csv

[Scraper]
delay_min = 1.0
delay_max = 3.0
max_retries = 3
```

**方法2：使用命令行**
```bash
# 设置数据库路径
python config_manager.py --set database_path "D:\cuevana3_data\cuevana3.db"

# 设置导出目录
python config_manager.py --set export_directory "D:\cuevana3_data\exports"

# 设置延迟时间
python config_manager.py --set delay_min 0.5
python config_manager.py --set delay_max 1.5
```

---

## 🔍 代码浏览和编辑

### 项目结构

```
cuevana3_v2/
├── .vscode/                    # VS Code 配置目录 ⭐
│   ├── tasks.json             # 任务配置
│   ├── launch.json            # 调试配置
│   ├── settings.json          # 编辑器设置
│   └── extensions.json        # 推荐扩展
├── main.py                     # 主程序入口
├── config_manager.py           # 配置管理
├── database.py                 # 数据库操作
├── movie_scraper.py            # 电影爬虫
├── tv_scraper.py               # 电视剧爬虫
├── cuevana3_launcher.bat       # Windows 启动脚本
├── config.ini                  # 配置文件
├── requirements.txt            # Python 依赖
└── *.md                        # 文档文件
```

### 快捷键

#### 导航
- `Ctrl+P` - 快速打开文件
- `Ctrl+Shift+F` - 全局搜索
- `Ctrl+G` - 跳转到指定行
- `F12` - 跳转到定义
- `Alt+←/→` - 前进/后退

#### 编辑
- `Ctrl+/` - 注释/取消注释
- `Ctrl+D` - 选择下一个相同内容
- `Alt+↑/↓` - 移动行
- `Shift+Alt+↑/↓` - 复制行
- `Ctrl+Shift+K` - 删除行

#### 终端
- `` Ctrl+` `` - 打开/关闭终端
- `Ctrl+Shift+5` - 拆分终端
- `Ctrl+Shift+C` - 复制
- `Ctrl+Shift+V` - 粘贴

#### 调试
- `F5` - 开始调试/继续
- `F9` - 设置/取消断点
- `F10` - 单步跳过
- `F11` - 单步进入
- `Shift+F11` - 单步跳出
- `Shift+F5` - 停止调试

---

## 📊 查看和编辑数据

### 查看 CSV 文件

VS Code 安装了 Rainbow CSV 扩展后，可以美化显示 CSV 文件：

1. 在 VS Code 中打开 `movies.csv` 或 `tv_series.csv`
2. CSV 文件会以彩色列显示，更易阅读
3. 可以使用 SQL 查询功能（右键 → "RBQL: Query"）

### 查看数据库

**方法1：使用 SQLite 扩展**
1. 安装扩展：`alexcvzz.vscode-sqlite`
2. 右键点击 `cuevana3.db`
3. 选择 "Open Database"

**方法2：使用命令行**
```bash
sqlite3 cuevana3.db
.tables
SELECT * FROM movies LIMIT 10;
.quit
```

### 查看日志

日志文件保存在 `logs/` 目录下：

1. 在 VS Code 中打开 `logs` 文件夹
2. 选择最新的日志文件
3. 可以使用搜索功能查找特定内容

---

## 🎨 自定义配置

### 修改任务配置

编辑 `.vscode/tasks.json` 添加自定义任务：

```json
{
    "label": "🎬 爬取自定义年份",
    "type": "shell",
    "command": "python",
    "args": [
        "main.py",
        "movies",
        "--year-start",
        "2020",
        "--year-end",
        "2025",
        "--max-pages",
        "10"
    ],
    "problemMatcher": [],
    "group": "build"
}
```

### 修改调试配置

编辑 `.vscode/launch.json` 添加自定义调试配置：

```json
{
    "name": "🎬 调试: 自定义电影爬取",
    "type": "debugpy",
    "request": "launch",
    "program": "${workspaceFolder}/main.py",
    "console": "integratedTerminal",
    "args": [
        "movies",
        "--year-start",
        "2020",
        "--year-end",
        "2025"
    ]
}
```

---

## 💡 使用技巧

### 1. 多终端同时运行

您可以同时打开多个终端，分别运行不同的任务：

1. 打开第一个终端：`` Ctrl+` ``
2. 点击终端右上角的 "+" 号创建新终端
3. 在不同终端中运行不同的命令

**示例：**
- 终端1：运行爬虫
- 终端2：查看统计信息
- 终端3：查看日志

### 2. 使用代码片段

在 Python 文件中输入以下前缀，然后按 `Tab` 快速插入代码：

- `def` - 函数定义
- `class` - 类定义
- `if` - if 语句
- `for` - for 循环
- `try` - try-except 块

### 3. 使用 Git 集成

VS Code 内置 Git 支持：

1. 点击左侧的 "源代码管理" 图标
2. 可以查看修改、提交、推送等
3. 快捷键：`Ctrl+Shift+G`

### 4. 分屏编辑

- `Ctrl+\` - 拆分编辑器
- `Ctrl+1/2/3` - 切换到第1/2/3个编辑器
- 拖动文件标签到侧边 - 手动分屏

### 5. Markdown 预览

查看文档时：
- `Ctrl+Shift+V` - 打开 Markdown 预览
- `Ctrl+K V` - 在侧边打开预览

---

## 🔧 常见问题

### Q1: VS Code 找不到 Python？

**A:** 需要配置 Python 解释器：

1. 按 `Ctrl+Shift+P`
2. 输入 "Python: Select Interpreter"
3. 选择已安装的 Python 版本

### Q2: 终端中文乱码？

**A:** 在 Windows 上：

1. 打开终端
2. 输入：`chcp 65001`
3. 或者使用 PowerShell 终端

### Q3: 任务运行失败？

**A:** 检查以下几点：

1. Python 是否正确安装
2. 依赖包是否已安装
3. 当前工作目录是否正确
4. 查看终端输出的错误信息

### Q4: 如何在 VS Code 中运行 Windows 批处理脚本？

**A:** 

1. 右键点击 `cuevana3_launcher.bat`
2. 选择 "在集成终端中打开"
3. 输入 `.\cuevana3_launcher.bat` 运行

或者直接在文件资源管理器中双击运行。

### Q5: 调试时如何查看变量值？

**A:** 

1. 设置断点（点击行号左侧）
2. 按 `F5` 开始调试
3. 程序暂停时，在左侧 "变量" 面板查看
4. 或者将鼠标悬停在变量上查看

---

## 🎯 推荐工作流

### 开发和调试

1. **在 VS Code 中打开项目**
2. **修改代码**（如果需要）
3. **使用调试器测试**
   - 设置断点
   - 按 `F5` 开始调试
   - 逐步执行，查看变量
4. **使用任务运行完整爬取**
5. **查看结果**
   - 使用 "📊 查看统计信息" 任务
   - 在 VS Code 中打开 CSV 文件

### 日常使用

1. **打开 VS Code**
2. **运行任务**
   - `Ctrl+Shift+B`
   - 选择 "🔄 更新所有数据"
3. **查看结果**
   - 选择 "📊 查看统计信息"
   - 选择 "💾 导出所有数据"

### 批量爬取

1. **修改任务配置**
   - 编辑 `.vscode/tasks.json`
   - 调整年份范围和页数限制
2. **运行自定义任务**
3. **监控进度**
   - 在终端中查看实时输出
   - 查看 `logs/` 目录中的日志

---

## 📚 扩展推荐

### 必装扩展

| 扩展名 | ID | 功能 |
|--------|----|----|
| Python | ms-python.python | Python 语言支持 |
| Pylance | ms-python.vscode-pylance | 智能提示和类型检查 |
| Python Debugger | ms-python.debugpy | Python 调试器 |

### 推荐扩展

| 扩展名 | ID | 功能 |
|--------|----|----|
| Rainbow CSV | mechatroner.rainbow-csv | CSV 文件高亮 |
| Markdown All in One | yzhang.markdown-all-in-one | Markdown 编辑增强 |
| Markdown Preview Enhanced | shd101wyy.markdown-preview-enhanced | Markdown 预览增强 |
| PowerShell | ms-vscode.powershell | PowerShell 支持 |
| SQLite | alexcvzz.vscode-sqlite | SQLite 数据库查看 |
| GitLens | eamodio.gitlens | Git 增强功能 |

---

## 🎉 总结

使用 VS Code 的优势：

✅ **图形化界面**：无需记忆命令，点击即可运行
✅ **调试功能**：可以逐步执行代码，查看变量
✅ **代码编辑**：强大的代码编辑和智能提示
✅ **集成终端**：在编辑器中直接运行命令
✅ **扩展丰富**：可以安装各种扩展增强功能
✅ **跨平台**：Windows、Mac、Linux 都可以使用

**现在您可以在 VS Code 中享受完整的开发体验了！** 🚀

---

## 📞 相关文档

- [README.md](README.md) - 完整文档
- [QUICKSTART.md](QUICKSTART.md) - 快速入门
- [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) - Windows 使用指南
- [CRONTAB_SETUP.md](CRONTAB_SETUP.md) - 定时任务设置

---

**祝您使用愉快！** 🎉
