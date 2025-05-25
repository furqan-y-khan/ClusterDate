from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from .models import VerificationToken, PasswordResetToken, UserVerification
from core.models import Profile
import uuid
import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Initialize Firebase Admin SDK
try:
    # Check if Firebase is already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_ADMIN_SDK_CREDENTIALS)
        firebase_admin.initialize_app(cred)
except (ValueError, firebase_admin.exceptions.FirebaseError) as e:
    # App already initialized or credentials not available
    print(f"Firebase initialization error: {e}")
    pass

def register(request):
    """
    User registration view
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validate form data
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'accounts/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False  # User will be activated after email verification
        )
        
        # Profile will be automatically created by the signal handler
        
        # Create verification token
        token = VerificationToken.objects.create(user=user)
        
        # Send verification email
        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_email', args=[token.token])
        )
        
        subject = 'Verify your Super Dating App account'
        html_message = render_to_string('accounts/email/verification_email.html', {
            'user': user,
            'verification_url': verification_url,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
        )
        
        # Store the username in session to use it for resending verification email
        request.session['pending_verification_username'] = username
        
        messages.success(request, f"""
            Registration successful! An email verification link has been sent to <strong>{email}</strong>.<br>
            Please check your email to verify your account before logging in.<br>
            <a href='{reverse('accounts:resend_verification')}' class='alert-link'>Click here</a> if you need to resend the verification email.
        """, extra_tags='safe')
        
        return redirect('accounts:login')
    
    return render(request, 'accounts/register.html')

def verify_email(request, token):
    """
    Email verification view
    """
    verification_token = get_object_or_404(VerificationToken, token=token)
    
    if verification_token.is_used:
        messages.error(request, "This verification link has already been used.")
        return redirect('accounts:login')
    
    if timezone.now() > verification_token.expires_at:
        messages.error(request, "This verification link has expired. Please request a new one.")
        return redirect('accounts:login')
    
    # Activate user
    user = verification_token.user
    user.is_active = True
    user.save()
    
    # Mark token as used
    verification_token.is_used = True
    verification_token.save()
    
    messages.success(request, "Email verified successfully! You can now log in.")
    return redirect('accounts:login')

def login_view(request):
    """
    User login view
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            
            # Redirect to the page the user was trying to access, or to the home page
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            # Check if the user exists but is not active
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    # Store the username in session to use it for resending verification email
                    request.session['pending_verification_username'] = username
                    messages.error(request, "Your account is not active. Please verify your email before logging in. <a href='{}' class='alert-link'>Resend verification email</a>".format(
                        reverse('accounts:resend_verification')
                    ), extra_tags='safe')
                else:
                    messages.error(request, "Invalid username or password.")
            except User.DoesNotExist:
                messages.error(request, "Invalid username or password.")
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    """
    User logout view
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

def forgot_password(request):
    """
    Forgot password view
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Create or update password reset token
            token, created = PasswordResetToken.objects.update_or_create(
                user=user,
                defaults={
                    'token': uuid.uuid4(),
                    'expires_at': timezone.now() + timezone.timedelta(hours=1),
                    'is_used': False
                }
            )
            
            # Send password reset email
            reset_url = request.build_absolute_uri(
                reverse('accounts:reset_password', args=[token.token])
            )
            
            subject = 'Reset your Super Dating App password'
            html_message = render_to_string('accounts/email/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
            )
            
            messages.success(request, "Password reset link sent to your email.")
        except User.DoesNotExist:
            # Don't reveal that the email doesn't exist
            messages.success(request, "If your email is registered, you will receive a password reset link.")
        
        return redirect('accounts:login')
    
    return render(request, 'accounts/forgot_password.html')

