from setuptools import setup, find_packages

setup(
    name="lidarr-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "typing-extensions>=4.0.0",  # For Python <3.8 compatibility
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-mock>=3.10.0',
            'responses>=0.23.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'lidarr-search=examples.search_artist:main',
        ],
    },
    author="jdrunyan",
    description="A Python library for interacting with the Lidarr API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jdrunyan/lidarr-api",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
)
