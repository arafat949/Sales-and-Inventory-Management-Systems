from django.test import TestCase
from django.urls import reverse

from .models import User


class AuthenticationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('testadmin', password='pass12345', role='ADMIN')
        self.employee = User.objects.create_user('testemp', password='pass12345', role='EMPLOYEE')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testadmin', 'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('dashboard:index'))

    def test_invalid_login_shows_error(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testadmin', 'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_employee_cannot_access_user_management(self):
        self.client.login(username='testemp', password='pass12345')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_user_management(self):
        self.client.login(username='testadmin', password='pass12345')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)

    def test_password_change(self):
        self.client.login(username='testadmin', password='pass12345')
        response = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'pass12345',
            'new_password1': 'newpass98765',
            'new_password2': 'newpass98765',
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('newpass98765'))
