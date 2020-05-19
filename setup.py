#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages
import versioneer

descr = """
The ``pyPM.ca`` population modeller (www.pyPM.ca) describes connected systems with
discrete-time difference equations. It was developed specifically
to understand and characterize the CoViD-19 epidemic. 

This package, ipypm, is a convenient graphical user interface (GUI) for
pyPM.ca based in interactive python widgets for use inside a Jupyter notebook.
After opening the GUI in a notebook, the user can open a pyPM.ca model
and compare its predictions with data.
Models and data can be accessed on the local filesystem or downloaded
from a network server.
The model parameters can be adjusted manually or by fitting to data.
Models can be examined in detail and modified through the GUI, without
programming.
"""

requirements = ['pypmca', 'scipy', 'numpy', 'ipywidgets', 'texttable', 'matplotlib',
                'requests', 'pandas']

setup_requirements = ['pytest-runner', ] + requirements

test_requirements = ['pytest>=3', ] + requirements

setup(author="Dean Karlen",
      author_email='karlen@uvic.ca',
      python_requires='>=3.5',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Natural Language :: English',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
      ],
      description="GUI for pyPM.ca Population Modeler",
      install_requires=requirements,
      license="GNU General Public License v3",
      long_description=descr,
      include_package_data=True,
      keywords='ipypm',
      name='ipypm',
      packages=find_packages(include=['ipypm', 'ipypm.*']),
      setup_requires=setup_requirements,
      test_suite='tests',
      tests_require=test_requirements,
      url='http://www.pypm.ca',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      zip_safe=False,
      )
