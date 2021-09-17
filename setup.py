import os
import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()
with open(os.path.join('rlq', 'VERSION'), 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name='rlq',
    version=version,
    author='Parth Joshi',
    author_email='parthjoshi.iitm@gmail.com',
    license='GNU GPL v3',
    packages=setuptools.find_packages(),
    description='A wrapper around Arelle to query XBRL instances using SQL-like queries',
    long_description_content_type='text/markdown',
    long_description=long_description,
    url='https://github.com/parthjoshi2007/rlq',
    # dependency_links=['git+https://github.com/Arelle/Arelle.git#egg=Arelle-1.0.0'],
    install_requires=['arelle'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3'
    ]
)
