# Generated by Django 2.2.1 on 2019-05-27 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('users', models.CharField(max_length=200)),
            ],
        ),
    ]