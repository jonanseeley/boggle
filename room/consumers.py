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
            # Game exists, send data to show to client
            self.game = self.room.game
            self.send_json({
                    "msg_type": "new_game",
                    "board": self.game.board,
                    "end_time": self.game.end_time,
                    "words": json.dumps(self.get_words()),
                    "scores": self.room.scores
            })
        else:
            self.game = None

        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.add_user_to_room()


    def update_room(self):
        self.room = self.get_room()
        if hasattr(self.room, "game"):
            self.game = self.room.game

    def get_words(self):
        if not self.game:
            return []
        # Load all submitted words, and return just the ones from the client
        submitted_words = json.loads(self.game.submitted_words)
        if self.user not in submitted_words:
            submitted_words[self.user] = []
            self.game.submitted_words = json.dumps(submitted_words)
            self.game.save()
            return []
        return submitted_words[self.user]


    def receive_json(self, content):
        print("received", content)
        command = content.get("command", None)
        if command is not None:
            self.update_room()
            if command == "submitted_word":
                self.received_word(content["word"])
            elif command == "new_game":
                self.new_game()
            elif command == "game_finished":
                self.game_finished()


    def new_game(self):
        if not self.game_running() and self.user == self.room.host:
            print("New game created")
            if self.game:
                self.game.delete()
            deadline = int(time.time() + (3 * 60) + 1)
            board = json.dumps(generate_board())
            submitted_words = {user: [] for user in json.loads(self.room.users)}
            self.game = Game(room=self.room, end_time=str(deadline), 
                    board=board, submitted_words=json.dumps(submitted_words),
                    final_words=json.dumps({}))
            self.game.save()
            async_to_sync(self.channel_layer.group_send) (
                self.room_name,
                {
                    "type": "boggle.newgame",
                    "board": board,
                    "end_time": deadline,
                    "words": json.dumps(self.get_words()),
                    "scores": self.room.scores
                }
            )


    def game_running(self):
        return self.game and int(self.game.end_time) > time.time()


    def received_word(self, word):
        board = json.loads(self.game.board)
        if not self.game_running():
            self.send_json({
                "msg_type": "invalid_word",
                "reason": f"You can't submit words when the game isn't running!"
            })
        elif check_word(board, word):
            word_list = json.loads(self.game.submitted_words)
            if self.user in word_list:
                if word not in word_list[self.user]:
                    word_list[self.user].append(word)
                else:
                    self.send_json({
                        "msg_type": "invalid_word",
                        "reason": f"You already submitted {word}!"
                    })
                    return
            else:
                word_list[self.user] = [word]
            self.game.submitted_words = json.dumps(word_list)
            self.game.save()
            self.send_json({
                "msg_type": "valid_word",
                "word": word
            })
        else:
            self.send_json({
                "msg_type": "invalid_word",
                "reason": f"{word} is not a valid word for this board!"
            })


    def game_finished(self):
        if len(json.loads(self.game.final_words)) == 0:
            # Build set of common_words
            submitted_words = json.loads(self.game.submitted_words)
            common_words = set()
            users = list(submitted_words.keys())
            for i in range(len(users)-1):
                for j in range(i+1, len(users)):
                    # Common words between user i and user j
                    useri_words = submitted_words[users[i]]
                    userj_words = submitted_words[users[j]]
                    words = set(useri_words).intersection(set(userj_words))
                    common_words = common_words.union(words)
            final_words = dict()
            rejected_words = dict()
            scores = json.loads(self.room.scores)
            for user, words in submitted_words.items():
                # Remove the words that are common from each user's word list
                wordSet = set(words)
                final_words[user] = list(wordSet.difference(common_words))
                rejected_words[user] = list(wordSet.intersection(common_words))
                word_scores = [word_score(word) for word in final_words[user]]
                scores[user] += sum(word_scores)
            self.game.final_words = json.dumps(final_words)
            self.game.save()
            self.room.scores = json.dumps(scores)
            self.room.save()
            async_to_sync(self.channel_layer.group_send) (
                self.room_name,
                {
                    "type": "boggle.scoreupdate",
                    "scores": self.room.scores,
                    "rejected_words": json.dumps(rejected_words),
                    "accepted_words": self.game.final_words
                }
            )


    def disconnect(self, event):
        self.remove_user_from_room()
        async_to_sync(self.channel_layer.group_discard)(self.room_name, 
                self.channel_name)
        raise channels.exceptions.StopConsumer


    def get_room(self):
        try:
            room = Room.objects.get(name=self.room_name)
        except Room.DoesNotExist:
            room = Room(name=name)
            room.save()
        return room


    def add_user_to_room(self):
        print(f"{self.user} just joined the room!")
        users = json.loads(self.room.users)
        scores = json.loads(self.room.scores)
        if (len(users) == 0):
            self.room.host = self.user
        users.append(self.user)
        scores[self.user] = 0
        self.room.users = json.dumps(sorted(users))
        self.room.scores = json.dumps(scores)
        self.room.save()
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                "type": "boggle.userchanges",
                "users": self.room.users,
                "host": self.room.host
            }
        )
        print(f"{self.room.host} is the host")


    def remove_user_from_room(self):
        print(f"{self.user} just left the room!")
        users = json.loads(self.room.users)
        scores = json.loads(self.room.scores)
        users.remove(self.user)
        scores.pop(self.user, None)
        if self.room.host == self.user and len(users) > 0:
            self.room.host = users[0]
        self.room.users = json.dumps(sorted(users))
        self.room.scores = json.dumps(scores)
        self.room.save()
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                "type": "boggle.userchanges",
                "users": self.room.users,
                "host": self.room.host
            }
        )
        print(f"{self.room.host} is the host")


    def boggle_userchanges(self, event):
        self.send_json(
            {
                "msg_type": "user_changes",
                "users": event["users"],
                "host": json.dumps(event["host"] == self.user)
            }
        )


    def boggle_newgame(self, event):
        self.room = self.get_room()
        self.game = self.room.game
        self.send_json(
            {
                "msg_type": "new_game",
                "board": event["board"],
                "end_time": event["end_time"],
                "words": event["words"],
                "scores": event["scores"]
            }
        )


    def boggle_scoreupdate(self, event):
        accepted_words = json.loads(event["accepted_words"])
        rejected_words = json.loads(event["rejected_words"])
        self.send_json({
            "msg_type": "score_update",
            "scores": event["scores"],
            "rejected_words": json.dumps(rejected_words[self.user]),
            "accepted_words": json.dumps(accepted_words[self.user])
        })
