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
    version="1.3.4.0",
    description="Small tool to convert Narou Novels to vertically written EPUBs.",
    long_description=readme,
    author="mkomuro",
    author_email="16011714+mkomuro@users.noreply.github.com",
    url="https://github.com/mkomuro/nepub",
    license=license,
    install_requires=install_requires,
    packages=find_packages(exclude=("test",)),
    package_data={"": ["files/*", "templates/*"]},
    entry_points=entry_points,
)