def reset_password(request, token):
    """
    Reset password view
    """
    reset_token = get_object_or_404(PasswordResetToken, token=token)
    
    if reset_token.is_used:
        messages.error(request, "This password reset link has already been used.")
        return redirect('accounts:login')
    
    if timezone.now() > reset_token.expires_at:
        messages.error(request, "This password reset link has expired. Please request a new one.")
        return redirect('accounts:forgot_password')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/reset_password.html', {'token': token})
        
        # Update user password
        user = reset_token.user
        user.set_password(password)
        user.save()
        
        # Mark token as used
        reset_token.is_used = True
        reset_token.save()
        
        messages.success(request, "Password reset successfully! You can now log in with your new password.")
        return redirect('accounts:login')
    
    return render(request, 'accounts/reset_password.html', {'token': token})

@login_required
def profile_edit(request):
    """
    Edit user profile view
    """
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        # Update user information
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.save()
        
        # Update profile information
        profile.bio = request.POST.get('bio', profile.bio)
        profile.gender = request.POST.get('gender', profile.gender)
        profile.location = request.POST.get('location', profile.location)
        
        # Handle birth date
        birth_date = request.POST.get('birth_date')
        if birth_date:
            from datetime import datetime
            profile.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        
        # Handle profile picture
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        # Update matching preferences
        profile.min_age_preference = request.POST.get('min_age_preference', profile.min_age_preference)
        profile.max_age_preference = request.POST.get('max_age_preference', profile.max_age_preference)
        profile.distance_preference = request.POST.get('distance_preference', profile.distance_preference)
        
        profile.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('accounts:profile_view', username=request.user.username)
    
    context = {
        'profile': profile
    }
    
    return render(request, 'accounts/profile_edit.html', context)

@login_required
def verify_identity(request):
    """
    Identity verification view
    """
    try:
        verification = UserVerification.objects.get(user=request.user)
    except UserVerification.DoesNotExist:
        verification = None
    
    if request.method == 'POST':
        if verification and verification.status == 'APPROVED':
            messages.info(request, "Your identity has already been verified.")
            return redirect('accounts:profile_view', username=request.user.username)
        
        # Create or update verification
        if verification:
            verification.status = 'PENDING'
        else:
            verification = UserVerification(user=request.user)
        
        # Handle ID document
        if 'id_document' in request.FILES:
            verification.id_document = request.FILES['id_document']
        
        # Handle selfie
        if 'selfie' in request.FILES:
            verification.selfie = request.FILES['selfie']
        
        verification.save()
        
        messages.success(request, "Verification documents submitted successfully! Our team will review them shortly.")
        return redirect('accounts:profile_view', username=request.user.username)
    
    context = {
        'verification': verification
    }
    
    return render(request, 'accounts/verify_identity.html', context)

def firebase_login_view(request):
    """
    View for Firebase login page
    """
    context = {
        'FIREBASE_CONFIG': settings.FIREBASE_CONFIG
    }
    return render(request, 'accounts/firebase_login.html', context)

def firebase_register_view(request):
    """
    View for Firebase registration page
    """
    context = {
        'FIREBASE_CONFIG': settings.FIREBASE_CONFIG
    }
    return render(request, 'accounts/firebase_register.html', context)

