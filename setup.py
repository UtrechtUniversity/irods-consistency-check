from setuptools import setup

setup(
   author="Paul Frederiks",
   author_email="p.frederiks@uu.nl",
   description=('Check consistency of irods database and vault'),
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
   version='0.2.3'
)
