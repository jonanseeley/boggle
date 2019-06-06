from django.db import models

class Room(models.Model):
    # name of the room (used for indexing)
    name  = models.CharField(max_length=100, primary_key=True)
    # users in the room 
    users = models.CharField(max_length=1000)

class Game(models.Model):
    # room this game is a part of
    room = models.OneToOneField(Room, on_delete=models.CASCADE)
    # boolean describing if the game is in progress
    inProgress = models.BooleanField(default=False)
    # time when the current game will be over (ignore if inProgress is false)
    endTime = models.DateTimeField(null=True)
    # game board as an encoded JSON array
    board = models.CharField(max_length=5000)

class WordGuess(models.Model):
    # room the guess was made in
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # user who made the guess
    user = models.CharField(max_length=100)
