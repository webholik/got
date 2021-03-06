import datetime
import logging
import math
from functools import partial
from threading import Thread

from django.conf import settings
from django.contrib.auth import login, logout
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import NewUserForm, AnswerForm, LoginForm, PasswordResetForm
from .models import Question, Answer, Contestant, ActivationModel, Contest, PasswordResetModel, Message
from .utils import verification_required, send_mail

logger = logging.getLogger('got')


def index(request):
    if request.user.is_active:
        return HttpResponseRedirect(reverse('contest:question'))
    return HttpResponseRedirect(reverse('contest:login'))
    # return render(request, "contest/index.html")


def handle_answer(request):
    """ Return true if the answer is wrong """
    contestant = request.user
    number = request.POST.get('question_id')
    if not number:
        return
    question = Question.objects.filter(pk=number)
    if not question:
        return
    question = question[0]
    if question in contestant.answered_questions.all():
        return
    answer_form = AnswerForm(request.POST)
    if not answer_form.is_valid():
        return

    answer = Answer(text=answer_form.cleaned_data['text'])
    answer.time = timezone.now()
    answer.contestant = contestant
    answer.question = question
    answer.save()
    if answer.text == question.correct_answer:
        contestant.answered_questions.add(question)
        contestant.points += question.points
        contest = Contest.objects.get(pk=1)
        contestant.extra_time += answer.time - contest.start_time
        contestant.last_answered = timezone.now()
        contestant.save()
        return
    else:
        return True


def ques_util(request, context):
    diff = timezone.now() - request.user.last_answered
    hints = context['question'].hint_set.all()
    context['hints'] = []
    if diff > datetime.timedelta(hours=3):
        context['hints'] = hints
        context['time_left'] = -1;
    elif diff > datetime.timedelta(hours=2):
        context['hints'].extend([hints[0], hints[1]])
        context['time_left'] = math.ceil((datetime.timedelta(hours=3) - diff).seconds / 60)
    elif diff > datetime.timedelta(hours=1):
        context['hints'].append(hints[0])
        context['time_left'] = math.ceil((datetime.timedelta(hours=2) - diff).seconds / 60)
    else:
        context['time_left'] = math.ceil((datetime.timedelta(hours=1) - diff).seconds / 60)

    return render(request, 'contest/questions.html', context)


@verification_required
def ques(request):
    contest = Contest.objects.get()
    if contest.start_time > timezone.now():
        return render(request, 'contest/countdown.html', {'start_time': contest.start_time - timezone.now()})

    context = {}
    if request.method == 'POST':
        if handle_answer(request):
            context['error'] = True
        else:
            q_num = request.POST.get('question_id')
            question = Question.objects.get(pk=q_num)
            if question:
                context['question'] = question
                context['answer_form'] = AnswerForm()
                context['solved'] = True
                # return render(request, 'contest/questions.html', context)
                return ques_util(request, context)

    questions = Question.objects.all().order_by('number')
    contestant = request.user
    for q in questions:
        if q not in contestant.answered_questions.all():
            context['question'] = q
            context['answer_form'] = AnswerForm()
            # return render(request, 'contest/questions.html', context)
            return ques_util(request, context)
    return render(request, 'contest/questions.html')


@require_http_methods(['GET', 'POST'])
def loginview(request):
    if request.user.is_authenticated:
        if request.user.is_active:
            return HttpResponseRedirect(reverse('contest:question'))
        else:
            return HttpResponseRedirect(reverse('contest:verify'))

    if request.method == 'GET':
        return render(request, 'contest/login.html', context={'form': LoginForm()})
    else:
        form = LoginForm(request, request.POST)
        if form.is_valid():
            login(request, form.user)
            if request.user.is_active:
                return HttpResponseRedirect(reverse('contest:question'))
            else:
                return HttpResponseRedirect(reverse('contest:verify'))
        else:
            return render(request, 'contest/login.html', context={'form': form})


@require_http_methods(['GET', 'POST'])
def signup(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('contest:question'))

    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            contestant = form.save()
            contestant.is_active = False
            contestant.last_answered = Contest.objects.get().start_time
            contestant.save()
            login(request, contestant)
            act = ActivationModel.objects.create(contestant=contestant)
            activation_util(contestant)
            return HttpResponseRedirect(reverse('contest:verify'))
        else:
            return render(request, 'contest/signup.html', {'form': form})
    else:
        return render(request, 'contest/signup.html', {'form': NewUserForm()})


