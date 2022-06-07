from setuptools import find_packages, setup


def parse_requirements(requirements):
    # carga el archivo requirements.txt
    with open(requirements) as file:
        lines = [line for line in file]
        # quita espacios
        stripped = list(map((lambda x: x.strip()), lines))
        # quita comentarios
        nocomments = list(filter((lambda x: not x.startswith('#')), stripped))
        # quita lineas en blanco
        reqs = list(filter((lambda x: x), nocomments))
        return reqs


if __name__ == '__main__':
    # setup de instalacion
    setup(
        name='Chazam',
        version='0.1.2',
        description='Chazam: Audio Fingerprinting in Python',
        long_description='',
        author='',
        author_email='',
        maintainer='',
        maintainer_email='',
        url='',
        license='MIT License',
        include_package_data=True,
        packages=find_packages(),
        platforms=['Unix'],
        install_requires=parse_requirements('requirements.txt'),

    )
<<<<<<< HEAD
=======
=======
from setuptools import setup, find_packages
# import os, sys


def parse_requirements(requirements):
    # load from requirements.txt
    with open(requirements) as f:
        lines = [l for l in f]
        # remove spaces
        stripped = map((lambda x: x.strip()), lines)
        # remove comments
        nocomments = filter((lambda x: not x.startswith('#')), stripped)
        # remove empty lines
        reqs = filter((lambda x: x), nocomments)
        return reqs

PACKAGE_NAME = 'Chazam'
PACKAGE_VERSION = '0.1'
SUMMARY = 'Chazam: Audio Fingerprinting in Python'
DESCRIPTION = """
Audio fingerprinting and recognition algorithm implemented in Python

See the explanation here: 

`http://willdrevo.com/fingerprinting-and-audio-recognition-with-python/`__

Chazam can memorize recorded audio by listening to it once and fingerprinting 
it. Then by playing a song and recording microphone input or on disk file, 
Chazam attempts to match the audio against the fingerprints held in the 
database, returning the song or recording being played.

__ http://willdrevo.com/fingerprinting-and-audio-recognition-with-python/
"""
REQUIREMENTS = parse_requirements('requirements.txt')

setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,
    description=SUMMARY,
    long_description=DESCRIPTION,
    author='',
    author_email='',
    maintainer='',
    maintainer_email='',
    url='',
    license='MIT License',
    include_package_data=True,
    packages=find_packages(),
    platforms=['Unix'],
    install_requires=REQUIREMENTS,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords="python, audio, fingerprinting, music, numpy, landmark",
)
>>>>>>> b1c312b (libreria chazam)
>>>>>>> n
