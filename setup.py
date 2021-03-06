from setuptools import setup

setup(
    name='Agent',
    version='0.0.8',
    description='My agent based model package',
    url='https://github.com/xiaomingk/Simpleagent.it',
    author='Xiaoming Kan',
    author_email='kanx@chalmers.se',
    license='unlicense',
    packages=['Agent'],
    zip_safe=False,
    include_package_data=True,
    package_data={'Agent': ['abm_data.xlsx']}
)