import zipfile
import os
import datetime

def package_project():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"filmpalast_crawler_pkg_{timestamp}.zip"
    
    # Files and directories to include
    includes = [
        'config',
        'src',
        'run_full_crawl.py',
        'run_incremental_crawl.py',
        'deploy.sh',
        'deploy.bat',
        'Dockerfile',
        'docker-compose.yml',
        'requirements.txt',
        'README.md',
        'filmpalast_crawler_technical_documentation.md'
    ]
    
    # Create empty directories in the zip
    empty_dirs = ['data', 'logs', 'exports']
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        print(f"Creating archive: {zip_filename}")
        
        # Add files and directories
        for item in includes:
            if os.path.isfile(item):
                print(f"Adding file: {item}")
                zipf.write(item)
            elif os.path.isdir(item):
                print(f"Adding directory: {item}")
                for root, dirs, files in os.walk(item):
                    # Skip __pycache__
                    if '__pycache__' in dirs:
                        dirs.remove('__pycache__')
                    
                    for file in files:
                        if file.endswith('.pyc'):
                            continue
                        file_path = os.path.join(root, file)
                        print(f"  Adding: {file_path}")
                        zipf.write(file_path)
        
        # Add empty directories (by adding a .gitkeep or similar, or just the dir entry)
        for d in empty_dirs:
            print(f"Adding empty directory structure: {d}/")
            # ZipFile doesn't strictly support empty dirs without files, 
            # usually we add a placeholder or just ensure the code creates them on deploy.
            # Dockerfile already creates them.
            # But let's add a placeholder to ensure structure exists if unzipped manually
            zip_info = zipfile.ZipInfo(d + "/")
            zipf.writestr(zip_info, "")

    print(f"\n✅ Package created successfully: {os.path.abspath(zip_filename)}")

if __name__ == "__main__":
    package_project()
