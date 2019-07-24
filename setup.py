import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytest-fixture-tools",
    version="0.0.1",
    author="Ben Slakey",
    author_email="benjaminslakey@gmail.com",
    description="A few tools for creating and using fixtures to mock out functions in pytest",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Benjaminslakey/pytest_fixture_tools",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 2.7",
        "Framework :: Pytest",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
)