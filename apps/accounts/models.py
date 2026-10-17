from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ADMIN = 'admin', 'Admin'

    avatar = models.ImageField(upload_to='avatars/', blank=True)
    bio = models.TextField('short description', max_length=500, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    @property
    def is_super_admin(self):
        return self.is_superuser

    @property
    def is_admin(self):
        return self.is_superuser or self.role == 'admin'

    def can_ban(self, target):
        if not self.is_admin:
            return False
        if target == self:
            return False
        if target.is_superuser:
            return False
        if target.is_admin:
            return self.is_superuser
        return True

    def can_change_role(self, target):
        if not self.is_superuser:
            return False
        if target == self or target.is_superuser:
            return False
        return True

    def ban(self):
        self.is_banned = True
        self.role = 'user'  # admin loses role
        self.save()

    def unban(self):
        self.is_banned = False
        self.save()

    def set_role(self, role):
        self.role = role
        self.save()

