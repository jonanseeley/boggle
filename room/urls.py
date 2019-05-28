from django.urls import path
from .views import (
    room_create_view,
    room_play_view
)

app_name = 'room'
urlpatterns = [
    path('<name>/', room_play_view)
]
