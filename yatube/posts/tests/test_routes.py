from django.test import TestCase
from django.urls import reverse

from ..urls import app_name

ID = 5
USERNAME = 'Roman'
SLUG = 'test-slug'

CASES = [
    ['/', 'index', []],
    [f'/group/{SLUG}/', 'posts_slug', [SLUG]],
    ['/create/', 'post_create', []],
    [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
    [f'/posts/{ID}/', 'post_detail', [ID]],
    [f'/posts/{ID}/edit/', 'post_edit', [ID]],
    ['/follow/', 'follow_index', []],
    [f'/profile/{USERNAME}/follow/', 'profile_follow', [USERNAME]],
    [f'/profile/{USERNAME}/unfollow/', 'profile_unfollow', [USERNAME]],
    [f'/posts/{ID}/comment/', 'add_comment', [ID]]
]


class TestRoutes(TestCase):
    def test_routes(self):
        for url, route, args in CASES:
            with self.subTest(url=url, route=route, args=args):
                self.assertEqual(
                    url,
                    reverse(f'{app_name}:{route}', args=args)
                )
