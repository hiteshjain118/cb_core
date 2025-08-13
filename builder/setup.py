from setuptools import setup, find_packages # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="builder",
    version="0.1.0",
    author="Hitesh Jain",
    author_email="hitesh@coralbricks.ai",
    description="A Python library for building conversational AI systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/coralbricks/builder",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "requests>=2.25.0",
        "pydantic>=1.8.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "pyright>=1.1.0",
        ],
    },
) 