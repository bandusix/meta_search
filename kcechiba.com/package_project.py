
import zipfile
import os
from pathlib import Path

def zip_project(output_filename='kcechiba_com_spider_project.zip'):
    # 需要打包的文件和目录
    include_files = [
        'main.py',
        'requirements.txt',
        'DEPLOY.md',
        'kcechiba_com_策驰影院_爬虫技术文档.md',
        'export_only.py'
    ]
    
    include_dirs = [
        'config',
        'core',
        'spiders',
        'exporters',
        'data' # 只打包目录结构，不打包内容（除了logs目录可能需要存在）
    ]
    
    # 排除模式
    exclude_patterns = [
        '__pycache__',
        '*.pyc',
        'spider.db',
        'spider_v2.db',
        '*.zip',
        '.git',
        '.vscode',
        'test_*'
    ]

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加文件
        for file in include_files:
            if os.path.exists(file):
                print(f"Adding {file}")
                zipf.write(file)
        
        # 添加目录
        for dir_name in include_dirs:
            for root, dirs, files in os.walk(dir_name):
                # 排除目录
                dirs[:] = [d for d in dirs if d not in ['__pycache__']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # 检查排除模式
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern.startswith('*'):
                            if file.endswith(pattern[1:]):
                                should_exclude = True
                                break
                        elif pattern == file:
                            should_exclude = True
                            break
                    
                    # 特殊处理 data 目录，排除已有数据和日志
                    if 'data' in root:
                        if file.endswith('.csv') or file.endswith('.log'):
                            should_exclude = True
                            
                    if not should_exclude:
                        print(f"Adding {file_path}")
                        zipf.write(file_path)
                        
    print(f"\n✅ Project packaged successfully to {output_filename}")

if __name__ == '__main__':
    zip_project()
