# 定时任务设置说明

## 方法一：使用 Crontab（Linux/Mac）

### 1. 编辑 crontab
```bash
crontab -e
```

### 2. 添加定时任务

**每天凌晨2点执行：**
```
0 2 * * * /path/to/cuevana3_v2/schedule_task.sh
```

**每天凌晨2点和下午2点执行（一天两次）：**
```
0 2,14 * * * /path/to/cuevana3_v2/schedule_task.sh
```

**每6小时执行一次：**
```
0 */6 * * * /path/to/cuevana3_v2/schedule_task.sh
```

### 3. 查看已设置的定时任务
```bash
crontab -l
```

### 4. 删除定时任务
```bash
crontab -e
# 删除对应行即可
```

## 方法二：使用 systemd timer（Linux）

### 1. 创建 service 文件
```bash
sudo nano /etc/systemd/system/cuevana3-scraper.service
```

内容：
```ini
[Unit]
Description=Cuevana3 Scraper Service
After=network.target

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/path/to/cuevana3_v2
ExecStart=/path/to/cuevana3_v2/schedule_task.sh

[Install]
WantedBy=multi-user.target
```

### 2. 创建 timer 文件
```bash
sudo nano /etc/systemd/system/cuevana3-scraper.timer
```

内容：
```ini
[Unit]
Description=Cuevana3 Scraper Timer
Requires=cuevana3-scraper.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 3. 启用并启动 timer
```bash
sudo systemctl daemon-reload
sudo systemctl enable cuevana3-scraper.timer
sudo systemctl start cuevana3-scraper.timer
```

### 4. 查看 timer 状态
```bash
sudo systemctl status cuevana3-scraper.timer
sudo systemctl list-timers
```

## 方法三：使用 Windows 任务计划程序

### 1. 打开任务计划程序
- 按 Win + R，输入 `taskschd.msc`

### 2. 创建基本任务
1. 点击"创建基本任务"
2. 名称：Cuevana3 Scraper
3. 触发器：每天
4. 时间：凌晨 2:00
5. 操作：启动程序
6. 程序：`python.exe`
7. 参数：`main.py update`
8. 起始于：`C:\path\to\cuevana3_v2`

## Crontab 时间格式说明

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── 星期几 (0-7, 0和7都代表星期日)
│ │ │ └───── 月份 (1-12)
│ │ └─────── 日期 (1-31)
│ └───────── 小时 (0-23)
└─────────── 分钟 (0-59)
```

### 常用示例

- `0 2 * * *` - 每天凌晨2点
- `0 */6 * * *` - 每6小时
- `0 2 * * 1` - 每周一凌晨2点
- `0 2 1 * *` - 每月1号凌晨2点
- `0 2 * * 1-5` - 每周一到周五凌晨2点

## 日志查看

日志文件保存在 `logs/` 目录下，文件名格式：`scraper_YYYYMMDD_HHMMSS.log`

查看最新日志：
```bash
ls -lt logs/ | head -5
cat logs/scraper_*.log | tail -100
```

## 手动执行测试

在设置定时任务前，建议先手动执行测试：
```bash
cd /path/to/cuevana3_v2
./schedule_task.sh
```

或直接使用 Python：
```bash
python3 main.py update
```

## 注意事项

1. **路径问题**：确保 crontab 中使用绝对路径
2. **Python 环境**：确保 crontab 能找到正确的 Python 解释器
3. **权限问题**：确保脚本有执行权限 (`chmod +x`)
4. **日志清理**：脚本会自动清理30天前的日志
5. **数据库备份**：建议定期备份 `cuevana3.db` 文件
