from django.db import models

'''
class RoomManager(models.Manager):
    def get_or_new(self, room_name, username):
        users = [username]
        try:
            room = Room.objects.get(name=name)
            users = json.loads(room.users)
            users.append(username)
            room.users = json.dumps(users)
            room.save()
        except Room.DoesNotExist:
            room = Room(name=name, users=json.dumps(users))
            room.save()
'''


class Room(models.Model):
    # name of the room (used for indexing)
    name  = models.CharField(max_length=100, primary_key=True)
    # users in the room 
    users = models.CharField(max_length=1000)
    # time when the game will end
    end_time      = models.DateTimeField()
    # all of the words the users have guessed
    words_guessed = models.CharField(max_length=10000)
