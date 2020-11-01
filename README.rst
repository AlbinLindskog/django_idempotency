Django Idempotency
------------------
Opt-in idempotency middleware for Django that correctly handles concurrent
requests without causing a cache stampede or resorting to responding HTTP 423
until the first request has been processed.

Based on distributed locks with Redis, and as such, requires that Redis is used
as cache-backend.

To activate django_idempotency middleware, add it to the MIDDLEWARE list in
your Django settings, and configure the 'idempotency' cache-backend::

    MIDDLEWARE = [
        ...
        'django_idempotency.IdempotencyMiddleware',
    ]

    CACHES = {
        ...
        'idempotency': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
            'OPTIONS': {
                'IGNORE_EXCEPTIONS': False,  # If the cache is down: raise an error, idempotency shouldn't fail silently
            }
        },
    }

To make an idempotent request, simply include the ´Idempotency-Key´-header
in your request. The response will be cached and subsequent requests with the
same header will simply prompt the cached response.

Safe methods, ('GET', 'HEAD', 'OPTIONS', 'TRACE', 'DELETE', 'PUT'), are not
cached by default, even if a  ´Idempotency-Key´-header is included in the
request.

Middleware attributes
^^^^^^^^^^^^^^^^^^^^^
It is possible to customize the behavior somewhat by subclassing
IdempotencyMiddleware and overriding the settings.

safe_methods:
    HTTP request methods that are considered safe, and are as such not
    cached by default.

cache_safe_methods:
    Whether to cache request with a safe method. The default is False.

header_name:
    The header used to identify idempotent requests.
    Default: 'IDEMPOTENCY_KEY'.

cache_name:
    Name of the cache used. Defaults to 'idempotency', Must be an instance
    of django_redis.cache.RedisCache.

timeout:
    The duration for which a cached response is saved. The default is 86400,
    24 hours.

get_cache_key():
    The method responsible for generating a key used to identify each request.
    The default implementation takes the path, method, user id, the provided
    idempotency header into account.

Django Rest Framework
^^^^^^^^^^^^^^^^^^^^^
Django Rest Framework uses it's own authentication framework, and request.user
is not sent yet when the request is passing through the middleware-layer.
get_cache_key() will thus not generate keys that are unique per user, if this
is important in your application you need to extend IdempotencyMiddleware and
implement a version of get_cache_key that uses some other identifer that is
unique per user.

Development
^^^^^^^^^^^
To run the tests; clone the repository, setup the virtual environment, and run
the tests.::

    # Setup the virtual environment
    $ virtualenv test_env
    $ source test_env/bin/activate
    $ pip3 install -r test_requirements.txt

    # Update the settings to point to a running Redis instance
    $ vi tests/settings.py

    # Run the tests
    $ cd tests
    $ python3 manage.py test
