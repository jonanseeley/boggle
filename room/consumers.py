import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
import channels

from .models import Room

class RoomConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("connected", event)
        room_name = self.scope['url_route']['kwargs']['name']
        user = self.scope['session'].get('username' or None)
        self.user = user

        room = await self.get_room(room_name, user)
        self.room = room
        self.room_name = room_name

        await self.channel_layer.group_add(
            room_name,
            self.channel_name
        )
        await self.send({
            "type": "websocket.accept"
        })
        await self.add_user_to_room()
        new_event = {
            "type": "user_changes",
            "text": json.dumps({"type": "user_changes", "users": self.room.users})
        }
        await self.channel_layer.group_send(
            self.room_name,
            new_event
        )

    async def user_changes(self, event):
        await self.send({
            "type": "websocket.send",
            "text": event["text"]
        })

    async def websocket_receive(self, event):
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
                await self.channel_layer.group_send(
                    self.room_name,
                    new_event
                )
            else:
                connected = loaded_data.get("text" or None)
                if connected != None:
                    print(f"{self.user} has joined!")

    async def word_submission(self, event):
        await self.send({
            "type": "websocket.send",
            "text": event['text']
        })

    async def websocket_disconnect(self, event):
        await self.remove_user_from_room()
        new_event = {
            "type": "user_changes",
            "text": json.dumps({"type": "user_changes", "users": self.room.users})
        }
        await self.channel_layer.group_send(
            self.room_name,
            new_event
        )
        print("disconnected", event)
        raise channels.exceptions.StopConsumer

    @database_sync_to_async
    # Grab room and append newcomer to the user list
    def get_room(self, room_name, username):
        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            room = Room(name=name, users=json.dumps([]))
            room.save()
        return room

    @database_sync_to_async
    def add_user_to_room(self):
        users = json.loads(self.room.users)
        users.append(self.user)
        self.room.users = json.dumps(users)
        self.room.save()

    @database_sync_to_async
    def remove_user_from_room(self):
        users = json.loads(self.room.users)
        print(f"{self.user} just left the room!")
        print(users)
        users.remove(self.user)
        print(users)
        self.room.users = json.dumps(users)
        self.room.save()

