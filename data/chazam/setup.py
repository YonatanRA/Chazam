from setuptools import setup, find_packages


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


setup(
    name='Chazam',
    version='0.1',
    description='Chazam: Audio Fingerprinting in Python',
    long_description='''
                        Audio fingerprinting and recognition algorithm implemented in Python

                        Chazam can memorize recorded audio by listening to it once and fingerprinting 
                        it. Then by playing a song and recording microphone input or on disk file, 
                        Chazam attempts to match the audio against the fingerprints held in the 
                        database, returning the song or recording being played.
                        ''',
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
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='python, audio, fingerprinting, music, numpy, landmark',
)
