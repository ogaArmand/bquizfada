from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
import json
from django.shortcuts import render, redirect, HttpResponseRedirect
from datetime import date, timedelta, datetime
from django.contrib.humanize.templatetags.humanize import intcomma
from django import template
from django.db.models import Func
from .models import *
from .forms import *
from django.contrib.auth import authenticate, login
import string
import random
from django.urls import reverse
import hashlib
import hmac
import requests
from django.db.models import Count
import pandas as pd
from django.db.models.functions import TruncMonth
# Create your views here.

import matplotlib
matplotlib.use('Agg')  # Utiliser le backend non interactif pour Matplotlib

from datetime import datetime
from matplotlib.dates import MonthLocator, DateFormatter
import pandas as pd
import matplotlib.pyplot as plt
from django.http import HttpResponse
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum
from .models import Transaction


groupe = None


def open_admin(request):
    return redirect('/admin/')

def moisenlettre():
    mois_en_lettres = {
    1: 'Janvier',
    2: 'Février',
    3: 'Mars',
    4: 'Avril',
    5: 'Mai',
    6: 'Juin',
    7: 'Juillet',
    8: 'Août',
    9: 'Septembre',
    10: 'Octobre',
    11: 'Novembre',
    12: 'Décembre'
    }

# Obtenez le mois actuel
    mois_en_cours = datetime.now().month

# Convertissez le numéro du mois en lettre en utilisant le dictionnaire
    mois_en_lettres = mois_en_lettres[mois_en_cours]
    return mois_en_lettres


def create_account(request):
    if request.method=='POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigez l'utilisateur vers la page de connexion ou toute autre page appropriée après la création du compte
            return redirect('loginuser')
    else:
        form = CustomUserCreationForm()
    return render(request, 'create_account.html', {'form': form})


class Unaccent(Func):
    function = 'UNACCENT'

register = template.Library()

@register.filter(name='intspace')
def intspace(value):
    """
    Similar to intcomma, but uses spaces as thousand separators instead of commas.
    """
    orig_value = intcomma(value)
    return orig_value.replace(',', ' ')

def loginuser(request):
    return render(request,'connexion.html')


@csrf_exempt
def connexion(request):
    username = request.POST.get('username')
    password = request.POST.get('pass')

    # Authentifier l'utilisateur avec les informations d'identification fournies
    user = authenticate(request, username=username, password=password)

    if user is not None:
        # Connecter l'utilisateur s'il est authentifié avec succès
        login(request, user)
        request.session['user_connecte'] = 1
        request.session['user_id'] = user.id
        request.session['user_name'] = user.last_name
        request.session['user_prenom'] = user.first_name
        request.session['user_login'] = user.username
        request.session['email'] = user.email
        
        return JsonResponse({'status': 'ok', 'message': 'Connecté'})
    else:
        return JsonResponse({'status': 'PasOk', 'message': 'Identifiants incorrects.'})




