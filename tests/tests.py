from time import sleep
from threading import Thread

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import TestCase, RequestFactory

from django_idempotency import IdempotencyMiddleware
from django_redis import get_redis_connection


def get_response(request):
    """
    Stand-in for a middleware wrapped view.
    """
    sleep(1)  # Not elegant, but it emulates the time it takes to process the view. Long enough for a thread-switch to occur.
    return HttpResponse(request.POST['test_data'])


class IdempotencyMiddlewareTestCase(TestCase):

    def setUp(self):
        self.middleware = IdempotencyMiddleware(get_response=get_response)

    def tearDown(self):
        get_redis_connection('idempotency').flushall()

    def request(self, data, key):
        request = RequestFactory().post('/idempotency/', {'test_data': data})
        request.user = AnonymousUser()
        request.META['HTTP_IDEMPOTENCY_KEY'] = key
        return request

    def test_get_cache_key_anonomous_user(self):
        """Should still work with anonymous users."""
        request = self.request(1, '12')

        key = self.middleware.get_cache_key(request)
        self.assertEqual(key, 'a45e620e853d4718e6ac854b36da7adacd6534ad9f9a1149027379a543a107b0')

    def test_locking(self):
        """
        If there are two concurrent requests, the first should apply the lock,
        the second should wait for the lock and the respond with the first
        requests cached response.

        In this setup we should that the two responses are the same, despite
        the different requests since the second will be cached.
        """
        responses = []

        def test(request, _responses):
            response = self.middleware(request)
            _responses.append(response)
            return response

        request_1 = self.request(1, '20')
        request_2 = self.request(2, '20')

        threads = [
            Thread(target=test, args=(request_1, responses)),
            Thread(target=test, args=(request_2, responses)),
        ]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(responses[0].content, responses[1].content)

    def test_non_blocking(self):
        """
        Requests with different keys should not block each other.
        """
        responses = []

        def test(request, _responses):
            response = self.middleware(request)
            _responses.append(response)
            return response

        request_1 = self.request(1, '21')
        request_2 = self.request(2, '22')

        threads = [
            Thread(target=test, args=(request_1, responses)),
            Thread(target=test, args=(request_2, responses)),
        ]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertNotEqual(responses[0].content, responses[1].content)