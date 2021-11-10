import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="AntaREST",
    version="2.1.1",
    description="Antares Server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AntaresSimulatorTeam/api-iso-antares",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Apache License :: 2.0",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
