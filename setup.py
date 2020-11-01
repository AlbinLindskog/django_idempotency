from distutils.core import setup

setup(
    name='Django idempotency',
    version='0.0.1',
    description='TIdempotency middleware for Django',
    long_description=open('README.rst').read(),
    install_requires=[
        'django-redis>=4.2.0'
    ],
    packages=['django_idempotency'],
    author='Albin Lindskog',
    author_email='albin@zerebra.com',
    url='https://github.com/albinlindskog/django_idempotency',
    zip_safe=True,
)
