from django.db import models

class Room(models.Model):
    # name of the room (used for indexing)
    name = models.CharField(max_length=100, primary_key=True)
    # users in the room 
    users = models.CharField(max_length=1000, default='[]')
    # host of the room
    host = models.CharField(max_length=100, default='')
    # scores for each player
    scores = models.CharField(max_length=1000, default='{}')

class Game(models.Model):
    # room this game is a part of
    room = models.OneToOneField(Room, on_delete=models.CASCADE)
    # time when the current game will be over
    end_time = models.CharField(max_length=1000, default='')
    # game board as an encoded JSON array
    board = models.CharField(max_length=5000, default='')
    # words submitted for this game
    submitted_words = models.CharField(max_length=10000, default='{}')
    # words for each user after game is over
    final_words = models.CharField(max_length=10000, default='{}')

