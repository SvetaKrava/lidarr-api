from setuptools import setup, find_packages

setup(
    name="lidarr-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    author="jdrunyan",
    description="A Python library for interacting with the Lidarr API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jdrunyan/lidarr-api",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
