from setuptools import setup, find_packages

def read_requirements():
    with open("requirements.txt") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="finance",
    version="0.5.1", 
    packages=find_packages(),
    install_requires=read_requirements(),
    author="ninja-con-gafas",
    description="The repository features a collection of modules to assist with managing and processing financial data.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ninja-con-gafas/finance",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
)
