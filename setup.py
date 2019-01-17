import os

from setuptools import setup, find_packages
from viber.version import __version__


def requirements():
    """Build the requirements list for this project"""
    requirements_list = []

    with open('requirements.txt') as requirements:
        for install in requirements:
            requirements_list.append(install.strip())

    return requirements_list


packages = find_packages(exclude=['tests*'])

fn = os.path.join('viber', 'version.py')
with open(fn) as fh:
    code = compile(fh.read(), fn, 'exec')
    exec(code)

setup(name='python-viber-bot',
      version=__version__,
      author='Flowelcat',
      author_email='Flowelcat@gmail.com',
      license='LGPLv3',
      keywords='python viber bot api wrapper',
      description="I have made you a wrapper you can't refuse",
      # long_description=fd.read(),
      packages=packages,
      install_requires=requirements(),
      # extras_require={
      #     'json': 'ujson',
      #     'socks': 'PySocks'
      # },
      include_package_data=True,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
          'Operating System :: OS Independent',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Communications :: Chat',
          'Topic :: Internet',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7'
      ], )
