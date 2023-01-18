from setuptools import find_packages, setup

setup(
    name="PySenpai-Flask",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={"pysenpai_flask.msg_data": ["*/messages.yml"]},
    install_requires=[
        "setuptools-git",
        "flask",
        "flask-sqlalchemy",
        "pysenpai",
    ],
)
