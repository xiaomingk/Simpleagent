from setuptools import setup

setup(
    name='Agent',
    version='0.0.7',
    description='My agent based model package',
    url='https://github.com/xiaomingk/Simpleagent.it',
    author='Xiaoming Kan',
    author_email='kanx@chalmers.se',
    license='unlicense',
    packages=['Agent'],
    zip_safe=False,
    package_data={'Agent': ['abm_data.xlsx']}
)