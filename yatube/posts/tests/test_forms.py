import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment
from ..urls import app_name

IMAGE_GIF_1 = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
IMAGE_GIF_2 = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3A'
)
IMAGE_NAME = 'small.gif'
IMAGE_NAME_2 = 'small_2.jpg'
IMAGE_TYPE_1 = 'image/gif'
IMAGE_TYPE_2 = 'gif/image'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
GROUP_DESCRIPTION = 'Тестовое описание'
LOGIN = reverse('users:login')

GROUP_TITLE_NEW = 'Новая тестовая группа'
GROUP_SLUG_NEW = 'test-slug-new'
GROUP_DESCRIPTION_NEW = 'Новое тестовое описание'
USERNAME = 'Roman'

COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT = 'Yes'

CREATE_URL = reverse('posts:post_create')
CREATE_REDIRECT = f'{LOGIN}?next={CREATE_URL}'
PROFILE_URL = reverse('posts:profile', args=[USERNAME])

POST_TEXT = 'Текстовая пост'
NEW_POST_TEXT = 'Новый текст'

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.test = User.objects.create_user(username='Assan')
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.group_new = Group.objects.create(
            title=GROUP_TITLE_NEW,
            slug=GROUP_SLUG_NEW,
            description=GROUP_DESCRIPTION_NEW
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            group=cls.group
        )
        cls.COMMENT = reverse(
            'posts:add_comment', kwargs={'post_id': cls.post.id}
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.EDIT_REDIRECT = f'{LOGIN}?next={cls.POST_EDIT_URL}'
        cls.COMMENT_REDIRECT = f'{LOGIN}?next={cls.COMMENT}'
        cls.anomymus = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.test)
        cls.image = SimpleUploadedFile(
            name=IMAGE_NAME,
            content=IMAGE_GIF_1,
            content_type=IMAGE_TYPE_1,
        )
        cls.image_2 = SimpleUploadedFile(
            name=IMAGE_NAME_2,
            content=IMAGE_GIF_2,
            content_type=IMAGE_TYPE_2,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        Post.objects.all().delete()
        image_test = SimpleUploadedFile(
            name=IMAGE_NAME,
            content=IMAGE_GIF_1,
            content_type=IMAGE_TYPE_1,
        )
        form_data = {
            'text': POST_TEXT,
            'group': self.group.id,
            'image': image_test
        }
        response = self.authorized_client.post(
            CREATE_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.get()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image.name, f"{app_name}/{form_data['image'].name}")
        self.assertRedirects(response, PROFILE_URL)

    def test_post_edit(self):
        form_data = {
            'text': NEW_POST_TEXT,
            'group': self.group_new.id,
            'image': self.image_2
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        post = response.context.get('post')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image.name, f"{app_name}/{form_data['image'].name}")
        self.assertRedirects(response, self.POST_DETAIL_URL)

    def test_form_create_and_edit_post_is_valid(self):
        urls = [
            CREATE_URL,
            self.POST_EDIT_URL
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for url in urls:
            response = self.authorized_client.get(url)
            for value, expected_value in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected_value)

    def test_comment_form(self):
        Comment.objects.all().delete()
        form_data = {
            'text': COMMENT_TEXT,
        }
        response = self.authorized_client.post(
            self.COMMENT,
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertRedirects(response, self.POST_DETAIL_URL)

    def test_add_comments_show_correct_context(self):
        response = self.authorized_client.get(self.POST_DETAIL_URL)
        form_fields = {
            'text': forms.fields.CharField,
        }

        for field, expected_value in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected_value)

    def test_guest_create_comment(self):
        """Анонимный пользователь не может оставлять комментарии."""
        Comment.objects.all().delete()
        form_data = {
            'text': NEW_COMMENT,
        }
        response = self.anomymus.post(
            self.COMMENT,
            data=form_data
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(
            response,
            self.COMMENT_REDIRECT
        )

    def test_anonymus_not_create_post(self):
        """Попытка анонима создать post."""
        Post.objects.all().delete()
        form_data = {
            'text': POST_TEXT,
            'group': self.group.id,
            'image': self.image
        }
        response = self.anomymus.post(
            CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 0)
        self.assertRedirects(response, CREATE_REDIRECT)

    def test_anonymus_edit_post(self):
        users_urls_list = [
            [self.anomymus, self.EDIT_REDIRECT],
            [self.another, self.POST_DETAIL_URL],
        ]
        image = SimpleUploadedFile(
            name=IMAGE_NAME_2,
            content=IMAGE_GIF_2,
            content_type=IMAGE_TYPE_2,
        )
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group_new.id,
            'image': image,
        }
        for client, url in users_urls_list:
            with self.subTest(user=client, url=url):
                response = client.post(
                    self.POST_EDIT_URL,
                    data=form_data,
                    follow=True
                )
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.group, post.group)
                self.assertEqual(self.post.author, post.author)
                self.assertRedirects(response, url)