def accueil(request):
    user_connecte = request.session.get('user_connecte', None)
    user_cf = request.session.get('user_cf', None)
    aujourdhui = date.today()
    if user_connecte is None:
        # La variable de session user_cf n'existe pas, rediriger vers la page de connexion
        return redirect('loginuser')
    user =  request.user
    user_name = user.first_name + ' ' + user.last_name

    total_amount = Transaction.objects.filter(user=request.user).aggregate(total_amount=models.Sum('amount'))
    transaction_count = Transaction.objects.filter(user=request.user).count()

    monthly_transactions = Transaction.objects.filter(user=request.user).annotate(
        month=TruncMonth('timestamp')
    ).values('month').annotate(
        transaction_count=Count('id'),
        total_amount=models.Sum('amount')
    ).order_by('month')

    # Convertir les résultats en DataFrame Pandas pour une manipulation facile
    df = pd.DataFrame(monthly_transactions)

    subscription=""
    remaining_questions=0
    userResponse_today = UserResponse.objects.filter(user=request.user,date_displayed=aujourdhui)
    userResponse_today_count = userResponse_today.count()
    userResponse_today_just = UserResponse.objects.filter(user=request.user,date_displayed=aujourdhui,is_correct=True)
    userResponse_today_count_just = userResponse_today_just.count()
    userResponse_today_count_faux=userResponse_today_count-userResponse_today_count_just

    if Subscription.objects.filter(user=request.user, activated=True).exists():
        subscription = Subscription.objects.get(user=request.user)
        remaining_questions = subscription.remaining_questions

    # Obtenez la date du jour

    context = {
        'aujourdhui':aujourdhui,
        'remaining_questions':remaining_questions,
        'userResponse_today_count':userResponse_today_count,
        'userResponse_today_count_just':userResponse_today_count_just,
        'userResponse_today_count_faux':userResponse_today_count_faux,
        'user_name':user_name,
        'total_amount': total_amount,
        'transaction_count': transaction_count,
        'monthly_transactions': df.to_json(orient='records'),
    }
    return render(request,'index.html',context)

def recharge(request):
    user_connecte = request.session.get('user_connecte', None)

    
    if user_connecte is None:
        # La variable de session user_cf n'existe pas, rediriger vers la page de connexion
        return redirect('loginuser')
    user =  request.user
    user_name = user.username
    context = {
       'user_name':user_name 
    }
    return render(request, 'subscription_required.html',context)

def calculate_questions_paid(amount_paid, question_cost):
    return int(amount_paid) // int(question_cost)


def show_questions(request):
    user_connecte = request.session.get('user_connecte', None)
    user_cf = request.session.get('user_cf', None)
    
    if user_connecte is None:
        # La variable de session user_cf n'existe pas, rediriger vers la page de connexion
        return redirect('loginuser')
    ACCEPTED = request.POST.get('ACCEPTED')

    if ACCEPTED == 'ACCEPTED':
        amount = request.POST.get('amount')
        if amount is not None:
            amount = eval(amount)[0] 
        question_cost = 50  # Coût d'une question
        questions_available = calculate_questions_paid(amount, question_cost)
        user_instance = User.objects.get(pk=request.user.id)
        # Vérifier si l'utilisateur a déjà un abonnement actif
        if not Subscription.objects.filter(user=user_instance, activated=True).exists():
            subscription = Subscription.objects.create(
                user=user_instance,
                activated=True,
                remaining_questions=questions_available
            )
            return JsonResponse({'status': 'ok', 'message': 'Abonnement créé avec succès'})

    if Subscription.objects.filter(user=request.user, activated=True).exists():
        subscription = Subscription.objects.get(user=request.user)
        if subscription.remaining_questions > 0:
            # Récupérer la date actuelle
            today = date.today()

            # Obtenez des questions qui n'ont pas encore été posées à l'utilisateur aujourd'hui
            answered_questions_today = UserQuestionHistory.objects.filter(user=request.user,is_affiche=True)
            userResponse_today = UserResponse.objects.filter(user=request.user,date_displayed=today)
            userResponse_today_count = userResponse_today.count()

            userResponse_today_just = UserResponse.objects.filter(user=request.user,date_displayed=today,is_correct=True)
            userResponse_today_count_just = userResponse_today_just.count()
            userResponse_today_count_faux=userResponse_today_count-userResponse_today_count_just
                    
            # Limitez à 5 questions par jour
            remaining_questions = min(subscription.remaining_questions, 5 - userResponse_today_count)
            questions = ""
            if remaining_questions >=0:
                # Obtenez des questions qui n'ont pas encore été posées à l'utilisateur
                available_questions = Question.objects.exclude(id__in=answered_questions_today.values_list('question_id', flat=True))
                questions = available_questions.order_by('?')[:remaining_questions]
            
            if questions:
                # Enregistrez les questions posées à l'utilisateur
                for question in questions:
                    premiere_question_id = question.id
                    break  # Sortir de la boucle après avoir récupéré la première question

                for question in questions:
                    # Vérifier si la question existe déjà dans l'historique pour cet utilisateur
                    user_history_entry = UserQuestionHistory.objects.filter(user=request.user, question=question).first()

                    if not user_history_entry:
                        # Si la question n'existe pas, vous pouvez la créer
                        UserQuestionHistory.objects.create(user=request.user, question=question)
                        
                    # UserQuestionHistory.objects.create(user=request.user, question=question)
                    instance_question = Question.objects.get(pk=premiere_question_id)
                    QuestionHistory_aff = UserQuestionHistory.objects.get(user=request.user, question=instance_question)
                    QuestionHistory_aff.is_affiche = True
                    QuestionHistory_aff.date_displayed = today
                    QuestionHistory_aff.save()
                # subscription.remaining_questions -= 5
                # subscription.save()
                    # print(question.question_text)
            
                context = {
                    'userResponse_today_count_faux':userResponse_today_count_faux,
                    'userResponse_today_count':userResponse_today_count,
                    'userResponse_today_count_just':userResponse_today_count_just,
                    'questions': questions,
                }
                print('OKOKOKOK OKOKOKOK')
                return render(request, 'show_questions.html', context)
            else:
                userresponse_today = UserResponse.objects.filter(user=request.user,date_displayed=today)
                userresponse_today_count = userresponse_today.count()
                
                context = {
                    'questions': questions,
                    'userresponse_today_count':userresponse_today_count,
                    }
                return render(request, 'no_question_today.html',context)
        else:
            return render(request, 'subscription_required.html')
    else:
        return render(request, 'subscription_required.html')




