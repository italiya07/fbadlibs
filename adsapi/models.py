from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
import datetime
from datetime import date

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email')

        user = self.model(
            email=email,
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password):
        """
        Creates and saves a staff user with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    # def get_avatar_path(self, filename):
    #     ext = filename.split('.')[-1]
    #     filename = "%s.%s" % (uuid.uuid4(), ext)
    #     return 'media/profile/' + filename

    #username=models.CharField(max_length=100,null=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True
    )
    first_name=models.CharField(null=True,blank=True, max_length=100)
    last_name=models.CharField(null=True, blank=True, max_length=100)
    # profile_picture=models.ImageField(upload_to=get_avatar_path, null=True, blank=True)
    #phone_number=models.PositiveBigIntegerField(null=True)
    date_joined=models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True) # a admin user; non super-user
    is_superuser = models.BooleanField(default=False) # a superuser

    # notice the absence of a "Password field", that is built in.

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Email & Password are required by default.
    objects = UserManager()
    
    def get_pre_signed_url(self):
        return self.profile_picture

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    # @property
    # def is_staff(self):
    #     "Is the user a member of staff?"
    #     return self.is_staff

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return self.is_superuser

class ForgotPassword(models.Model):
    email=models.ForeignKey(User,on_delete=models.CASCADE)
    forgot_password_token=models.CharField(max_length=100)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email.email

class SaveAds(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    ad=models.CharField(max_length=100)

class Subscription_details(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    customer_id=models.CharField(max_length=122,null=False,blank=False)
    subscription_id=models.CharField(max_length=122)
    sub_status=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
