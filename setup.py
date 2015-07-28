from setuptools import setup

setup(
    name='regularbus',
    packages=['regularbus'],
    version='0.2',
    install_requires=[
        "flask",
        "twisted",
        "autobahn",
        "coverage"
    ],
    description='python coverage test tool',
    author='ting wu',
    author_email='ting.wu@corp.netease.com',
    url='',
    download_url='',
    keywords=['testing', 'coverage'],
    classifiers=[],
)
