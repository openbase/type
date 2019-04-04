import codecs
import sys
from setuptools import setup, find_packages

PROTO_SOURCES = "target/generated-sources/protobuf/python"

#with open('src/version.py') as f:
#    exec(f.read())

with codecs.open('README.md', 'r', 'utf-8') as f:
    # cut the badges from the description and also the TOC which is currently not working on PyPi
    long_description = ''.join(f.readlines())

#if len(set(('test', 'easy_install')).intersection(sys.argv)) > 0:
#    import setuptools

setup(
    name="openbase-type",
    version='1.0.0',
    description="Type lib",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Divine Threepwood',
    author_email='divine@openbase.org',
    #maintainer='',
    #maintainer_email='',
    url='https://github.com/openbase/type.git',
    #packages=find_packages(where='target/generated-sources/protobuf/python'),
    packages=find_packages('openbase_type'),
    package_data={'proto': ['data/proto/*']},
    package_dir={'':'openbase_type'},
    include_package_data=True,
    install_requires=['protobuf'],
    #extras_require=extras_require,
    #tests_require=tests_require,
    license='LGPLv3+',
    #download_url='https://github.com/xxx/%s.tar.gz' % __version__,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Home Automation",
        "Topic :: Scientific/Engineering :: Artificial Intelligence"
    ],
    #**extra_setuptools_args
)
