from django.test import TestCase
from django.urls import reverse

ID = 5
USERNAME = 'Roman'
SLUG = 'test-slug'

ROUTES = [
    ['/', 'index', []],
    [f'/group/{SLUG}/', 'posts_slug', [SLUG]],
    ['/create/', 'post_create', []],
    [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
    [f'/posts/{ID}/', 'post_detail', [ID]],
    [f'/posts/{ID}/edit/', 'post_edit', [ID]],
]


class TestRoutes(TestCase):
    def test_routes(self):
        for url, route, args in ROUTES:
            with self.subTest(url=url, route=route, args=args):
                self.assertEqual(url, reverse(f'posts:{route}', args=args))