def check_payment_status(transaction_id, site_id, apikey):
    api_url = "https://api-checkout.cinetpay.com/v2/payment/check"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "transaction_id": transaction_id,
        "site_id": site_id,
        "apikey": apikey
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None
    
@csrf_exempt
def payment_success_view(request): # url de retour
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')  # Récupérez le transaction_id de la requête POST
        site_id = '524004'  # Remplacez par votre site_id
        apikey = '200725165962c58cffd92489.76665090'  # Remplacez par votre apikey

        # Vérifiez le statut de la transaction en utilisant la fonction check_payment_status
        result = check_payment_status(transaction_id, site_id, apikey)

        amount = result["data"]["amount"],
        status = result["data"]["status"],
        payment_method = result["data"]["payment_method"],
        description = result["data"]["description"],
        metadata =  result["data"]["metadata"],
        operator_id = result["data"]["operator_id"],
        payment_date = result["data"]["payment_date"],
        fund_availability_date = result["data"]["fund_availability_date"],
        
        if result is not None:
            # Si la requête a réussi, vous pouvez renvoyer le statut de la transaction dans la réponse JSON
            context = {
            'amount':amount,
            'status':status,
            'payment_method':payment_method,
            'description':description,
            'metadata':metadata,
            'operator_id':operator_id,
            'payment_date':payment_date,
            'fund_availability_date':fund_availability_date
            }
            #return JsonResponse({"status": result["status"]})
            return render(request, "success.html",context)
        else:
            # Si la requête a échoué ou si le résultat est None, vous pouvez renvoyer une réponse d'erreur
            return JsonResponse({"error": "Une erreur s'est produite lors de la vérification du statut de la transaction"})
    else:
        # Si la requête n'est pas de type POST, renvoyer une réponse d'erreur
        #return JsonResponse({"error": "Méthode non autorisée"}, status=405)
        return render(request, "success.html")


def generate_random_transaction_id():
    # Génère un ID aléatoire de 10 caractères en combinant lettres minuscules et chiffres
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(10))

