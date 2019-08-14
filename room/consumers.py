import json
import time

import channels
from django.contrib.auth import get_user_model
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync

from .models import Room, Game
from .utils import *

class RoomConsumer(JsonWebsocketConsumer):

    def connect(self):
        self.accept()
        print("connected")
        self.room_name = self.scope['url_route']['kwargs']['name']
        self.room = self.get_room()
        self.user = self.scope['session'].get('username', "Anonymous")
        if hasattr(self.room, "game"):
            self.game = self.room.game
            self.send_json(
                {
                    "msg_type": "new_game",
                    "board": self.game.board,
                    "end_time": self.game.end_time,
                    "words": json.dumps(self.get_words())
                }
            )
        else:
            self.game = None

        async_to_sync(self.channel_layer.group_add) (
            self.room_name,
            self.channel_name
        )
        self.add_user_to_room()


    def get_words(self):
        if not self.game:
            return []
        submitted_words = json.loads(self.game.submitted_words)
        if self.user not in submitted_words:
            submitted_words[self.user] = []
            self.game.submitted_words = json.dumps(submitted_words)
            self.game.save()
            return []
        return submitted_words[self.user]


    def receive_json(self, content):
        print("receive", content)
        command = content.get("command", None)
        if command is not None:
            if command == "submitted_word":
                self.received_word(content["word"])
            elif command == "new_game":
                self.new_game()
            elif command == "game_finished":
                self.game_finished()


    def new_game(self):
        if not self.game or int(self.room.game.end_time) < time.time():
            deadline = int(time.time() + (3 * 60) + 1)
            board = json.dumps(generate_board())
            print("New game created")
            submitted_words = {user: [] for user in json.loads(self.room.users)}
            self.game.delete()
            self.game = Game(room=self.room, end_time=str(deadline), 
                    board=board, submitted_words=json.dumps(submitted_words))
            self.game.save()
            async_to_sync(self.channel_layer.group_send) (
                self.room_name,
                {
                    "type": "boggle.newgame",
                    "board": board,
                    "end_time": deadline,
                    "words": json.dumps(self.get_words())
                }
            )


    def received_word(self, word):
        board = json.loads(self.game.board)
        if check_word(board, word):
            word_list = json.loads(self.game.submitted_words)
            if self.user in word_list:
                word_list[self.user].append(word)
            else:
                word_list[self.user] = [word]
            self.game.submitted_words = json.dumps(word_list)
            self.game.save()
            self.send_json(
                {
                    "msg_type": "valid_word",
                    "word": word
                }
            )
        else:
            self.send_json(
                {
                    "msg_type": "invalid_word",
                    "word": word
                }
            )


    def game_finished(self):
        ''' 
        Check if the final words have been calculated yet
        If they haven't, go ahead and remove common words from each player's
            word list
        Calculate score for each player
            Use that score to update the scores for each player in the room
            Send the score to each player 
        '''
        print(self.game.final_words)
        if not self.game.final_words:
            # Build set of common_words
            submitted_words = json.loads(self.game.submitted_words)
            common_words = set()
            users = submitted_words.keys()
            for i in range(len(users)-1):
                for j in range(i+1, len(users)):
                    # Common words between user i and user j
                    words = set(users[i]).intersection(set(users[j]))
                    common_words = common_words.union(words)
            final_words = dict()
            for user, words in submitted_words.items():
                final_words[user] = list(set(words).difference(common_words))


    def disconnect(self, event):
        self.remove_user_from_room()
        async_to_sync(self.channel_layer.group_discard)(self.room_name, 
                self.channel_name)
        raise channels.exceptions.StopConsumer


    def get_room(self):
        try:
            room = Room.objects.get(name=self.room_name)
        except Room.DoesNotExist:
            room = Room(name=name, users=json.dumps([]))
            room.save()
        return room


    def add_user_to_room(self):
        print(f"{self.user} just joined the room!")
        users = json.loads(self.room.users)
        if (len(users) == 0):
            self.room.host = self.user
        users.append(self.user)
        self.room.users = json.dumps(sorted(users))
        self.room.save()
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                "type": "boggle.userchanges",
                "users": self.room.users
            }
        )
        print(f"{self.room.host} is the host")

    def remove_user_from_room(self):
        print(f"{self.user} just left the room!")
        users = json.loads(self.room.users)
        users.remove(self.user)
        if self.room.host == self.user and len(users) > 0:
            self.room.host = users[0]
        self.room.users = json.dumps(sorted(users))
        self.room.save()
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                "type": "boggle.userchanges",
                "users": self.room.users
            }
        )
        print(f"{self.room.host} is the host")


    def boggle_userchanges(self, event):
        self.send_json(
            {
                "msg_type": "user_changes",
                "users": event["users"]
            }
        )


    def boggle_newgame(self, event):
        self.send_json(
            {
                "msg_type": "new_game",
                "board": event["board"],
                "end_time": event["end_time"],
                "words": event["words"]
            }
        )

