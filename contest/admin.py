from django.contrib import admin

from .models import Question, Hint, Contestant, Answer, Contest, Message


class AnswerInLine(admin.TabularInline):
    model = Answer
    readonly_fields = ['question', 'text', 'time']
    extra = 1


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['seen']


@admin.register(Contestant)
class MyUserAdmin(admin.ModelAdmin):
    inlines = [AnswerInLine, MessageInline]
    list_display = ['username', 'name', 'email', 'phone', 'college', 'points', 'extra_time']
    fields = ['username', 'name', 'email', 'phone', 'college', 'points', 'extra_time', 'is_active', 'answered_questions']
    filter_horizontal = ['answered_questions']
    # readonly_fields = ['answered_questions']
    search_fields = ['username', 'first_name', 'last_name', 'email']


# Register your models here.
class HintInline(admin.TabularInline):
    model = Hint
    extra = 3


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [HintInline]
    list_display = ['__str__', 'text', 'points']
    ordering = ['number']


admin.site.register(Contest)
