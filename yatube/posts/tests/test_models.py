from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment, Follow

User = get_user_model()

USERNAME_1 = 'Roman'
USERNAME_2 = 'Pekarev'

class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME_1)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текстовая пост',
        )
        cls.author = User.objects.create_user(username=USERNAME_2)
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.user
        )
    def test_models_have_correct_object_names(self):
        '''Проверяем, что у моделей корректно работает __str__.'''
        self.assertEqual(self.group.title, str(self.group))
        self.assertEqual(self.post.text[:15], str(self.post))


