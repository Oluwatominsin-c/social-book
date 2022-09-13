from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Post, LikePost, FollowersCount

import re

# Create your views here.
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
    users = User.objects.all()

    new_users = [i for i in users if not FollowersCount.objects.filter(follower=user_object.username, user=i.username).exists()]
    new_users = [i for i in new_users if i != user_object]
    context = {
        "user_profile": user_profile,
        "posts": posts,
        "new_users": new_users,
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