def paiement(request):
    if request.method == 'POST':
        cout = request.POST.get('cout')
       
        cout = int(cout)
        user = request.user

    # Accédez aux informations de l'utilisateur, par exemple :
        customer_name = user.first_name
        customer_email = user.email
        customer_id = user.id
        customer_last_name = user.last_name
        transaction_id = generate_random_transaction_id()
         # Obtenez le jeton CSRF à partir de la requête POST
        csrf_token = request.COOKIES['csrftoken']
        api_url = "https://api-checkout.cinetpay.com/v2/payment"  # Remplacez ceci par l'URL de votre API
        headers = {
        'Content-Type': 'application/json; charset=utf8',
        'X-CSRFToken': csrf_token,  # Incluez le jeton CSRF dans l'en-tête
        }
        data = {
        
        "apikey": "200725165962c58cffd92489.76665090",
        "site_id": "524004",
        "transaction_id": transaction_id,
        "amount": cout,
        "currency": "XOF",
        "alternative_currency": "",
        "description": "Abonnement bible quiz fada" ,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "customer_surname": customer_last_name,
        "customer_email": customer_email,
        "customer_phone_number": "+225004315545",
        "customer_address": "Abidjan",
        "customer_city": "Abidjan",
        "customer_country": "CI",
        "customer_state": "CI",
        "customer_zip_code": "065100",
        # "notify_url": "https://dry-sands-12879-45d4e55d9cf1.herokuapp.com/api/kobotoolbox-data/",
        # "notify_url": "https://webhook.site/9c604710-681b-434b-80b9-535385e56e30",
        # "notify_url": request.build_absolute_uri(reverse('payment_notification')),
        "return_url": request.build_absolute_uri(reverse('payment_success_view')),  # Utilise la vue payment_success_view comme URL de redirection
        "channels": "ALL",
        "metadata": "user1",
        "lang": "FR",
        # "invoice_data": {
        #     "Type de location ": Car_Type,
        #     "Code de la reservation": "",
        #     "item reservé": description
        #     }
        }

        user_instance = User.objects.get(pk=customer_id)
        transaction = Transaction.objects.create(
            user=user_instance,
            amount=cout,
            idTransaction=transaction_id,
            timestamp=datetime.now()
        )

        try:
            response = requests.post(api_url, headers=headers, json=data)

            # Vérifiez si la requête a réussi (code 200)
            if response.status_code == 200:
                
                data = response.json()  # Convertit la réponse JSON en Python dict/list
                payment_url = data["data"]["payment_url"]
                payment_token = data["data"]["payment_token"]
                return redirect(payment_url)  # Redirige l'utilisateur vers l'URL de paiement
            else:
            # Si la requête a échoué, vous pouvez retourner un code d'erreur ou un message approprié
                    return JsonResponse({"error": "La requête a échoué"}, status=response.status_code)
        except requests.exceptions.RequestException as e:
        # Si une exception se produit (par exemple, problème de connexion réseau), vous pouvez la gérer ici
                return JsonResponse({"error": "Une erreur s'est produite lors de la requête"}, status=500)
       

    return render(request,'subscription_required.html')


@csrf_exempt
def save_answers(request):

    today = date.today()
    if request.method == 'POST':
        data = json.loads(request.body)  # Assurez-vous d'envoyer les données en tant que JSON depuis le frontend
        question_id = data.get('question_id')
        Idquestion_aff = data.get('Idquestion_aff')
        answer_id = data.get('answer_id')

        try:
            print(data)
            print(question_id)
            print(Idquestion_aff)
            print(answer_id)
            instance_question = Question.objects.get(pk=Idquestion_aff)
            QuestionHistory_aff = UserQuestionHistory.objects.get(user=request.user, question=instance_question)
            QuestionHistory_aff.is_affiche = True
            QuestionHistory_aff.date_displayed = today
            QuestionHistory_aff.save()
            # Récupérer l'objet Answer associé à l'ID de réponse
            answer = Answer.objects.get(id=answer_id)
            # Récupérer l'utilisateur actuel
            user_instance = request.user
            # Récupérer l'objet Question associé à l'ID de question
            question_instance = Question.objects.get(pk=question_id)
            # Créer et sauvegarder l'objet UserResponse dans la base de données
            response = UserResponse.objects.create(
                question=question_instance, 
                response_text=answer.answer_text, 
                is_correct=answer.is_correct, 
                user=user_instance
            )
                        # Décrémenter le nombre de questions disponibles pour l'utilisateur
            subscription = Subscription.objects.get(user=user_instance)
            subscription.decrement_questions()

            return JsonResponse({'status': 'ok', 'message': 'Réponse enregistrée avec succès.','status_reponse':answer.is_correct})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Méthode de requête non autorisée.'})





