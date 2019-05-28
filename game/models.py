from django.db import models

class Game(models.Model):
    # time when the game will end
    end_time      = models.DateTimeField()
    # all of the words the users have guessed
    words_guessed = models.CharField(max_length=10000)


