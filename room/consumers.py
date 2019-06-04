import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from .models import Room

class RoomConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("connected", event)
        room_name = self.scope['url_route']['kwargs']['name']
        user = self.scope['session'].get('username' or None)
        room = await self.get_room(room_name, user)
        self.room_name = room_name
        await self.channel_layer.group_add(
            room_name,
            self.channel_name
        )
        await self.send({
            "type": "websocket.accept"
        })

    async def websocket_receive(self, event):
        print("receive", event)
        front_data = event.get("text" or None)
        if front_data is not None:
            loaded_data = json.loads(front_data)
            word = loaded_data.get("word" or None)
            user = self.scope['session'].get('username' or None)
            myResponse = {
                "word": word,
                "user": user
            }
            new_event = {
                "type": "word_submission",
                "text": json.dumps(myResponse)
            }
            await self.channel_layer.group_send(
                self.room_name,
                new_event
            )

    async def word_submission(self, event):
        await self.send({
            "type": "websocket.send",
            "text": event['text']
        })

    async def websocket_disconnect(self, event):
        print("disconnected", event)

    @database_sync_to_async
    def get_room(self, room_name, username):
        try:
            room = Room.objects.get(name=room_name)
            users = json.loads(room.users)
            users.append(username)
            room.users = json.dumps(users)
        except Room.DoesNotExist:
            room = Room(name=name, users=json.dumps(users))
        room.save()
        return room
