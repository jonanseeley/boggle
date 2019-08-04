# Generated by Django 2.2.1 on 2019-07-01 00:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('room', '0003_room_host'),
    ]

    operations = [
        migrations.RenameField(
            model_name='game',
            old_name='endTime',
            new_name='end_time',
        ),
        migrations.RenameField(
            model_name='game',
            old_name='inProgress',
            new_name='in_progress',
        ),
        migrations.AddField(
            model_name='game',
            name='submitted_words',
            field=models.CharField(default='', max_length=10000),
            preserve_default=False,
        ),
    ]