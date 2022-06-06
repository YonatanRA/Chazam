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
