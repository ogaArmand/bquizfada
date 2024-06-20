"""fada URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from biblequiz.views import *
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy

urlpatterns = [
    path('admin/', admin.site.urls),
    path('loginuser',loginuser,name='loginuser'),
    path('open_admin', open_admin, name='open_admin'),
    path('', accueil, name='accueil'),
    path('contacts', contacts, name='contacts'),
    path('apropos', apropos, name='apropos'),
    path('predications', predications, name='predications'),
    path('espacequiz', espacequiz, name='espacequiz'),
    path('temoignages', temoignages, name='temoignages'),
    path('create_account/', create_account, name='create_account'),
    path('paiement/', paiement, name='paiement'),
    path('recharge/', recharge, name='recharge'),
    path('show_questions/', show_questions, name='show_questions'),
    path('actualise_user_response/', actualise_user_response, name='actualise_user_response'),
    path('save_answers/', save_answers, name='save_answers'),
    path('save_answers_derniere/', save_answers_derniere, name='save_answers_derniere'),
    path('payment_success_view', payment_success_view,name='payment_success_view'),
    # path('monthly_transactions_count', monthly_transactions_count,name='monthly_transactions_count'),
    path('monthly_transactions_amount', monthly_transactions_amount,name='monthly_transactions_amount'),
    path('monthly_transactions_chart', monthly_transactions_chart,name='monthly_transactions_chart'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('loginuser')), name='logout'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

htmx_utrlpatern = [
    path('connexion/', connexion, name='connexion'),
]

urlpatterns += htmx_utrlpatern