from setuptools import setup

from rggbar import __version__

setup(
    name='RGGBar',
    version=__version__,
    packages=['rggbar'],
    url='',
    license='',
    author='faststim',
    author_email='',
    description='',
    install_requires=[
        'PyQt6>=6.4.0',
        'uvicorn>=0.20.0',
        'fastapi>=0.88.0',
        'setuptools>=60.2.0',
        'websockets>=10.4',
        'websocket-client>=1.4.2'
    ]
)
