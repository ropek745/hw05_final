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
FOLLOWER = 'Pekarev'

INDEX_FOLLOW = reverse('posts:follow_index')
FOLLOW = reverse('posts:profile_follow', args=[USERNAME])
UNFOLLOW = reverse('posts:profile_unfollow', args=[USERNAME])

INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:posts_slug', args=[GROUP_SLUG])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
GROUP_LIST_URL_2 = reverse('posts:posts_slug', args=[GROUP_SLUG_NEW])
OTHER_PAGES = 4
NEXT_PAGE = '?page=2'

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
UPLOADED = SimpleUploadedFile(
    name='small.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
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
            image=UPLOADED
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])

        cls.follower = User.objects.create(username=FOLLOWER)
        cls.guest = Client()
        cls.authorized = Client()
        cls.authorized.force_login(cls.user)
        cls.follow = Client()
        cls.follow.force_login(cls.follower)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_show_correct_context(self):
        Follow.objects.create(user=self.follower, author=self.user)
        urls = [
            INDEX_URL,
            GROUP_LIST_URL,
            PROFILE_URL,
            self.POST_DETAIL_URL,
            INDEX_FOLLOW
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.follow.get(url)
                with self.subTest(url=url):
                    if 'page_obj' in response.context:
                        self.assertEqual(len(response.context['page_obj']), 1)
                        post = response.context['page_obj'][0]
                    else:
                        post = response.context['post']
                    self.assertEqual(post.text, self.post.text)
                    self.assertEqual(post.group, self.post.group)
                    self.assertEqual(post.author, self.post.author)
                    self.assertEqual(post.id, self.post.id)
                    self.assertEqual(post.image, self.post.image)

    def test_profile_show_correct_context(self):
        response = self.authorized.get(PROFILE_URL)
        self.assertEqual(self.user, response.context['author'])

    def test_group_list_show_correct_context(self):
        group = self.authorized.get(GROUP_LIST_URL).context['group']
        self.assertEqual(group.id, self.group.id)
        self.assertEqual(group.title, GROUP_TITLE)
        self.assertEqual(group.slug, GROUP_SLUG)
        self.assertEqual(group.description, GROUP_DESCRIPTION)

    def test_cache_index_page(self):
        """Тест работы кеша"""
        response_1 = self.authorized.get(INDEX_URL).content
        Post.objects.all().delete()
        response_2 = self.authorized.get(INDEX_URL).content
        self.assertEqual(response_1, response_2)
        cache.clear()
        response_3 = self.authorized.get(INDEX_URL).content
        self.assertNotEqual(response_1, response_3)

    def test_post_following_author(self):
        """
        Пост не отображается в другой группе и не появляется в ленте тех,
        кто не подписан на пользователя.
        """
        urls = [
            INDEX_FOLLOW,
            GROUP_LIST_URL_2
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized.get(url)
                self.assertNotIn(self.post, response.context['page_obj'])

    def test_authorized_follow(self):
        """Проверка возможности подписаться авторизованному пользователю
           на других пользователей.
        """
        self.follow.get(FOLLOW)
        follow = Follow.objects.filter(user=self.follower, author=self.user)
        self.assertTrue(follow.exists())

    def test_unfollow(self):
        self.authorized.get(UNFOLLOW)
        follow = Follow.objects.filter(user=self.user, author=self.follower)
        self.assertFalse(follow.exists())

    def test_new_post_in_another_group(self):
        """Наличие поста в другой группе"""
        self.assertNotIn(
            self.post,
            self.authorized.get(GROUP_LIST_URL_2).context['page_obj'])


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
                image=UPLOADED)
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
            [PROFILE_URL, PAGINATOR_COUNT],
            [INDEX_URL + NEXT_PAGE, OTHER_PAGES],
            [GROUP_LIST_URL + NEXT_PAGE, OTHER_PAGES],
            [PROFILE_URL + NEXT_PAGE, OTHER_PAGES]
        ]
        for url, page_count in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), page_count
                )