def calculate_user_performance(user):
    total_correct_answers = UserResponse.objects.filter(user=user, is_correct=True).count()
    return total_correct_answers

def award_rewards(user):
    
    performance = calculate_user_performance(user)
    # Exemple d'attribution de récompenses
    if performance >= 20:
        # Attribuer un badge "Expert Biblique" à l'utilisateur
        user.profile.badges.add(Badge.objects.get(name="Expert Biblique"))
    elif performance >= 10:
        # Attribuer un badge "Connaisseur Biblique" à l'utilisateur
        user.profile.badges.add(Badge.objects.get(name="Connaisseur Biblique"))
    # Ajoutez d'autres conditions et récompenses selon votre choix


def show_rewards(request):
    user = request.user
    # Obtenez les badges de l'utilisateur
    badges = user.profile.badges.all()
    return render(request, 'show_rewards.html', {'badges': badges})


def save_answers_derniere(request):
    today = date.today()

    if request.method == 'POST':
        data = request.POST  # Assurez-vous d'envoyer les données en tant que JSON depuis le frontend
        question_id = data.get('question_idd')
        questions = "" 
        
        # Idquestion_aff = data.get('Idquestion_aff')
        answer_id = data.get('question'+question_id)

        try:
            

            # Récupérer l'objet Answer associé à l'ID de réponse
            answer = Answer.objects.get(id=answer_id)
            # Récupérer l'utilisateur actuel
            user_instance = request.user
            # Récupérer l'objet Question associé à l'ID de question
            question_instance = Question.objects.get(pk=question_id)
            # Créer et sauvegarder l'objet UserResponse dans la base de données
            response = UserResponse.objects.create(
                question=question_instance, 
                response_text=answer.answer_text, 
                is_correct=answer.is_correct, 
                user=user_instance
            )
            userresponse_today = UserResponse.objects.filter(user=request.user,date_displayed=today)
            userresponse_today_count = userresponse_today.count()
            print(userresponse_today_count)
            # award_rewards(user_instance)
                        # Décrémenter le nombre de questions disponibles pour l'utilisateur
            subscription = Subscription.objects.get(user=user_instance)
            subscription.decrement_questions()
            
            context = {
                'questions': questions,
                'userresponse_today_count':userresponse_today_count
            }

            return render(request, 'no_question_today.html',context)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Méthode de requête non autorisée.'})


