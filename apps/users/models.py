from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email: str, full_name: str, password: str = None) -> 'User':
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email: str, full_name: str, password: str) -> 'User':
        """
        Creates and saves a staff user with the given email and password.
        """
        user = self.create_user(
            email=email,
            full_name=full_name,
            password=password
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, full_name: str, password: str) -> 'User':
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            full_name=full_name,
            password=password
        )
        user.staff = True
        user.admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """
    Custom user model
    """
    id = models.AutoField(primary_key=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255
    )
    user_id = models.CharField(verbose_name='Fyle user id', max_length=255, unique=True)
    full_name = models.CharField(verbose_name='full name', max_length=255)
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['full_name', 'email']

    objects = UserManager()

    class Meta:
        db_table = 'users'

    def has_module_perms(self, app_label: any) -> bool:
        """
        Does the user have permissions to view the app
        """
        return True

    def has_perm(self, perm: any, obj: any = None) -> bool:
        """
        Does the user have a specific permission?
        """
        return True

    def get_full_name(self) -> str:
        """
        The user is identified by their email address
        """
        return self.full_name

    def get_short_name(self) -> str:
        """
        The user is identified by their email address
        """
        return self.email

    def __str__(self) -> str:
        """
        Returns a string representation of the user
        """
        return self.user_id

    @property
    def is_staff(self) -> bool:
        """
        Is the user a member of staff?
        """
        return self.staff

    @property
    def is_admin(self) -> bool:
        """
        Is the user an admin member?
        """
        return self.admin

    @property
    def is_active(self) -> bool:
        """
        Is the user active?
        """
        return self.active