@verification_required
def leaderboard(request):
    num = 20
    contestants = Contestant.objects.all().order_by('-points', 'extra_time')
    paginator = Paginator(contestants, num)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'start_num': (page_obj.number - 1) * num
    }
    return render(request, 'contest/leader.html', context=context)


def logoutview(request):
    if request.user.is_authenticated:
        logout(request)

    return HttpResponseRedirect(reverse('contest:index'))


def verify_view(request):
    if request.user.is_active:
        return HttpResponseRedirect(reverse('contest:question'))

    if request.method == 'POST':
        resend = request.POST.get('resend_email')
        username = request.session.get('user')
        user = Contestant.objects.get(pk=username)
        if user and resend:
            activation_util(user)
        else:
            return HttpResponseRedirect(reverse('contest:login'))
    else:
        hashcode = request.GET.get('h')
        if hashcode:
            model = ActivationModel.objects.filter(hash=hashcode)
            if model:
                contestant = model[0].contestant
                contestant.is_active = True
                # Everyone should start with the same last_answered
                contestant.save()
                return HttpResponseRedirect(reverse('contest:question'))

    if request.user.is_authenticated:
        user = request.user
        logout(request)
        request.session['user'] = user.username
        return render(request, 'contest/verify.html', {'email': user.email})
    else:
        return HttpResponseRedirect(reverse('contest:login'))


def activation_util(user):
    hashcode = ActivationModel.objects.get(contestant=user).hash
    url = 'http://' + settings.ALLOWED_HOSTS[0] + '/verify/?h=' + hashcode
    header = "Verify account"
    message = "Thank you for signing up for NeoDrishti Game of Troves.\n\n" + "Please follow the link below to verify your account.\n\n" + url
    html_message = f'''
                <html>
                    <body>
                        Thank you for signing up for NeoDrishti Game of Troves. <br><br>
                        Please follow the link below to verify your account. <br><br> {url}
                    </body>
                </html>
            '''

    t = Thread(target=partial(user.send_email, header=header, message=message, html_message=html_message))
    t.start()


def password_reset_util(user):
    model = PasswordResetModel.objects.create(contestant=user)
    hashcode = model.hash
    url = 'http://' + settings.ALLOWED_HOSTS[0] + '/reset/?h=' + hashcode
    header = "Reset Password"
    message = "We have received a request to reset your password on Neodrishti Game of Troves\n\n" \
              + "If the request was made by you then please follow the link below to reset your password." \
              + "Otherwise simply ignore this email.\n\n" \
              + url
    html_message = f'''
                    <html>
                        <body>
                            We have received a request to reset your password on Neodrishti Game of Troves <br><br>
                            If the request was made by you then please follow the link below to reset your password. 
                            Otherwise simply ignore this email. <br><br> {url} 
                        </body>
                    </html>
                '''

    t = Thread(target=partial(user.send_email, header=header, message=message, html_message=html_message))
    t.start()


# @verification_required
# def rules(request):
#     pass


def reset_password(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('contest:question'))

    if request.method == 'POST':
        email = request.POST.get('email')
        user = Contestant.objects.filter(email=email)
        if user:
            password_reset_util(user[0])
            return render(request, 'contest/reset_password.html', {'sent': True})
        else:
            return render(request, 'contest/reset_password.html', {'error': True})

    return render(request, 'contest/reset_password.html')


def reset(request):
    if request.method == 'GET':
        hashcode = request.GET.get('h')
        model = PasswordResetModel.objects.filter(hash=hashcode)
        if model:
            user = model[0].contestant
            model[0].delete()
            request.session['user'] = user.username
            return render(request, 'contest/reset.html', {'form': PasswordResetForm})
    elif request.method == 'POST':
        username = request.session.get('user')
        user = Contestant.objects.filter(pk=username)
        if user:
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                user[0].set_password(form.cleaned_data['password1'])
                user[0].save()
                return HttpResponseRedirect(reverse('contest:login'))

    return render(request, 'contest/reset.html', {'error': True})


def read_message(request):
    id = request.POST.get('id')
    message = Message.objects.filter(id=id)
    if message and not message[0].seen:
        message[0].seen = True
        message[0].save()


@csrf_exempt
def send_email_to(request):
    name = request.POST.get('name')
    email = request.POST.get('email')
    message = request.POST.get('message')
    if name and email and message:
        send_mail('LifeofPy contact mail from ' + name, 'nd.ojass@nitjsr.ac.in', message, sender=email)

    print(request.headers)
    return HttpResponseRedirect('http://lifeofpy.neodrishti.live')
