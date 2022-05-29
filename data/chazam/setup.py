from setuptools import find_packages, setup


def parse_requirements(requirements):
    # load from requirements.txt
    with open(requirements) as f:
        lines = [l for l in f]
        # remove spaces
        stripped = list(map((lambda x: x.strip()), lines))
        # remove comments
        nocomments = list(filter((lambda x: not x.startswith('#')), stripped))
        # remove empty lines
        reqs = list(filter((lambda x: x), nocomments))
        return reqs


if __name__ == '__main__':

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


