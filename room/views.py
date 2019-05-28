import json

from django.shortcuts import render, redirect, get_object_or_404
from .forms import RoomForm
from .models import Room

def room_create_view(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            username  = form.cleaned_data['username']
            request.session['username'] = username
            room_name = form.cleaned_data['room_name']
            return redirect('/room/' + room_name + "/")
    else:
        print(request.session.get('username' or None))
        form = RoomForm()
    return render(request, "room/room_create.html", {'form': form})

def room_play_view(request, name):
    username = request.session.get('username' or None)
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
    context = {'room': room, 'user_list': users}
    return render(request, "room/room_play.html", context)

