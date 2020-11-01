import hashlib

from django.core.cache import caches


class IdempotencyMiddleware:
    """
    Implements the Idempotency logic as middleware.
    """

    safe_methods = ('GET', 'HEAD', 'OPTIONS', 'TRACE', 'DELETE', 'PUT')
    cache_safe_methods = False
    header_name = 'IDEMPOTENCY_KEY'
    cache_name = 'idempotency'
    timeout = 86400  # 24 hours

    def __init__(self, get_response=None):
        self.get_response = get_response

    def get_cache_key(self, request):
        key_hash = hashlib.sha256()
        key_hash.update(request.META[f'HTTP_{self.header_name}'].encode('utf-8'))
        key_hash.update(request.path.encode('utf-8'))
        key_hash.update(request.method.encode('utf-8'))
        key_hash.update(str(getattr(request.user, 'id', '')).encode('utf-8'))
        return key_hash.hexdigest()

    def __call__(self, request):
        # Idempotency not requested, continue to view:
        if not request.META.get(f'HTTP_{self.header_name}', ''):
            return self.get_response(request)

        # If not-cached safe method, continue to view:
        if (request.method in self.safe_methods) and not self.cache_safe_methods:
            return self.get_response(request)

        # Acquire a blocking lock while we process the request:
        cache = caches[self.cache_name]
        key = self.get_cache_key(request)
        with cache.lock(f'key_{key}'):

            # Make sure the response wasn't created while we waited to acquire the lock.
            response = cache.get(key)
            if response is not None:
                return response

            # It wasn't, so lets go ahead; create it and store it.
            response = self.get_response(request)
            cache.set(key, response, self.timeout)
            response[self.header_name] = request.META[f'HTTP_{self.header_name}']
            return response
