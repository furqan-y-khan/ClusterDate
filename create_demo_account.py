#!/usr/bin/env python
import os
import sys
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "super_dating_app.settings")
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
import random
from core.models import Profile, Interest
from payments.models import Plan, Subscription
from mainstream.models import MainstreamProfile

# Demo account credentials
EMAIL = 'furqaniitp@gmail.com'
PASSWORD = 'Furqan@309'
USERNAME = 'furqan_demo'

# Helper function to get a random list of elements from a list
def get_random_elements(lst, num_elements):
    return random.sample(lst, min(num_elements, len(lst)))

def create_demo_account():
    # Check if user already exists
    if User.objects.filter(email=EMAIL).exists():
        print(f"User with email {EMAIL} already exists. Skipping account creation.")
        user = User.objects.get(email=EMAIL)
    else:
        # Create the user
        user = User.objects.create_user(
            username=USERNAME,
            email=EMAIL,
            password=PASSWORD
        )
        user.first_name = "Furqan"
        user.last_name = "Demo"
        user.is_active = True
        user.save()
        
        print(f"Created user: {user.username}")
        
        # Create or update profile
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)
        
        # Update profile fields
        profile.bio = "Hi, I'm a demo account for testing the dating app features. I enjoy traveling, reading, and trying new cuisines."
        profile.birth_date = timezone.now().date() - timezone.timedelta(days=365 * 30)  # 30 years old
        profile.gender = "M"
        profile.location = "New York, NY"
        profile.min_age_preference = 25
        profile.max_age_preference = 40
        profile.distance_preference = 50
        profile.save()
        
        print("Profile created/updated")
        
        # Add interests
        interests = [
            "Travel", "Reading", "Cooking", "Hiking", "Photography", 
            "Music", "Movies", "Technology", "Sports", "Art"
        ]
        
        for interest_name in interests:
            interest, created = Interest.objects.get_or_create(name=interest_name)
            profile.interests.add(interest)
        
        print("Interests added")
        
        # Create mainstream profile
        try:
            mainstream_profile = MainstreamProfile.objects.get(profile=profile)
        except MainstreamProfile.DoesNotExist:
            mainstream_profile = MainstreamProfile.objects.create(profile=profile)
        
        # Update mainstream profile fields
        mainstream_profile.relationship_status = "SINGLE"
        mainstream_profile.looking_for = "DATING"
        mainstream_profile.education_level = "BACHELORS"
        mainstream_profile.occupation = "Software Engineer"
        mainstream_profile.interested_in_gender = "F"
        mainstream_profile.has_children = False
        mainstream_profile.wants_children = True
        mainstream_profile.smoker = False
        mainstream_profile.drinker = True
        mainstream_profile.save()
        
        print("Mainstream profile created/updated")
        
        # Add a subscription (if plans exist)
        try:
            # Get a premium plan if available
            plan = Plan.objects.filter(is_active=True).order_by('-price').first()
            if plan:
                # Create subscription
                subscription = Subscription.objects.create(
                    user=user,
                    plan=plan,
                    status='active',
                    start_date=timezone.now(),
                    stripe_subscription_id='demo_subscription',
                    stripe_customer_id='demo_customer'
                )
                print(f"Added premium subscription: {plan.name}")
        except Exception as e:
            print(f"Couldn't add subscription: {str(e)}")
    
    return user

if __name__ == "__main__":
    print("Creating demo account...")
    user = create_demo_account()
    print(f"Demo account created/updated successfully! Username: {user.username}, Email: {EMAIL}")
    print("You can now log in with these credentials to test the application.") 