from setuptools import setup

setup(
    author="Paul Frederiks, Lazlo Westerhof, Sietse Snel, Chris Smeele",
    author_email="p.frederiks@uu.nl, l.r.westerhof@uu.nl, s.t.snel@uu.nl, c.j.smeele@uu.nl",
    description=('Check consistency of iRODS database and vault'),
    install_requires=[
        'python-irodsclient == 2.2.0',
        'boto3 == 1.23.10'
    ],
    name='ichk',
    packages=['ichk'],
    entry_points={
        'console_scripts': [
            'ichk = ichk.command:entry'
        ]
    },
    version='3.0.0'
)
