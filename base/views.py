from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import Room, Topic, Message, User, Task
from .forms import RoomForm, UserForm, MyUserCreationForm, SummarizeForm
from googletrans import Translator
from .languages import LANGUAGES
from django.http import JsonResponse, HttpResponseForbidden
from .models import Message
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import requests
import google.generativeai as genai
from django.conf import settings
import re, os
from django.utils import timezone
import pytz
import uuid
import io
from PIL import Image
import base64
from dotenv import load_dotenv
load_dotenv() 

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, email=email, password=password)
        

        if user is not None:
            login(request, user)
            user.status = 'online'
            user_timezone = request.user.timezone  # Update this line based on your user model
            request.session['user_timezone'] = user_timezone
            timezone.activate(user_timezone)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exit')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    User.status = 'offline'
    return redirect('home')


def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            user_timezone = request.user.timezone  # Update this line based on your user model
            request.session['user_timezone'] = user_timezone
            timezone.activate(user_timezone)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'base/login_register.html', {'form': form})


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(
        Q(room__topic__name__icontains=q))[0:3]

    context = {'rooms': rooms, 'topics': topics,
               'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)

@login_required(login_url='login')
def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()
    
    # Retrieve user's timezone from their profile, default to UTC if not set
    user_tz = pytz.timezone(request.user.timezone if request.user.timezone else 'UTC')
    
    # Convert message timestamps to user's timezone
    for message in room_messages:
        message.created = timezone.localtime(message.created, user_tz)
        message.updated = timezone.localtime(message.updated, user_tz)

    if request.method == 'POST':
        body = request.POST.get('body')
        if body.startswith('/s'):  # Bot command detected
            form = SummarizeForm(request.POST)
            if form.is_valid():
                start_time = form.cleaned_data['start_time']
                end_time = form.cleaned_data['end_time']

                # Ensure start_time and end_time are timezone-aware
                if timezone.is_naive(start_time):
                    start_time = user_tz.localize(start_time)
                else:
                    start_time = start_time.astimezone(user_tz)
                
                if timezone.is_naive(end_time):
                    end_time = user_tz.localize(end_time)
                else:
                    end_time = end_time.astimezone(user_tz)

                # Convert start and end time to UTC for querying messages
                start_time_utc = start_time.astimezone(pytz.UTC)
                end_time_utc = end_time.astimezone(pytz.UTC)

                summary = summarize_chat(room_messages, start_time_utc, end_time_utc)
                
                chatbot_user = User.objects.get(username='chatbot')
                # relative_image_path = generate_image_from_summary(summary)
                
                Message.objects.create(
                    user=chatbot_user,
                    room=room,
                    body=f"Summary:\n{summary}",
                    # image=relative_image_path,
                )
            return redirect('room', pk=room.id)
        else:  # Regular message
            message = Message.objects.create(
                user=request.user,
                room=room,
                body=body
            )
            room.participants.add(request.user)
            return redirect('room', pk=room.id)

    else:
        form = SummarizeForm()

    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants,
        'form': form,
    }
    return render(request, 'base/room.html', context)


genai_api_key = os.getenv('GENAI_API_KEY')

genai.configure(api_key=genai_api_key)

def summarize_chat(messages, start_time, end_time):
    # Convert to timezone-aware datetime if needed
    start_time = timezone.make_aware(start_time) if timezone.is_naive(start_time) else start_time
    end_time = timezone.make_aware(end_time) if timezone.is_naive(end_time) else end_time

    # Filter messages within the given time frame
    messages_to_summarize = messages.filter(
        created__gte=start_time, 
        created__lte=end_time
    )

    # Combine the messages into a single text
    text = "\n".join([f"{msg.created.strftime('%Y-%m-%d %H:%M:%S')} - {msg.body}" for msg in messages_to_summarize])
    
    if not text.strip():
        return "No content to summarize."
   
    model = genai.GenerativeModel("gemini-pro")
    chat = model.start_chat()
        
    prompt = f"Please summarize the content of this chat:\n{text}"
        
    response = chat.send_message(prompt)
    
    print(response)
        
    try:
        summarized_text = response.text  # Accessing the text summary assuming 'text' is an attribute
    except AttributeError:
        # Handle the case where 'text' is not an attribute of the response
        summarized_text = "Could not retrieve summarized text."

    return summarized_text
    
import sqlite3
print(sqlite3.sqlite_version)    

image_api_key = os.getenv('IMAGE_API_KEY')

