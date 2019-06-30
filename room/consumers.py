import json
import time

import channels
from django.contrib.auth import get_user_model
from channels.consumer import SyncConsumer
from asgiref.sync import async_to_sync

from .models import Room, Game
from .utils import BoggleGame

class RoomConsumer(SyncConsumer):
    boggleGame = BoggleGame()

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
            if "word" in loaded_data:
                word = loaded_data.get("word")
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
            elif "new_game" in loaded_data:
                self.game = Game()
                boggleGame = BoggleGame()
                myResponse = {
                    "type": "new_game",
                    "board": json.dumps(boggleGame.display_board),
                    "end_time": int(time.time() + (3 * 60) + 1)
                }
                new_event = {
                    "type": "new_game",
                    "text": json.dumps(myResponse)
                }
                async_to_sync(self.channel_layer.group_send)(
                    self.room_name,
                    new_event
                )
                    
    def word_submission(self, event):
        self.send({
            "type": "websocket.send",
            "text": event['text']
        })

    def new_game(self, event):
        self.send({
            "type": "websocket.send",
            "text": event['text']
        })

    def websocket_disconnect(self, event):
        self.remove_user_from_room()
        async_to_sync(self.channel_layer.group_discard)(self.room_name, self.channel_name)
        raise channels.exceptions.StopConsumer

    def notify_of_updated_userlist(self):
        new_event = {
            "type": "user_changes",
            "text": json.dumps({"type": "user_changes", "users": self.room.users})
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            new_event
        )

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
        users = json.loads(self.room.users)
        if (len(users) == 0):
            self.room.host = self.user
        users.append(self.user)
        self.room.users = json.dumps(sorted(users))
        self.room.save()
        self.notify_of_updated_userlist()

    def remove_user_from_room(self):
        print(f"{self.user} just left the room!")
        self.room = self.get_room(self.room_name)
        users = json.loads(self.room.users)
        users.remove(self.user)
        if self.room.host == self.user and len(users) > 0:
            self.room.host = users[0]
        self.room.users = json.dumps(sorted(users))
        self.room.save()
        self.notify_of_updated_userlist()


