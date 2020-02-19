# Generated by Django 3.0.2 on 2020-02-19 00:05

import contest.models
import datetime
from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contestant',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('college', models.CharField(max_length=500)),
                ('points', models.IntegerField(default=0)),
                ('extra_time', models.DurationField(default=datetime.timedelta(0))),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('text', models.TextField(max_length=1500)),
                ('image', models.ImageField(blank=True, upload_to='')),
                ('correct_answer', models.CharField(max_length=500)),
                ('release_date', models.DateTimeField()),
                ('points', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PasswordResetModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash', models.CharField(default=contest.models.generate_random_string, max_length=10)),
                ('contestant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contest.Contestant')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Hint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(blank=True, max_length=500)),
                ('image', models.ImageField(blank=True, upload_to='')),
                ('release_date', models.DateTimeField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contest.Question')),
            ],
        ),
        migrations.AddField(
            model_name='contestant',
            name='answered_questions',
            field=models.ManyToManyField(to='contest.Question'),
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500)),
                ('time', models.DateTimeField()),
                ('contestant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contest.Contestant')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contest.Question')),
            ],
        ),
        migrations.CreateModel(
            name='ActivationModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash', models.CharField(default=contest.models.generate_random_string, max_length=10)),
                ('contestant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contest.Contestant')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
