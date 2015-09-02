from setuptools import setup

setup(
    name='regularbus',
    packages=['regularbus', 'regularbus.pycallgraph', 'regularbus.pycoverage'],
    version='0.2',
    install_requires=[
        "flask>=0.10.1",
        "twisted>=15.2.1",
        "autobahn>=0.10.4",
        "coverage==3.7.1"
    ],
    description='python coverage test tool',
    author='ting wu',
    author_email='ting.wu@corp.netease.com',
    url='',
    download_url='',
    keywords=['testing', 'coverage'],
    classifiers=[],
)
