from setuptools import setup, find_packages

setup(
    name='teknoir_labelstudio_sdk',
    version='0.0.1',
    packages=find_packages(exclude=['examples*']),
    license='MIT',
    description='Teknoir Label Studio SDK',
    long_description=open('README.md').read(),
    install_requires=['label_studio_sdk'],
    url='https://github.com/teknoir/teknoir-labelstudio-sdk',
    author='Anders Åslund',
    author_email='anders.aslund@teknoir.ai'
)