def generate_image_from_summary(prompt):
    api_url = "https://modelslab.com/api/v6/images/text2img"
    api_key = image_api_key

    payload = {
        "key": api_key,
        "model_id": "sdxl",
        "prompt": prompt,
        "width": "256",
        "height": "256",
        "samples": "1",
        "num_inference_steps": "41",
        "guidance_scale": 7.5,
        "scheduler": "UniPCMultistepScheduler",
        "seed": None,
        "webhook": None,
        "track_id": None
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        response_json = response.json()
        print("API Response:", response_json)  # Debugging line
        
        if 'output' in response_json:
            image_url = response_json['output'][0]
            image_response = requests.get(image_url)

            if image_response.status_code == 200:
                image = Image.open(io.BytesIO(image_response.content))
                save_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                # Sanitize and create filename
                max_length = 128
                sanitized_prompt = re.sub(r'[\\/:*?"<>|,]+', '', prompt)
                truncated_prompt = sanitized_prompt[:max_length]
                filename = re.sub(r'\s+', '_', truncated_prompt) + '.png'

                outputfile = os.path.join(save_dir, filename)
                print("Saving image to:", outputfile)  # Debugging line
                image.save(outputfile, 'PNG')

                return f'images/{filename}'
            else:
                print("Failed to download image from URL:", image_url)
    else:
        print("API Request failed with status:", response.status_code)

    return None


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms,
               'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        room = Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )

        room.participants.add(request.user)
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    return render(request, 'base/update-user.html', {'form': form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})


def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})



def translation(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        source_language = request.POST.get('source_language')
        target_language = request.POST.get('target_language')
        
        translation = Translator()
        
        result = translation.translate(text, src=source_language, dest=target_language)
        
        return JsonResponse({'translate_text': result.text})
    return render(request, 'base/translation.html', {'languages': LANGUAGES})

translator = Translator()

def translate_message(request, message_id, target_lang):
    message = Message.objects.get(id=message_id)
    translated_text = translator.translate(message.body, dest=target_lang).text
    message.translated_body = translated_text
    message.save()
    return JsonResponse({'translated_text': translated_text})

def restore_message(request, message_id):
    message = Message.objects.get(id=message_id)
    original_text = message.body
    message.translated_body = None
    message.save()
    return JsonResponse({'original_text': original_text})

@csrf_exempt
def set_timezone(request):
    if request.method == 'POST':
        user_timezone = request.POST.get('timezone')
        request.session['user_timezone'] = user_timezone
        timezone.activate(user_timezone)
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "failed"})


@login_required(login_url='login')
def task_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.user not in room.participants.all():
        messages.error(request, "You are not allowed to view tasks.")
        return redirect('home')
    
    if request.method == 'POST':
        if request.user == room.host:
            task_title = request.POST.get('task_title')
            task_description = request.POST.get('task_description')
            Task.objects.create(title=task_title, description=task_description, user=request.user, room=room)
            messages.success(request, "Task added successfully!")  # Thông báo thành công khi thêm task
        else:
            return HttpResponseForbidden("You are not allowed to add tasks.")
        return redirect('task_view', room_id=room.id)

    tasks = Task.objects.filter(room=room)
    return render(request, 'base/task.html', {'tasks': tasks, 'room': room})

@login_required(login_url='login')
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Kiểm tra xem người dùng có phải là thành viên của phòng hay không
    if request.user not in task.room.participants.all():
        messages.error(request, "You are not allowed to mark tasks as completed.")
        return redirect('home')
    
    if request.user not in task.completed_by.all():
        task.completed_by.add(request.user)  # Thêm người dùng vào danh sách hoàn thành
        messages.success(request, "Task marked as completed!")  # Thông báo hoàn thành task
    else:
        task.completed_by.remove(request.user)  # Xóa người dùng khỏi danh sách hoàn thành
        messages.success(request, "Task unmarked as completed!")  # Thông báo bỏ đánh dấu hoàn thành
    
    task.save()
    return redirect('task_view', room_id=task.room.id)

@login_required(login_url='login')
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.user != task.room.host:
        return HttpResponseForbidden("You are not allowed to delete tasks.")
    
    task.delete()
    messages.success(request, "Task deleted successfully!")  # Thông báo khi task bị xóa
    return redirect('task_view', room_id=task.room.id)


@login_required(login_url='login')
def callRoom(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # Kiểm tra xem người dùng có phải là participant không
    if request.user not in room.participants.all():
        messages.error(request, "You are not allowed to join this call.")
        return redirect('home')

    # Kiểm tra xem đã có call room chưa
    if room.call_room_id is None:
        room.call_room_id = str(uuid.uuid4())  # Tạo ID duy nhất cho cuộc gọi
        room.save()

    return render(request, 'base/call_room.html', {'room': room})

@login_required(login_url='login')
def get_commands(request):
    commands = [
        {"command": "/b", "description": "Call the Bot to summarize chat"},
    ]
    return JsonResponse(commands, safe=False)


