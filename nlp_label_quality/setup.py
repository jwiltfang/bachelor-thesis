from setuptools import setup

setup(
    name='nlp_label_quality',
    version='0.0.1',
    packages=['nlp_label_quality'],
    include_package_data=True,
    install_requires=[
        'pandas>=1.2.3',
        'pm4py>=2.2.1',
        'numpy>=1.20.1',
        'spacy>=2.3.2',
    ],
    license='',
    author='Jasper Wiltfang',
    author_email='jasper.wiltfang@uni-bayreuth.de',
    description='Module to improve log quality through repairing distorted and synoymous labels interactively',
)
