from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import logging

logger = logging.getLogger(__name__)

class User(AbstractUser):

    email = models.EmailField(unique=True, blank=False)
    telegram_id = models.CharField(max_length=50, unique=True, blank=False)

    groups = models.ManyToManyField(
        Group,
        related_name = 'user_group', 
        blank = True,
        help_text = 'The groups this user belongs to.',
        verbose_name = 'groups'
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        related_name = 'user_permissions',
        blank = True,
        help_text = 'Specific permissions for this user.',
        verbose_name =' user permissions'
    )
    
    def save(self, *args, **kwargs):
        logger.debug('DEBUG: Saving instance of Account: %s', self.username)
        logger.info('INFO: Saving instance of Account: %s', self.username)
        logger.warning('WARNING: Saving instance of Account: %s', self.username)
        logger.error('ERROR: Saving instance of Account: %s', self.username)
        logger.critical('CRITICAL: Saving instance of Account: %s', self.username)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