@require_POST
def firebase_auth(request):
    """
    Handle Firebase authentication
    """
    try:
        data = json.loads(request.body)
        id_token = data.get('idToken')
        provider = data.get('provider', 'email')
        
        if not id_token:
            return JsonResponse({'success': False, 'error': 'No ID token provided'}, status=400)
        
        # Verify the ID token
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_user_id = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # User doesn't exist, redirect to registration
            return JsonResponse({
                'success': False, 
                'error': 'User not found',
                'redirect_url': reverse('accounts:firebase_register')
            }, status=404)
        
        # Log the user in
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('home')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_POST
def firebase_register(request):
    """
    Handle Firebase registration
    """
    try:
        data = json.loads(request.body)
        id_token = data.get('idToken')
        provider = data.get('provider', 'email')
        username = data.get('username', '')
        
        if not id_token:
            return JsonResponse({'success': False, 'error': 'No ID token provided'}, status=400)
        
        # Verify the ID token
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_user_id = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            # User already exists, log them in
            login(request, user)
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('home')
            })
        except User.DoesNotExist:
            # Create a new user
            if not username:
                username = email.split('@')[0]
            
            # Make sure username is unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=None  # No password for social auth
            )
            
            # Create profile
            Profile.objects.create(user=user)
            
            # Log the user in
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('accounts:profile_edit')
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def update_fcm_token(request):
    """
    Update the user's FCM token for push notifications
    """
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({'success': False, 'error': 'Token is required'}, status=400)
        
        # Update user's profile
        profile = request.user.profile
        profile.fcm_token = token
        profile.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def delete_account(request):
    """
    Handle account deletion with GDPR compliance
    """
    if request.method == 'POST':
        password = request.POST.get('password')
        confirmation = request.POST.get('confirmation')
        
        # Verify password
        if not request.user.check_password(password):
            messages.error(request, "Incorrect password. Please try again.")
            return render(request, 'accounts/delete_account.html')
        
        # Verify confirmation text
        if confirmation != "DELETE MY ACCOUNT":
            messages.error(request, "Please type the confirmation text exactly as shown.")
            return render(request, 'accounts/delete_account.html')
        
        # Get user object
        user = request.user
        
        # Cancel any active subscriptions
        try:
            from payments.models import Subscription
            active_subscriptions = Subscription.objects.filter(
                user=user, 
                status='active',
                end_date__isnull=True
            )
            
            for subscription in active_subscriptions:
                try:
                    import stripe
                    from django.conf import settings
                    stripe.api_key = settings.STRIPE_API_KEY
                    
                    # Cancel in Stripe
                    if subscription.stripe_subscription_id:
                        stripe.Subscription.delete(subscription.stripe_subscription_id)
                    
                    # Update our database
                    subscription.status = 'canceled'
                    subscription.end_date = timezone.now()
                    subscription.save()
                except Exception as e:
                    logger.error(f"Error canceling subscription during account deletion: {str(e)}")
        except ImportError:
            # Payments module not available
            pass
        
        # Log the user out
        logout(request)
        
        # Anonymize user data instead of hard delete (GDPR compliant)
        user.username = f"deleted_user_{user.id}"
        user.email = f"deleted_{user.id}@example.com"
        user.first_name = "Deleted"
        user.last_name = "User"
        user.is_active = False
        user.set_unusable_password()
        user.save()
        
        # Delete or anonymize profile data
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.bio = ""
            profile.location = ""
            
            # Delete profile picture
            if profile.profile_picture:
                profile.profile_picture.delete()
            
            # Remove interests
            profile.interests.clear()
            
            # Save anonymized profile
            profile.save()
        
        # Delete user verification documents if any
        if hasattr(user, 'verification'):
            verification = user.verification
            if verification.id_document:
                verification.id_document.delete()
            if verification.selfie:
                verification.selfie.delete()
            verification.delete()
        
        messages.success(request, "Your account has been successfully deleted. We're sorry to see you go.")
        return redirect('home')
    
    return render(request, 'accounts/delete_account.html')


