from django.db import models

class Room(models.Model):
    # name of the room (used for indexing)
    name  = models.CharField(max_length=100, primary_key=True)
    # users in the room 
    users = models.CharField(max_length=1000)