def monthly_transactions_amount(request):
    # Obtenez l'année en cours
    current_year = datetime.now().year
    
    # Obtenez les données mensuelles pour l'année en cours
    monthly_transactions = Transaction.objects.filter(user=request.user,timestamp__year=current_year) \
        .annotate(month=TruncMonth('timestamp')) \
        .values('month') \
        .annotate(transaction_count=Count('id'), total_amount=Sum('amount')) \
        .order_by('month')
    
    # Convertir les résultats en DataFrame Pandas pour une manipulation facile
    df = pd.DataFrame(monthly_transactions)

    # Assurez-vous que la colonne 'month' est de type datetime
    df['month'] = pd.to_datetime(df['month'])
    
    # # Plot
    # fig, ax1 = plt.subplots(figsize=(6, 3))
    # ax1.plot(df['month'], df['transaction_count'], marker='o', linestyle='-', color='b', label='Transaction Count')
    # ax1.set_xlabel('Month')
    # ax1.set_ylabel('Transaction Count', color='b')
    

    # # Créer un diagramme en camembert pour le montant total
    # fig, ax1 = plt.subplots(figsize=(3, 3))
    # ax1.pie(df['total_amount'], labels=df['month'].dt.strftime('%B'), autopct='%1.1f%%', startangle=140)
    # ax1.axis('equal')  # Assurez-vous que le diagramme en camembert est circulaire

    fig, ax = plt.subplots(figsize=(4, 4))
    wedges, labels, autopct = ax.pie(df['total_amount'], autopct='%1.1f%%', startangle=140)
    ax.axis('equal')  # Assurez-vous que le diagramme en camembert est circulaire
    ax.legend(wedges, df['month'].dt.strftime('%B'), title='Mois', loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=3)


    plt.title('Monthly Transactions for {}'.format(current_year))
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    # Convertir le graphique en image
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response


def monthly_transactions_chart(request):
    # Obtenez l'année en cours
    current_year = datetime.now().year
    
    # Obtenez les données mensuelles pour l'année en cours
    
    monthly_transactions = Transaction.objects.filter(user=request.user,timestamp__year=current_year) \
        .annotate(month=TruncMonth('timestamp')) \
        .values('month') \
        .annotate(transaction_count=Count('id'), total_amount=Sum('amount')) \
        .order_by('month')
    
    # Convertir les résultats en DataFrame Pandas pour une manipulation facile
    df = pd.DataFrame(monthly_transactions)

    # Assurez-vous que la colonne 'month' est de type datetime
    df['month'] = pd.to_datetime(df['month'])
    
    # Plot
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.plot(df['month'], df['transaction_count'], marker='o', linestyle='-', color='b', label='Nombre de Transactions')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Nombre de Transactions', color='b')
    
    # Configurer l'axe des abscisses pour afficher uniquement les mois de l'année en cours
    ax1.xaxis.set_major_locator(MonthLocator())
    ax1.xaxis.set_major_formatter(DateFormatter('%B'))  # '%B' pour afficher le nom complet du mois
    
    # Ajouter une deuxième échelle à droite pour le montant total
    ax2 = ax1.twinx()
    ax2.plot(df['month'], df['total_amount'], marker='s', linestyle='-', color='r', label='Montant')
    ax2.set_ylabel('Montant', color='r')

    # Gérer la légende
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines +lines2, labels +labels2, loc='upper right')

    plt.title('Transactions Mensuelles pour {}'.format(current_year))
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    # Convertir le graphique en image
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response 


def actualise_user_response(request):
    today = date.today()
    userResponse_today = UserResponse.objects.filter(user=request.user,date_displayed=today)
    userResponse_today_count = userResponse_today.count()

    userResponse_today_just = UserResponse.objects.filter(user=request.user,date_displayed=today,is_correct=True)
    userResponse_today_count_just = userResponse_today_just.count()
    userResponse_today_count_faux=userResponse_today_count-userResponse_today_count_just

    return JsonResponse({
        'userResponse_today_count': userResponse_today_count,
        'userResponse_today_count_just': userResponse_today_count_just,
        'userResponse_today_count_faux': userResponse_today_count_faux,
    })


def contacts(request):
    return render(request,'contact.html')

def apropos(request):
    return render(request,'about.html')

def predications(request):
    return render(request,'product.html')

