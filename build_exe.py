#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build script for creating exe from Artale_Bot_Reporter.py
"""

import os
import sys
import shutil
from pathlib import Path

def clean_build():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Cleaned {dir_name} directory")

def build_exe():
    """Build the exe using PyInstaller"""
    
    # Clean previous builds
    clean_build()
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',                    # Create single exe file
        '--windowed',                   # No console window (GUI only)
        '--name=Artale_Bot_Reporter',   # Name of the exe
        '--icon=app_icon.ico',          # Icon (if exists)
        '--add-data=korean_chinese.json;.',  # Include JSON file
        '--hidden-import=cv2',          # Ensure OpenCV is included
        '--hidden-import=numpy',        # Ensure NumPy is included
        '--hidden-import=tkinter',      # Ensure tkinter is included
        '--hidden-import=scapy.all',    # Ensure scapy is included
        '--hidden-import=pygetwindow',  # Ensure pygetwindow is included
        'main.py'        # Main script
    ]
    
    # Check if icon exists, if not remove from command
    if not os.path.exists('app_icon.ico'):
        cmd = [c for c in cmd if not c.startswith('--icon')]
    
    # Execute PyInstaller
    os.system(' '.join(cmd))
    
    print("\n" + "="*50)
    print("Build completed!")
    print("="*50)
    
    # Check if build was successful
    exe_path = Path('dist/Artale_Bot_Reporter.exe')
    if exe_path.exists():
        print(f"✅ Exe file created: {exe_path.absolute()}")
        print(f"📁 File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        
        # Copy additional files to dist folder
        files_to_copy = ['korean_chinese.json', 'watched_maps.json']
        for file_name in files_to_copy:
            if os.path.exists(file_name):
                shutil.copy2(file_name, 'dist/')
                print(f"📋 Copied {file_name} to dist folder")
    else:
        print("❌ Build failed! Check the output above for errors.")

if __name__ == '__main__':
    print("🔨 Building Artale Bot Reporter Exe...")
    build_exe() 