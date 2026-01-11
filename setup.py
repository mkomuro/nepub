from setuptools import find_packages, setup

with open("requirements.txt", encoding="utf-8") as f:
    install_requires = f.read()

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

with open("LICENSE", encoding="utf-8") as f:
    license = f.read()

entry_points = {"console_scripts": ["nepub = nepub.__main__:main"]}

setup(
    name="nepub",
    version="1.4.1",
    description="Small tool to convert Narou and Kakuyomu novels to vertically written EPUBs.",
    long_description=readme,
    author="tama@ttk1.net",
    author_email="tama@ttk1.net",
    url="https://github.com/ttk1/nepub",
    license=license,
    install_requires=install_requires,
    packages=find_packages(exclude=("test",)),
    package_data={"": ["files/*", "templates/*"]},
    entry_points=entry_points,
)
