import logging
from functools import partial
from smtplib import SMTPException
from threading import Thread

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .decorators import verification_required
from .forms import NewUserForm, AnswerForm, LoginForm
from .models import Question, Answer, Contestant, ActivationModel

logger = logging.getLogger('got')


# Create your views here.
# @login_required
def index(request):
    if request.user.is_active:
        return HttpResponseRedirect(reverse('contest:question'))
    return render(request, "contest/index.html")


# @verification_required
# @require_http_methods(['GET', 'POST'])
# def question(request, id):
#     if request.method == 'GET':
#         context = {}
#         context['question'] = get_object_or_404(Question, number=id)
#         context['answer_form'] = AnswerForm()
#         return render(request, 'contest/question.html', context)
#
#     elif request.method == 'POST':
#         contestant = request.user.contestant
#         if contestant.answered_questions.filter(number=id):
#             return HttpResponseRedirect(reverse('contest:index'))
#
#         question = get_object_or_404(Question, number=id)
#         if (question.release_date > timezone.now()):
#             return HttpResponseRedirect(reverse('contest:index'))
#         answer_form = AnswerForm(request.POST)
#         if answer_form.is_valid():
#             answer = Answer(text=answer_form.cleaned_data['text'])
#             answer.time = timezone.now()
#             answer.contestant = contestant
#             answer.question = question
#             answer.save()
#             if answer.text == question.correct_answer:
#                 contestant.answered_questions.add(question)
#                 contestant.points += question.points
#                 contestant.extra_time += answer.time - question.release_date
#                 contestant.save()
#             else:
#                 return render(request, 'contest/question.html', {
#                     'question': question,
#                     'answer_form': answer_form,
#                     'wrong_answer': True,
#                 })
#
#             return HttpResponseRedirect(reverse('contest:index'))
#         else:
#             return HttpResponseRedirect(reverse('contest:question', args=[id]))


class Login(LoginView):
    template_name = 'contest/login.html'
    redirect_authenticated_user = True


def handle_answer(request):
    """ Return true if the answer is wrong """
    contestant = request.user.contestant
    number = request.POST.get('question_no')
    if not number:
        return
    question = Question.objects.filter(number=number)
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
        contestant.extra_time += answer.time - question.release_date
        contestant.save()
        return
    else:
        return question.number


@verification_required
def ques(request):
    context = {
        'questions': Question.objects.all(),
        'answer_form': AnswerForm(),
        'contestant': request.user.contestant
    }
    if request.method == 'POST':
        context['error_no'] = handle_answer(request)

    return render(request, 'contest/questions.html', context)


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
            contestant.save()
            login(request, contestant)
            act = ActivationModel.objects.create(contestant=contestant)
            activation_util(request)
            return HttpResponseRedirect(reverse('contest:verify'))
        else:
            render(request, 'contest/signup.html', {'form': form})
    else:
        return render(request, 'contest/signup.html', {'form': NewUserForm()})


@verification_required
def leaderboard(request):
    contestants = Contestant.objects.all().order_by('-points', 'extra_time')
    paginator = Paginator(contestants, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'start_num': (page_obj.number - 1) * 10
    }
    return render(request, 'contest/leader.html', context=context)


def logoutview(request):
    if request.user.is_authenticated:
        logout(request)

    return HttpResponseRedirect(reverse('contest:index'))


# @login_required
# def verifyview(request):
#     if request.user.is_active:
#         return HttpResponseRedirect(reverse('contest:index'))
#
#     if request.method == 'GET':
#         return render(request, 'contest/verify.html', {'email': request.user.email})
#     else:
#         code = request.POST.get('code')
#         act = ActivationModel.objects.get(hash=code)
#         if act:
#             act.contestant.is_active = True
#             act.contestant.save()
#             return HttpResponseRedirect(reverse('contest:index'))
#         else:
#             return HttpResponse('Invalid Code')


@login_required
@require_http_methods(['GET', 'POST'])
def verify_view(request):
    if request.user.is_active:
        return HttpResponseRedirect(reverse('contest:question'))

    if request.method == 'POST':
        resend = request.POST.get('resend_email')
        if resend:
            activation_util(request)
    else:
        hashcode = request.GET.get('h')
        if hashcode:
            model = ActivationModel.objects.filter(hash=hashcode)
            if model:
                contestant = model[0].contestant
                contestant.is_active = True
                contestant.save()
                return HttpResponseRedirect(reverse('contest:question'))

    return render(request, 'contest/verify.html', {'email': request.user.email})


# @login_required
# def resend_email(request):
#     if request.user.is_active:
#         return HttpResponseRedirect(reverse('contest:index'))
#
#     act = ActivationModel.objects.get(contestant=request.user)
#     try:
#         send_mail(
#             "Verification Code",
#             f"Your verification code is {act.hash}.",
#             "ankit@neodrishti.com",
#             [request.user.email],
#             fail_silently=False
#         )
#         return HttpResponseRedirect(reverse('contest:verify'))
#     except SMTPException:
#         HttpResponse("Couldn't send email")

def activation_util(request):
    contestant = request.user.contestant
    email = contestant.email
    hashcode = ActivationModel.objects.get(contestant=contestant).hash
    url = settings.ALLOWED_HOSTS[0] + '/verify/?h=' + hashcode
    t = Thread(target=partial(send_verification_email, receiver=email, url=url))
    t.start()


def send_verification_email(receiver, url):
    try:
        send_mail(
            "Verify account",
            "Thank you for signing up for NeoDrishti Game of Troves.\n\n"
            "Please follow the link below to verify your account.\n\n" + url,
            "ankit@neodrishti.com",
            [receiver],
            fail_silently=False,
            html_message=f'''
                <html>
                    <body>
                        Thank you for signing up for NeoDrishti Game of Troves. <br><br>
                        Please follow the link below to verify your account. <br><br> {url}
                    </body>
                </html>
            '''
        )
    except SMTPException as e:
        logger.exception(e)
        logger.debug(e)


# def api(request, id):
#     if id:
#         question = Question.objects.get(pk=id)
#         data = {}
#         data['text'] = question.text
#         data['ans'] = question.correct_answer
#         return HttpResponse(json.dumps(data))
#     return HttpResponse('id not found')


@verification_required
def rules(request):
    return render(request, 'contest/rules.html')
