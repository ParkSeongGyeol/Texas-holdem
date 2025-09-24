from setuptools import setup, find_packages

setup(
    name="texas-holdem-poker",
    version="1.0.0",
    description="Texas Hold'em poker game with AI - Algorithm class team project",
    author="문현준, 박성결, 박종호, 박우현",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "websockets>=12.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "poker-game=src.main:main",
        ],
    },
)