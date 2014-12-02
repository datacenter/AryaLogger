import os
from setuptools import setup, find_packages

with open('LICENSE.txt') as f:
    license = f.read()

exec(open(os.path.join('arya', 'version.py')).read())


PKGNAME = 'AryaLogger'
URL = 'https://github.com/datacenter/ACI/' + '/' + PKGNAME
DOWNLOADURL = URL + '/releases/tag/' + str(__version__)

setup(
    name=PKGNAME,
    version=__version__,
    description='Use the SimpleAciUiLogServer and arya to convert UI REST ' +
                'API calls to ACI Python SDK code.',
    long_description=open('README.rst').read(),
    packages=find_packages(),
    url='https://github.com/datacenter/AryaLogger',
    download_url=DOWNLOADURL,
    license=license,
    author='Mike Timm',
    author_email='mtimm@cisco.com',
    zip_safe=False,
    install_requires=[
        'SimpleAciUiLogServer',
        'acicobra',
        'arya'
    ],
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ),
    scripts=[os.path.join('AryaLogger', 'AryaLogger.py')],
    entry_points={
        "console_scripts": [
            "aryalogger=AryaLogger:main",
            "AryaLogger=AryaLogger:main",
        ],
    },
)
