import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as fh:
    requirements = fh.read()

setuptools.setup(
    name='notificator_yandprakt_middle_python',
    version='0.0.5',
    author='Roman Volodin',
    author_email='rozarioagro@gmail.com',
    description='Notificator for inner ussage',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/RomanAVolodin/notificator_middle_python',
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
