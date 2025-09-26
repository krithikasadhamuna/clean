#!/usr/bin/env python3
"""
Setup script for AI SOC Platform with Log Forwarding
"""

from setuptools import setup, find_packages
import os

def read_requirements():
    """Read requirements from requirements.txt"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r') as f:
        requirements = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements

setup(
    name="ai-soc-platform",
    version="1.0.0",
    description="AI-powered Security Operations Center platform with attack simulation and log forwarding",
    author="SOC Team",
    author_email="soc@company.com",
    packages=find_packages(),
    install_requires=read_requirements(),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: System :: Monitoring",
    ],
    entry_points={
        'console_scripts': [
            'ai-soc=main:main',
            'phantomstrike-server=log_forwarding.server.server_manager:main',
            'phantomstrike-client=log_forwarding.client.client_agent:main',
        ],
    },
    include_package_data=True,
    package_data={
        'config': ['*.yaml'],
        'ml_models': ['*.pkl', '*.joblib', '*.json'],
    },
)
