# Setuptools install script for ByeByeBots

import sys
major, minor = sys.version_info[0:2]
if major != 3 or minor < 7:
    print('ByeByeBots requires Python 3.7.x')
    sys.exit(1)

with open('requirements.txt') as f:
    requires = [requirement.strip() for requirement in f]

entry_points = {
    'console_scripts': [
        'byebyebots = byebyebots.byebyebots:main',
    ]
}

exec(open('byebyebots/version.py').read())

from setuptools import setup
setup(
    name='byebyebots',
    version=__version__,
    description='Unsubscribe bot-like users from the Instagram account',
    long_description=open('README.md').read(),
    author='Viktor Krasheninnikov',
    author_email='krasherspost@gmail.com',
    url='https://github.com/VikGit/byebyebots-instagram.git',
    keywords='instagram bots unsubscribe',
    packages=['byebyebots'],
    install_requires=requires,
    entry_points=entry_points,
    license=open("LICENSE").read(),
)