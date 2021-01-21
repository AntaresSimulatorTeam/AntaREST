import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="storage-api",
    version="0.0.1",
    description="Storage API for antares",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AntaresSimulatorTeam/api-iso-antares",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Apache License :: 2.0",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
