from setuptools import setup, find_packages


setup(
    name="shinewave_webapp",
    version="1.0",
    packages=find_packages(include=['shinewave_webapp', 'shinewave_webapp.*']),
)
