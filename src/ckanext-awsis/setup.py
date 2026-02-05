from setuptools import setup, find_namespace_packages

setup(
    name='ckanext-awsis',
    version='1.0.0',
    description='AWSIS (Akvo Water Security Information System) theme for CKAN',
    long_description='A sophisticated CKAN theme extension for the AWSIS project focusing on water management in the Sundarbans region.',
    author='Akvo',
    author_email='tech.consultancy@akvo.org',
    license='AGPL-3.0',
    url='https://github.com/akvo/awsis-ckan',
    packages=find_namespace_packages(include=['ckanext.*']),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'ckan.plugins': [
            'awsis=ckanext.awsis.plugin:AwsisPlugin',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
