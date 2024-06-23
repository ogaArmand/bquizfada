from django.db import models
from django.contrib.auth.models import User

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    badges = models.ManyToManyField(Badge, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone_indicatif = models.CharField(max_length=10, blank=True,null=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.username


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    activated = models.BooleanField(default=False)
    remaining_questions = models.IntegerField(default=0)

    def decrement_questions(self):
        if self.remaining_questions > 0:
            self.remaining_questions -= 1
            self.save()

class Question(models.Model):
    question_text = models.CharField(max_length=1000)
    theme = models.CharField(max_length=100)
    explication = models.CharField(max_length=1000)
    niveau = models.IntegerField(default=1)
    def __str__(self) -> str:
        return self.question_text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=1000)
    is_correct = models.BooleanField(default=False)
    # Ajoutez d'autres champs si nécessaire

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    idTransaction = models.CharField(max_length=100,default='')
    confirm = models.BooleanField(default=False)
    timestamp = models.DateTimeField()

class UserQuestionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_affiche = models.BooleanField(default=False)
    date_displayed=models.DateField(null=True)

class UserResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    date_displayed=models.DateField(auto_now_add=True,null=True)