def espacequiz(request):
    user_connecte = request.session.get('user_connecte', None)
    user_cf = request.session.get('user_cf', None)
    
    if user_connecte is None:
        # La variable de session user_cf n'existe pas, rediriger vers la page de connexion
        return redirect('loginuser')
    ACCEPTED = request.POST.get('ACCEPTED')

    if ACCEPTED == 'ACCEPTED':
        amount = request.POST.get('amount')
        if amount is not None:
            amount = eval(amount)[0] 
        question_cost = 50  # Coût d'une question
        questions_available = calculate_questions_paid(amount, question_cost)
        user_instance = User.objects.get(pk=request.user.id)
        # Vérifier si l'utilisateur a déjà un abonnement actif
        if not Subscription.objects.filter(user=user_instance, activated=True).exists():
            subscription = Subscription.objects.create(
                user=user_instance,
                activated=True,
                remaining_questions=questions_available
            )
            return JsonResponse({'status': 'ok', 'message': 'Abonnement créé avec succès'})

    if Subscription.objects.filter(user=request.user, activated=True).exists():
        subscription = Subscription.objects.get(user=request.user)
        if subscription.remaining_questions > 0:
            # Récupérer la date actuelle
            today = date.today()

            # Obtenez des questions qui n'ont pas encore été posées à l'utilisateur aujourd'hui
            answered_questions_today = UserQuestionHistory.objects.filter(user=request.user,is_affiche=True)
            userResponse_today = UserResponse.objects.filter(user=request.user,date_displayed=today)
            userResponse_today_count = userResponse_today.count()

            userResponse_today_just = UserResponse.objects.filter(user=request.user,date_displayed=today,is_correct=True)
            userResponse_today_count_just = userResponse_today_just.count()
            userResponse_today_count_faux=userResponse_today_count-userResponse_today_count_just
                    
            # Limitez à 5 questions par jour
            remaining_questions = min(subscription.remaining_questions, 5 - userResponse_today_count)
            questions = ""
            if remaining_questions >=0:
                # Obtenez des questions qui n'ont pas encore été posées à l'utilisateur
                available_questions = Question.objects.exclude(id__in=answered_questions_today.values_list('question_id', flat=True))
                questions = available_questions.order_by('?')[:remaining_questions]
            
            if questions:
                # Enregistrez les questions posées à l'utilisateur
                for question in questions:
                    premiere_question_id = question.id
                    break  # Sortir de la boucle après avoir récupéré la première question

                for question in questions:
                    # Vérifier si la question existe déjà dans l'historique pour cet utilisateur
                    user_history_entry = UserQuestionHistory.objects.filter(user=request.user, question=question).first()

                    if not user_history_entry:
                        # Si la question n'existe pas, vous pouvez la créer
                        UserQuestionHistory.objects.create(user=request.user, question=question)
                        
                    # UserQuestionHistory.objects.create(user=request.user, question=question)
                    instance_question = Question.objects.get(pk=premiere_question_id)
                    QuestionHistory_aff = UserQuestionHistory.objects.get(user=request.user, question=instance_question)
                    QuestionHistory_aff.is_affiche = True
                    QuestionHistory_aff.date_displayed = today
                    QuestionHistory_aff.save()
                # subscription.remaining_questions -= 5
                # subscription.save()
                    # print(question.question_text)
            
                context = {
                    'userResponse_today_count_faux':userResponse_today_count_faux,
                    'userResponse_today_count':userResponse_today_count,
                    'userResponse_today_count_just':userResponse_today_count_just,
                    'questions': questions,
                }
                print('OKOKOKOK OKOKOKOK')
                return render(request,'blog_list.html',context)
                # return render(request, 'show_questions.html', context)
            else:
                userresponse_today = UserResponse.objects.filter(user=request.user,date_displayed=today)
                userresponse_today_count = userresponse_today.count()
                
                context = {
                    'questions': questions,
                    'userresponse_today_count':userresponse_today_count,
                    }
                return render(request, 'no_question_today.html',context)
        else:
            return render(request, 'subscription_required.html')
    else:
        return render(request, 'subscription_required.html')
    

def temoignages(request):
    return render(request,'blog_list.html')