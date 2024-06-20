from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import *
from .forms import CustomUserCreationForm, UserProfileForm

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    add_form = CustomUserCreationForm

class Transactionadmin(admin.ModelAdmin):
    list_display = ('user','amount','idTransaction','confirm','timestamp')

class Subscriptionadmin(admin.ModelAdmin):
    list_display = ('user','activated','remaining_questions')
    
class questionsadmin(admin.ModelAdmin):
    list_display = ('question_text','theme','explication','niveau')

class Answeradmin(admin.ModelAdmin):
    list_display = ('question','answer_text','is_correct')

class UserQuestionHistoryadmin(admin.ModelAdmin):
    list_display = ('question','user','date_displayed','is_affiche')

class UserResponseadmin(admin.ModelAdmin):
    list_display = ('question','user','response_text','is_correct','date_displayed')

class Badgeadmin(admin.ModelAdmin):
    list_display = ('name','description')

class UserProfileadmin(admin.ModelAdmin):
    list_display = ('user','display_badges','date_of_birth','phone_number')

    def display_badges(self, obj):
        return ", ".join([badge.name for badge in obj.badges.all()])


admin.site.register(Badge,Badgeadmin)
admin.site.register(UserProfile,UserProfileadmin)
admin.site.register(UserResponse,UserResponseadmin)
admin.site.register(UserQuestionHistory,UserQuestionHistoryadmin)
admin.site.register(Answer,Answeradmin)
admin.site.register(Question,questionsadmin)
admin.site.register(Subscription,Subscriptionadmin)
admin.site.register(Transaction,Transactionadmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)



admin.site.site_header = 'Administration Bible Quiz Fada'
admin.site.site_title = 'Bible Quiz Fada'