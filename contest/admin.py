from django.contrib import admin

from .models import Question, Hint, Contestant, Answer


class AnswerInLine(admin.TabularInline):
    model = Answer


@admin.register(Contestant)
class MyUserAdmin(admin.ModelAdmin):
    inlines = [AnswerInLine]
    list_display = ['username', 'first_name', 'last_name', 'email', 'college', 'points', 'extra_time']


# Register your models here.
class HintInline(admin.TabularInline):
    model = Hint
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [HintInline]
