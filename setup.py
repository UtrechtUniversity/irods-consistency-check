from setuptools import setup

setup(
    author="Paul Frederiks, Lazlo Westerhof",
    author_email="p.frederiks@uu.nl, l.r.westerhof@uu.nl",
    description=('Check consistency of iRODS database and vault'),
    install_requires=[
        'python-irodsclient',
        'enum34',
        'six'
    ],
    name='ichk',
    packages=['ichk', 'irodsutils'],
    entry_points={
        'console_scripts': [
            'ichk = ichk.command:entry'
        ]
    },
    version='0.3.1'
)
