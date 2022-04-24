import shutil
import tempfile

from django.core.cache import cache
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from yatube.settings import PAGINATOR_COUNT
from posts.models import Group, Post, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
GROUP_DESCRIPTION = 'Тестовое описание'
GROUP_TITLE_NEW = 'Группа-2'
GROUP_SLUG_NEW = 'test-2'
GROUP_DESCRIPTION_NEW = 'новая группа'
POST_TEXT = 'I love django tests'
USERNAME = 'Roma'
AUTHOR = 'Pekarev'

INDEX_FOLLOW = reverse('posts:follow_index')
FOLLOW = reverse('posts:profile_follow', args=[USERNAME])
UNFOLLOW = reverse('posts:profile_unfollow', args=[USERNAME])

INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:posts_slug', args=[GROUP_SLUG])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
GROUP_LIST_URL_2 = reverse('posts:posts_slug', args=[GROUP_SLUG_NEW])
OTHER_PAGES = 4
NEXT_PAGE = '?page=2'

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
uploaded = SimpleUploadedFile(
    name='small.gif',
    content=small_gif,
    content_type='image/gif'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.following = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.group_2 = Group.objects.create(
            title=GROUP_TITLE_NEW,
            slug=GROUP_SLUG_NEW,
            description=GROUP_DESCRIPTION_NEW
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            group=cls.group,
            image=uploaded
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.author = Client()
        cls.author.force_login(cls.following)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.following
        )


    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_post_context(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.image, self.post.image)

    def test_show_correct_context(self):
        urls = [
            INDEX_URL,
            GROUP_LIST_URL,
            PROFILE_URL,
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.author.get(url)
                if 'page_obj' in response.context:
                    self.assertEqual(len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
                    self.check_post_context(post)


    def test_detail_page_show_correct(self):
        response = self.authorized_client.get(self.POST_DETAIL_URL)
        self.check_post_context(response.context['post'])

    def test_profile_show_correct_context(self):
        response = self.authorized_client.get(PROFILE_URL)
        self.assertEqual(self.user, response.context['author'])

    def test_group_list_show_correct_context(self):
        response = self.authorized_client.get(GROUP_LIST_URL)
        self.assertEqual(self.group, response.context['group'])
        self.assertEqual(self.group.title, GROUP_TITLE)
        self.assertEqual(self.group.slug, GROUP_SLUG)
        self.assertEqual(self.group.description, GROUP_DESCRIPTION)

    # Тесты подписок

    def test_post_following_author(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто не подписан на него.
        """
        response = self.authorized_client.get(INDEX_FOLLOW)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_authorized_follow(self):
        """Проверка возможности подписаться авторизованному пользователю
           на других пользователей.
        """
        self.author.get(FOLLOW)
        follow = Follow.objects.filter(user=self.following, author=self.user)
        self.assertTrue(follow.exists())

    def test_unfollow(self):
        self.authorized_client.get(UNFOLLOW)
        follow = Follow.objects.filter(user=self.following, author=self.user)
        self.assertFalse(follow.exists())

    def test_new_post_in_another_group(self):
        """Наличие поста в другой группе"""
        self.assertNotIn(
            self.post,
            self.authorized_client.get(GROUP_LIST_URL_2).context['page_obj'])

    class PaginatorViewsTest(TestCase):
        @classmethod
        def setUpClass(cls) -> None:
            super().setUpClass()
            # Создадим запись в БД
            cls.user = User.objects.create_user(username=USERNAME)
            cls.group = Group.objects.create(
                title=GROUP_TITLE,
                slug=GROUP_SLUG,
                description=GROUP_DESCRIPTION,
            )
            Post.objects.bulk_create(
                Post(
                    text=f'Post {i}',
                    author=cls.user,
                    group=cls.group,
                    image=uploaded)
                for i in range(PAGINATOR_COUNT + OTHER_PAGES)
            )

        def setUp(self) -> None:
            self.authorized_client = Client()
            self.authorized_client.force_login(self.user)

        def test_paginator_on_pages_have_ten_post(self):
            '''Количество постов на страницах не больше 10 штук.'''
            urls = [
                [INDEX_URL, PAGINATOR_COUNT],
                [GROUP_LIST_URL, PAGINATOR_COUNT],
                [PROFILE_URL, PAGINATOR_COUNT]
                [INDEX_URL + NEXT_PAGE, OTHER_PAGES],
                [GROUP_LIST_URL + NEXT_PAGE, OTHER_PAGES],
                [PROFILE_URL + NEXT_PAGE, OTHER_PAGES]
            ]
            for url, page_count in urls:
                with self.subTest(url=url):
                    response = self.client.get(url)
                    self.assertEqual(
                        len(response.context['page_obj'], page_count)
                    )

        def test_cache_index_page(self):
            """Тест работы кеша"""
            response_1 = self.authorized_client.get(INDEX_URL).content
            Post.objects.all().delete()
            response_2 = self.authorized_client.get(INDEX_URL).content
            self.assertEqual(response_1, response_2)
            cache.clear()
            self.assertNotEqual(response_1, response_2)