@login_required
def export_user_data(request):
    """
    Export all user data in compliance with GDPR
    """
    user = request.user
    
    # Collect user data
    user_data = {
        'account': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
    }
    
    # Add profile data
    if hasattr(user, 'profile'):
        profile = user.profile
        user_data['profile'] = {
            'bio': profile.bio,
            'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
            'gender': profile.get_gender_display() if profile.gender else None,
            'location': profile.location,
            'latitude': profile.latitude,
            'longitude': profile.longitude,
            'interests': [interest.name for interest in profile.interests.all()],
            'created_at': profile.created_at.isoformat(),
            'updated_at': profile.updated_at.isoformat(),
        }
    
    # Add matches
    from core.models import Match
    matches = []
    user_matches = Match.objects.filter(user1=user) | Match.objects.filter(user2=user)
    for match in user_matches:
        match_data = {
            'matched_with': match.user2.username if match.user1 == user else match.user1.username,
            'created_at': match.created_at.isoformat() if hasattr(match, 'created_at') else None,
        }
        matches.append(match_data)
    user_data['matches'] = matches
    
    # Add messages
    from messaging.models import Message
    messages_data = []
    user_messages = Message.objects.filter(sender=user) | Message.objects.filter(receiver=user)
    for msg in user_messages:
        message_data = {
            'sender': msg.sender.username,
            'receiver': msg.receiver.username,
            'content': msg.content,
            'sent_at': msg.sent_at.isoformat(),
            'is_read': msg.is_read,
        }
        messages_data.append(message_data)
    user_data['messages'] = messages_data
    
    # Add subscription data if available
    try:
        from payments.models import Subscription, Payment
        subscriptions_data = []
        user_subscriptions = Subscription.objects.filter(user=user)
        for sub in user_subscriptions:
            subscription_data = {
                'plan_name': sub.plan.name if sub.plan else None,
                'status': sub.get_status_display(),
                'start_date': sub.start_date.isoformat(),
                'end_date': sub.end_date.isoformat() if sub.end_date else None,
                'created_at': sub.created_at.isoformat(),
            }
            subscriptions_data.append(subscription_data)
        user_data['subscriptions'] = subscriptions_data
        
        # Add payment history
        payments_data = []
        user_payments = Payment.objects.filter(user=user)
        for payment in user_payments:
            payment_data = {
                'amount': str(payment.amount),
                'currency': payment.currency,
                'status': payment.get_status_display(),
                'description': payment.description,
                'created_at': payment.created_at.isoformat(),
            }
            payments_data.append(payment_data)
        user_data['payments'] = payments_data
    except ImportError:
        # Payments module not available
        pass
    
    # Create JSON response
    response = JsonResponse(user_data, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="{user.username}_data_export.json"'
    
    return response


@login_required
def privacy_settings(request):
    """
    Manage privacy settings for the user
    """
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        # Update notification preferences
        profile.receive_message_notifications = 'receive_message_notifications' in request.POST
        profile.receive_match_notifications = 'receive_match_notifications' in request.POST
        profile.receive_like_notifications = 'receive_like_notifications' in request.POST
        
        # Update profile visibility settings
        profile_visibility = request.POST.get('profile_visibility', 'public')
        if hasattr(profile, 'profile_visibility'):
            profile.profile_visibility = profile_visibility
        
        # Update location sharing settings
        share_location = 'share_location' in request.POST
        if hasattr(profile, 'share_location'):
            profile.share_location = share_location
        
        profile.save()
        messages.success(request, "Your privacy settings have been updated.")
        return redirect('accounts:privacy_settings')
    
    context = {
        'profile': profile,
    }
    return render(request, 'accounts/privacy_settings.html', context)

@login_required
def onboarding_start(request):
    """
    Starting point for the onboarding wizard
    Displays welcome message and begins the profile setup flow
    """
    # Check if user already completed onboarding
    profile = request.user.profile
    onboarding_completed = profile.bio and profile.birth_date and profile.gender and profile.profile_picture
    
    if onboarding_completed:
        messages.info(request, "You've already completed your profile setup.")
        return redirect('accounts:profile_edit')
    
    # Initialize onboarding session data
    request.session['onboarding_step'] = 1
    request.session['onboarding_data'] = {}
    
    # Prepare context
    context = {
        'step': 1,
        'total_steps': 5,
        'profile': profile,
    }
    
    return render(request, 'accounts/onboarding/start.html', context)


@login_required
def onboarding_basics(request):
    """
    Step 1: Basic profile information (name, birth date, gender, bio)
    """
    profile = request.user.profile
    user = request.user
    
    # Ensure proper step sequence
    if request.session.get('onboarding_step', 1) != 1:
        return redirect('accounts:onboarding_start')
    
    if request.method == 'POST':
        # Process form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        birth_date = request.POST.get('birth_date')
        gender = request.POST.get('gender')
        bio = request.POST.get('bio')
        
        # Validate data
        if not (first_name and last_name and birth_date and gender):
            messages.error(request, "Please fill in all required fields.")
            return redirect('accounts:onboarding_basics')
        
        # Update user model
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        # Update profile
        profile.birth_date = birth_date
        profile.gender = gender
        profile.bio = bio
        profile.save()
        
        # Store in session for review at end
        onboarding_data = request.session.get('onboarding_data', {})
        onboarding_data['basics'] = {
            'first_name': first_name,
            'last_name': last_name,
            'birth_date': birth_date,
            'gender': gender,
            'bio': bio,
        }
        request.session['onboarding_data'] = onboarding_data
        
        # Move to next step
        request.session['onboarding_step'] = 2
        return redirect('accounts:onboarding_photos')
    
    # Prepare context with any existing data
    context = {
        'step': 1,
        'total_steps': 5,
        'profile': profile,
        'user': user,
    }
    
    return render(request, 'accounts/onboarding/basics.html', context)


@login_required
def onboarding_photos(request):
    """
    Step 2: Upload profile photos
    """
    profile = request.user.profile
    
    # Ensure proper step sequence
    if request.session.get('onboarding_step', 1) != 2:
        return redirect('accounts:onboarding_start')
    
    if request.method == 'POST':
        # Process main profile picture
        profile_picture = request.FILES.get('profile_picture')
        
        if profile_picture:
            # Delete existing profile picture if any
            if profile.profile_picture:
                profile.profile_picture.delete()
            
            # Save new profile picture
            profile.profile_picture = profile_picture
            profile.save()
            
            # Store data in session (just the fact that it was uploaded)
            onboarding_data = request.session.get('onboarding_data', {})
            onboarding_data['photos'] = {
                'profile_picture_uploaded': True,
            }
            request.session['onboarding_data'] = onboarding_data
            
            # Process additional photos if applicable
            # This would be expanded in a real implementation
            
            # Move to next step
            request.session['onboarding_step'] = 3
            return redirect('accounts:onboarding_interests')
        else:
            messages.error(request, "Please upload at least a main profile picture.")
    
    # Prepare context
    context = {
        'step': 2,
        'total_steps': 5,
        'profile': profile,
    }
    
    return render(request, 'accounts/onboarding/photos.html', context)


@login_required
def onboarding_interests(request):
    """
    Step 3: Select interests/hobbies
    """
    profile = request.user.profile
    
    # Ensure proper step sequence
    if request.session.get('onboarding_step', 1) != 3:
        return redirect('accounts:onboarding_start')
    
    # Get all available interests
    from core.models import Interest
    all_interests = Interest.objects.all().order_by('category', 'name')
    
    # Group interests by category
    interests_by_category = {}
    for interest in all_interests:
        category = interest.category or 'Other'
        if category not in interests_by_category:
            interests_by_category[category] = []
        interests_by_category[category].append(interest)
    
    if request.method == 'POST':
        # Get selected interests
        selected_interests = request.POST.getlist('interests')
        
        if not selected_interests:
            messages.warning(request, "Please select at least a few interests to help us match you better.")
            return redirect('accounts:onboarding_interests')
        
        # Update profile interests
        profile.interests.clear()  # Remove existing interests
        profile.interests.add(*selected_interests)
        
        # Store in session for review
        onboarding_data = request.session.get('onboarding_data', {})
        onboarding_data['interests'] = {
            'selected_interests': selected_interests,
        }
        request.session['onboarding_data'] = onboarding_data
        
        # Move to next step
        request.session['onboarding_step'] = 4
        return redirect('accounts:onboarding_preferences')
    
    # Prepare context
    context = {
        'step': 3,
        'total_steps': 5,
        'profile': profile,
        'interests_by_category': interests_by_category,
        'current_interests': list(profile.interests.all().values_list('id', flat=True)),
    }
    
    return render(request, 'accounts/onboarding/interests.html', context)


@login_required
def onboarding_preferences(request):
    """
    Step 4: Set matching preferences
    """
    profile = request.user.profile
    
    # Ensure proper step sequence
    if request.session.get('onboarding_step', 1) != 4:
        return redirect('accounts:onboarding_start')
    
    if request.method == 'POST':
        # Get preference data
        min_age = request.POST.get('min_age')
        max_age = request.POST.get('max_age')
        distance = request.POST.get('distance')
        gender_preference = request.POST.get('gender_preference', '')
        
        # Validate age range
        try:
            min_age = int(min_age)
            max_age = int(max_age)
            distance = int(distance)
            
            if min_age < 18:
                min_age = 18  # Enforce minimum age
            
            if max_age < min_age:
                max_age = min_age
            
            # Update profile
            profile.min_age_preference = min_age
            profile.max_age_preference = max_age
            profile.distance_preference = distance
            
            # Set gender preference if model supports it
            if hasattr(profile, 'gender_preference'):
                profile.gender_preference = gender_preference
            
            profile.save()
            
            # Store in session
            onboarding_data = request.session.get('onboarding_data', {})
            onboarding_data['preferences'] = {
                'min_age': min_age,
                'max_age': max_age,
                'distance': distance,
                'gender_preference': gender_preference,
            }
            request.session['onboarding_data'] = onboarding_data
            
            # Move to final step
            request.session['onboarding_step'] = 5
            return redirect('accounts:onboarding_complete')
            
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid numbers for age and distance preferences.")
    
    # Prepare context
    context = {
        'step': 4,
        'total_steps': 5,
        'profile': profile,
    }
    
    return render(request, 'accounts/onboarding/preferences.html', context)


@login_required
def onboarding_complete(request):
    """
    Final step: Review profile and complete onboarding
    """
    profile = request.user.profile
    user = request.user
    
    # Ensure proper step sequence
    if request.session.get('onboarding_step', 1) != 5:
        return redirect('accounts:onboarding_start')
    
    # Get all onboarding data
    onboarding_data = request.session.get('onboarding_data', {})
    
    # Calculate profile completion percentage
    completion_items = [
        bool(user.first_name and user.last_name),  # Name
        bool(profile.birth_date),                  # Birth date
        bool(profile.gender),                      # Gender
        bool(profile.bio),                         # Bio
        bool(profile.profile_picture),             # Profile picture
        bool(profile.interests.all()),             # Interests
        True,                                      # Preferences (set in previous step)
    ]
    
    completion_percentage = int((sum(1 for item in completion_items if item) / len(completion_items)) * 100)
    
    # If form submitted, redirect to app
    if request.method == 'POST':
        # Mark onboarding as complete (could store in profile if needed)
        if 'onboarding_data' in request.session:
            del request.session['onboarding_data']
        if 'onboarding_step' in request.session:
            del request.session['onboarding_step']
        
        messages.success(request, "Your profile is now complete! Start matching with others.")
        return redirect('home')
    
    # Prepare context
    context = {
        'step': 5,
        'total_steps': 5,
        'profile': profile,
        'user': user,
        'completion_percentage': completion_percentage,
        'onboarding_data': onboarding_data,
    }
    
    return render(request, 'accounts/onboarding/complete.html', context)

def resend_verification(request):
    """
    Resend verification email to user
    """
    username = request.session.get('pending_verification_username')
    
    if not username:
        messages.error(request, "No pending verification found.")
        return redirect('accounts:login')
    
    try:
        user = User.objects.get(username=username)
        
        # Delete any existing token
        VerificationToken.objects.filter(user=user).delete()
        
        # Create new verification token
        token = VerificationToken.objects.create(user=user)
        
        # Send verification email
        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_email', args=[token.token])
        )
        
        subject = 'Verify your Super Dating App account'
        html_message = render_to_string('accounts/email/verification_email.html', {
            'user': user,
            'verification_url': verification_url,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
        )
        
        messages.success(request, "Verification email has been resent. Please check your email.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    
    return redirect('accounts:login')
