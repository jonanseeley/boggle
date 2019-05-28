from django import forms

class RoomForm(forms.Form):
    username  = forms.CharField(label="Username", max_length=100)
    room_name = forms.CharField(label="Room name", max_length=100)
