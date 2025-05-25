from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile, Interest, Match, Like
from datetime import date, timedelta
import math


class ProfileModelTests(TestCase):
    """Tests for the Profile model"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpassword'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword'
        )
        
        # Profile should be auto-created by signal
        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile
        
        # Update profile data
        self.profile1.bio = "Test bio for user 1"
        self.profile1.birth_date = date(1990, 1, 1)
        self.profile1.gender = 'M'
        self.profile1.latitude = 40.7128
        self.profile1.longitude = -74.0060
        self.profile1.save()
        
        self.profile2.bio = "Test bio for user 2"
        self.profile2.birth_date = date(1992, 2, 2)
        self.profile2.gender = 'F'
        self.profile2.latitude = 34.0522
        self.profile2.longitude = -118.2437
        self.profile2.save()
        
        # Create interests
        self.interest1 = Interest.objects.create(name="Music", category="Entertainment")
        self.interest2 = Interest.objects.create(name="Hiking", category="Outdoors")
        
        # Add interests to profiles
        self.profile1.interests.add(self.interest1, self.interest2)
        self.profile2.interests.add(self.interest1)
    
    def test_profile_creation(self):
        """Test that a profile is created for a user"""
        self.assertEqual(self.user1.profile, self.profile1)
        self.assertEqual(self.user2.profile, self.profile2)
    
    def test_profile_str_method(self):
        """Test the string representation of a profile"""
        self.assertEqual(str(self.profile1), "testuser1's Profile")
    
    def test_profile_age_property(self):
        """Test the age property of a profile"""
        today = date.today()
        age1 = today.year - self.profile1.birth_date.year - (
            (today.month, today.day) < (self.profile1.birth_date.month, self.profile1.birth_date.day)
        )
        self.assertEqual(self.profile1.age, age1)
    
    def test_distance_calculation(self):
        """Test distance calculation between two profiles"""
        # Haversine formula calculation (approximate)
        lat1, lon1 = self.profile1.latitude, self.profile1.longitude
        lat2, lon2 = self.profile2.latitude, self.profile2.longitude
        
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
        
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth radius in km
        
        expected_distance = c * r
        calculated_distance = self.profile1.distance_to(self.profile2)
        
        # Allow for minor floating point differences
        self.assertAlmostEqual(calculated_distance, expected_distance, places=2)


class MatchLikeTests(TestCase):
    """Tests for the Match and Like models"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpassword'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword'
        )
    
    def test_like_creation(self):
        """Test creating a like"""
        like = Like.objects.create(from_user=self.user1, to_user=self.user2)
        self.assertEqual(like.from_user, self.user1)
        self.assertEqual(like.to_user, self.user2)
        
        # Check there's no match yet
        self.assertEqual(Match.objects.count(), 0)
    
    def test_mutual_like_creates_match(self):
        """Test that mutual likes create a match"""
        # User1 likes User2
        like1 = Like.objects.create(from_user=self.user1, to_user=self.user2)
        
        # No match yet
        self.assertEqual(Match.objects.count(), 0)
        
        # User2 likes User1 back
        like2 = Like.objects.create(from_user=self.user2, to_user=self.user1)
        
        # Test that create_match_if_mutual was called and created a match
        self.assertEqual(Match.objects.count(), 1)
        
        # Get the match
        match = Match.objects.first()
        
        # Check match has correct users (Match always has lower user ID as user1)
        if self.user1.id < self.user2.id:
            self.assertEqual(match.user1, self.user1)
            self.assertEqual(match.user2, self.user2)
        else:
            self.assertEqual(match.user1, self.user2)
            self.assertEqual(match.user2, self.user1)


class ViewTests(TestCase):
    """Tests for the views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Set up profile
        self.profile = self.user.profile
        self.profile.bio = "Test bio"
        self.profile.birth_date = date(1990, 1, 1)
        self.profile.gender = 'M'
        self.profile.save()
    
    def test_home_view(self):
        """Test the home view"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
    
    def test_profile_view_authenticated(self):
        """Test the profile view when authenticated"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('accounts:profile_view', args=['testuser']))
        self.assertEqual(response.status_code, 200)
    
    def test_profile_view_unauthenticated(self):
        """Test the profile view redirects when not authenticated"""
        response = self.client.get(reverse('accounts:profile_view', args=['testuser']))
        self.assertEqual(response.status_code, 302)  # Redirect to login
