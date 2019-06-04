import json
from django.contrib.auth import get_user_model
from channels.consumer import SyncConsumer
import channels
from asgiref.sync import async_to_sync

from .models import Room

class RoomConsumer(SyncConsumer):
    def websocket_connect(self, event):
        print("connected", event)
        room_name = self.scope['url_route']['kwargs']['name']
        self.room_name = room_name
        user = self.scope['session'].get('username' or None)
        if user == None:
            user = "Anonymous"
        self.user = user
        room = self.get_room(room_name)
        self.room = room

        async_to_sync(self.channel_layer.group_add)(
            room_name,
            self.channel_name
        )
        self.send({
            "type": "websocket.accept"
        })
        self.add_user_to_room()
        new_event = {
            "type": "user_changes",
            "text": json.dumps({"type": "user_changes", "users": self.room.users})
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            new_event
        )

    def user_changes(self, event):
        self.send({
            "type": "websocket.send",
            "text": event["text"]
        })

    def websocket_receive(self, event):
        print("receive", event)
        front_data = event.get("text" or None)
        if front_data is not None:
            loaded_data = json.loads(front_data)
            word = loaded_data.get("word" or None)
            if word != None:
                myResponse = {
                    "type": "new_word",
                    "word": word,
                    "user": self.user
                }
                new_event = {
                    "type": "word_submission",
                    "text": json.dumps(myResponse)
                }
                async_to_sync(self.channel_layer.group_send)(
                    self.room_name,
                    new_event
                )
            else:
                connected = loaded_data.get("text" or None)
                if connected != None:
                    print(f"{self.user} has joined!")
                    
    def word_submission(self, event):
        self.send({
            "type": "websocket.send",
            "text": event['text']
        })

    def websocket_disconnect(self, event):
        self.remove_user_from_room()
        new_event = {
            "type": "user_changes",
            "text": json.dumps({"type": "user_changes", "users": self.room.users})
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            new_event
        )
        print("disconnected", event)
        raise channels.exceptions.StopConsumer

    # Grab room and append newcomer to the user list
    def get_room(self, room_name):
        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            room = Room(name=name, users=json.dumps([]))
            room.save()
        return room

    def add_user_to_room(self):
        print(f"{self.user} just joined the room!")
        self.room = self.get_room(self.room_name)
        print(self.room.users)
        users = json.loads(self.room.users)
        users.append(self.user)
        print(users)
        self.room.users = json.dumps(sorted(users))
        self.room.save()
        print(self.room.users)

    def remove_user_from_room(self):
        print(f"{self.user} just left the room!")
        self.room = self.get_room(self.room_name)
        print(self.room.users)
        users = json.loads(self.room.users)
        users.remove(self.user)
        self.room.users = json.dumps(sorted(users))
        self.room.save()
        print(self.room.users)

