#!/usr/bin/env python3
"""
Setup script for CogniFlow - DSA Assistant
"""

from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="cogniflow",
    version="1.0.0",
    author="DSA Developer",
    author_email="",  # Add your email
    description="Assistente DSA con AI locale e interfaccia accessibile",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/cogniflow",  # Update with actual repo
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Education",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "black>=23.0.0",
        ],
        "ocr": [
            "pytesseract>=0.3.10",
        ],
        "speech": [
            "pyaudio>=0.2.13",
        ],
    },
    entry_points={
        "console_scripts": [
            "cogniflow=main_00_launcher:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.qml", "*.json", "*.md"],
    },
    data_files=[
        ("share/applications", ["cogniflow.desktop"]),
        ("share/icons/hicolor/256x256/apps", ["assistente_dsa/ICO-fonts-wallpaper/icon.png"]),
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/cogniflow/issues",
        "Source": "https://github.com/yourusername/cogniflow",
    },
)