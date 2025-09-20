#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

setup(
    name="mkanban",
    version="0.1.4",
    description="A Terminal User Interface Kanban Board",
    long_description="MKanban is a TUI Kanban board application for managing tasks in a terminal interface.",
    author="blendonl",
    author_email="blendonluta@gmail.com",
    url="https://github.com/blendonl/mkanban",
    packages=find_packages() + ["src", "src.application", "src.application.dto", "src.application.handlers", "src.config", "src.controllers", "src.core", "src.domain", "src.domain.entities", "src.domain.repositories", "src.infrastructure", "src.infrastructure.cli", "src.infrastructure.storage", "src.services", "src.ui", "src.ui.dialogs", "src.ui.widgets", "src.utils"],
    py_modules=["main"],
    include_package_data=True,
    package_data={
        "src.ui": ["*.css"],
    },
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mkanban=main:main",
            "mkanban-daemon=src.scripts.mkanban_daemon:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)

