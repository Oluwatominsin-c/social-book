from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Post, LikePost, FollowersCount
from django.forms.models import model_to_dict

import re
import pprintpp
import json
import random
from itertools import chain

# Regex for email validation
regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')

def isValid(email):
    if re.fullmatch(regex, email):
      return True
    else:
      return False

@login_required(login_url="signin")
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    posts = Post.objects.all()

    feed = [] 
    for i in posts:
        if FollowersCount.objects.filter(user=i.user, follower=request.user.username).exists():
            feed.append(i)
        if i.user == request.user.username:
            feed.append(i)

    # User Suggestion
    users = User.objects.all()
    user_following = FollowersCount.objects.filter(follower=request.user.username)
    print(users)
    print(user_following)

    user_following_objects = []

    for user in user_following:
        _user = User.objects.get(username=user.user)
        user_following_objects.append(_user)
    print(user_following_objects)
    user_suggestions = [x for x in list(users) if (x not in user_following_objects) and (x != user_object)]
    

    random.shuffle(user_suggestions)

    user_suggestions_ids = []
    user_suggestion_list = []

    for user in user_suggestions:
        user_suggestions_ids.append(user.id)
    for ids in user_suggestions_ids:
        profiles = Profile.objects.filter(id_user=ids)
        if profiles:
            user_suggestion_list.append(profiles)
    print(user_suggestions_ids)
    print(user_suggestion_list)

    suggestions_profile_list = list(chain(*user_suggestion_list))
    print(suggestions_profile_list)
    
    # Shuffle user_suggestions list

    context = {
        "user_profile": user_profile,
        "posts": feed,
        "suggestions_username_profile_list": suggestions_profile_list[:4]
        }

    
    return render(request, "index.html", context)

def signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        # check if blank
        if not all([username, email, password1, password2]):
            messages.info(request, "Form still has blank spaces")
            return redirect("signup")
        
        # validations
        if len(username) < 5:
            messages.info(request, "username too short")
            return redirect("signup")
        if len(password1) < 8:
            messages.info(request, "password too short")
            return redirect("signup")


        if password1 == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email Taken")
                return redirect("signup")
            elif User.objects.filter(username=username).exists():
                messages.info(request, "Username Taken")
                return redirect("signup")
            else:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()

                # log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password1)
                auth.login(request, user_login)

                # create new Profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect("settings")
        else:
            messages.info(request, "Passwords Do Not Match")
            return redirect("signup")
    else:
        return render(request, "signup.html")

def signin(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        # check if blank
        if not all([username, password]):
            messages.info(request, "Form still has blank spaces")
            return redirect("signin")
        
        user = auth.authenticate(username=username, password=password)

        if user:
            auth.login(request, user)
            return redirect("/")
        else:
            messages.info(request, "Invalid Credentials")
            return redirect("signin")
    else:
        return render(request, "signin.html")

@login_required(login_url="signin")
def settings(request):
    user_profile = Profile.objects.get(user=request.user)  
    user = User.objects.get(username=request.user.username)

    if request.method == "POST":
        email = request.POST["email"]      
        bio = request.POST["bio"]
        location = request.POST["location"]
        image = request.FILES.get("image")
        firstname = request.POST["firstname"]
        lastname = request.POST["lastname"] 

        # check if form was filed
        if not image:
            image = user_profile.profileimg
        if not firstname:
            messages.info(request, "First name cannot be blank")
            return redirect("settings")
        if not lastname:
            messages.info(request, "Last name cannot be blank")
            return redirect("settings")
        if not email:
            messages.info(request, "Email cannot be blank")
            return redirect("settings")
            
        if email != user.email:
            if isValid(email):
                if User.objects.filter(email=email).exists():
                    messages.info(request, "Email Taken")
                    return redirect("settings")
            else:
                messages.info(request, "Invalid Email")
                return redirect("settings")
        
        user_profile.profileimg = image
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()

        user.email = email
        user.first_name = firstname
        user.last_name = lastname
        user.save()
        return redirect("settings")
    else:
        return render(request, "setting.html", {"context": user_profile})

@login_required(login_url="signin")
def logout(request):
    auth.logout(request)
    return redirect('signin')

@login_required(login_url="signin")
def post(request):
    if request.method == "POST":
        user = request.user.username
        image = request.FILES.get("image_upload")
        caption = request.POST["caption"]

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect("/")
    else:
        return redirect('/')

@login_required(login_url="signin")
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    profile_object = Profile.objects.get(user=user_object)
    posts = Post.objects.filter(user=pk)
    len_posts = len(posts)

    follower = request.user.username
    user = pk

    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button = "Unfollow"
    
    else:
        button = "Follow"
        
    follwers_count = len(FollowersCount.objects.filter(user=user))
    following_count = len(FollowersCount.objects.filter(follower=user))
    context = {
        "user_object": user_object,
        "profile_object": profile_object,
        "posts": posts,
        "len_posts": len_posts,
        "button": button,
        "follwers_count": follwers_count,
        "following_count": following_count
    }
    return render(request, "profile.html", context)

@login_required(login_url="signin")
def follow(request):
    if request.method == "POST":
        user = request.POST["user"]
        follower = request.POST["follower"]

        if FollowersCount.objects.filter(user=user, follower=follower).first():
            delete_follower = FollowersCount.objects.get(user=user, follower=follower)
            delete_follower.delete()
            return redirect("profile/" + user)
        else:
            new_follower = FollowersCount.objects.create(user=user, follower=follower)
            new_follower.save()
            return redirect("profile/" + user)

    else:
        return redirect("/")

@login_required(login_url="signin")
def like_post(request):
    username = request.user.username
    post_id = request.GET.get("post_id")

    post = Post.objects.get(id=post_id)
    
    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    
    if not like_filter:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        
        post.likes += 1
        post.save()
        return redirect("/")
    else:
        like_filter.delete()

        post.likes -= 1
        post.save()
        return redirect("/")

@login_required(login_url="signin")
def search(request):
    current_user = User.objects.get(username=request.user.username)
    current_user_profile = Profile.objects.get(user=current_user)

    if request.method == "POST":
        username = request.POST["username"]
        if User.objects.filter(username=username).exists():
            user = User.objects.filter(username=username)
            user_profile = []

            if len(user) == 1:
                one_user = User.objects.get(username=username)
                profile = Profile.objects.get(user=one_user)
                user_profile.append(profile)
            else:
                for i in user:
                    profile = Profile.objects.get(user=i)
                    user_profile.append(profile)

            context = {
            "user_searched": username,
            "user_profile": current_user_profile,
            "username_profile_list": user_profile
            }
            return render(request, "search.html", context)
        else:
            context = {
            "user_profile": current_user_profile
            }
            return render(request, "search.html", context)
    else:
        context = {
        "user_profile": current_user_profile
        }
        return render(request, "search.html", context)