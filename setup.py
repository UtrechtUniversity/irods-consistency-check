from setuptools import setup

setup(
    author="Paul Frederiks, Lazlo Westerhof, Sietse Snel, Chris Smeele",
    author_email="p.frederiks@uu.nl, l.r.westerhof@uu.nl, s.t.snel@uu.nl, c.j.smeele@uu.nl",
    description=('Check consistency of iRODS database and vault'),
    install_requires=[
        'python-irodsclient >= 1.1.0',
        'six'
    ],
    name='ichk',
    packages=['ichk', 'irodsutils'],
    entry_points={
        'console_scripts': [
            'ichk = ichk.command:entry'
        ]
    },
    version='2.0.0'
)
