from django.contrib import admin

from .models import Question, Hint, Contestant, Answer, Contest


class AnswerInLine(admin.TabularInline):
    model = Answer
    readonly_fields = ['text', 'question', 'time']


@admin.register(Contestant)
class MyUserAdmin(admin.ModelAdmin):
    inlines = [AnswerInLine]
    list_display = ['username', 'name', 'email', 'college', 'points', 'extra_time']
    fields = ['username',  'name', 'email', 'college', 'points', 'extra_time', 'answered_questions']
    filter_horizontal = ['answered_questions']
    # readonly_fields = ['answered_questions']
    search_fields = ['username', 'first_name', 'last_name', 'email']


# Register your models here.
class HintInline(admin.TabularInline):
    model = Hint
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [HintInline]
    list_display = ['__str__', 'text', 'points']
    ordering = ['number']


admin.site.register(Contest)
