from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.registerPage, name="register"),

    path('', views.home, name="home"),
    path('room/<str:pk>/', views.room, name="room"),
    path('profile/<str:pk>/', views.userProfile, name="user-profile"),

    path('create-room/', views.createRoom, name="create-room"),
    path('update-room/<str:pk>/', views.updateRoom, name="update-room"),
    path('delete-room/<str:pk>/', views.deleteRoom, name="delete-room"),
    path('delete-message/<str:pk>/', views.deleteMessage, name="delete-message"),

    path('update-user/', views.updateUser, name="update-user"),

    path('topics/', views.topicsPage, name="topics"),
    path('activity/', views.activityPage, name="activity"),
    
    path('translate/', views.translation, name="translate_text"),

    path('translate-message/<int:message_id>/<str:target_lang>/', views.translate_message, name='translate-message'),
    path('restore-message/<int:message_id>/', views.restore_message, name='restore-message'),
    path('set-timezone/', views.set_timezone, name='set-timezone'),
    
    path('room/<int:room_id>/tasks/', views.task_view, name='task_view'),
    path('tasks/toggle/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    
    path('call-room/<int:room_id>/', views.callRoom, name='call_room'),
    path('get-commands/', views.get_commands, name='get_commands'),
]
