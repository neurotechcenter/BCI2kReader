from setuptools import setup

setup(
    name='BCI2kReader',
    version='0.31dev0',
    packages=['BCI2kReader',],
    license='GNU 3',
    author='Markus Adamek',
    url='https://github.com/markusadamek/BCI2kReader',
    author_email='markus.adamek@gmail.com',
    install_requires=['numpy', ],
    long_description=open('README.md').read(),
    classifiers=["Development Status :: 3 - Alpha",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 2"],
)