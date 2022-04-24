import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment

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

CREATE_URL = reverse('posts:post_create')
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
        cls.anomymus = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
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
        form_data = {
            'text': POST_TEXT,
            'group': self.group.id,
            'image': self.image
        }
        response = self.authorized_client.post(
            CREATE_URL,
            data=form_data,
        )
        post = Post.objects.get()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image.name, f"posts/{form_data['image'].name}")
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(Post.objects.count(), 1)

    def test_post_edit(self):
        # Создаём форму
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
        self.assertEqual(post.image.name, f"posts/{form_data['image'].name}")
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
        comment = Comment.objects.all()[0]
        self.assertEqual(form_data['text'], (form_data['text']))
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

    def test_anonymus_not_create_comment(self):
        """Попытка анонима создать комментарий."""
        Comment.objects.all().delete()
        response = self.anomymus.get(self.COMMENT)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.exists())
    
    def test_anonymus_not_create_post(self):
        """Попытка анонима создать post."""
        Post.objects.all().delete()
        response = self.anomymus.get(CREATE_URL)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.exists())

    def test_anonymus_edit_post(self):
        form_data = {
            'text': NEW_POST_TEXT,
            'group': self.group_new.id,
        }
        response = self.anomymus.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        post = Post.objects.get()
        self.assertRedirects(response, self.EDIT_REDIRECT)
        self.assertNotEqual(post.text, form_data['text'])
        self.assertNotEqual(post.group.id, form_data['group'])
    