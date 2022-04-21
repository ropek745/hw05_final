from http import HTTPStatus
from django.test import TestCase, Client


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    # Проверка доступности адресов

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/."""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_tech_url_exists_at_desired_location(self):
        """Проверка доступности адреса /tech/."""
        self.assertEqual(
            self.guest_client.get('/about/tech/').status_code,
            HTTPStatus.OK
        )

    # Проверка доступности шаблонов

    def test_url_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        template_url_names = {
            '/about/author/': 'about/about.html',
            '/about/tech/': 'about/tech.html',
        }

        for address, template in template_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
