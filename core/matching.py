from django.contrib.auth.models import User
from django.db.models import Q
from .models import Profile, Match, Like, Block, Interest
import logging

logger = logging.getLogger(__name__)

def get_matches_for_user(user, limit=20):
    """
    Get potential matches for a user based on preferences
    
    Args:
        user: The user to find matches for
        limit: Maximum number of matches to return
        
    Returns:
        List of user objects that match the criteria
    """
    try:
        profile = user.profile
        
        # Get user preferences
        min_age = profile.min_age_preference
        max_age = profile.max_age_preference
        distance = profile.distance_preference
        gender_preference = profile.gender_preference
        
        # Start with all users
        potential_matches = User.objects.exclude(id=user.id)
        
        # Filter by gender preference if specified
        if gender_preference and gender_preference != 'any':
            potential_matches = potential_matches.filter(profile__gender=gender_preference)
        
        # Filter by age range
        potential_matches = potential_matches.filter(
            profile__age__gte=min_age,
            profile__age__lte=max_age
        )
        
        # Exclude users that have blocked or been blocked by the current user
        blocked_users = Block.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        ).values_list('from_user', 'to_user')
        
        blocked_ids = set()
        for from_id, to_id in blocked_users:
            if from_id != user.id:
                blocked_ids.add(from_id)
            if to_id != user.id:
                blocked_ids.add(to_id)
        
        potential_matches = potential_matches.exclude(id__in=blocked_ids)
        
        # Filter by distance if location is available
        if profile.latitude and profile.longitude:
            # This would be a more complex query using geodjango or similar
            # For simplicity, we'll just return the filtered results without distance filtering
            pass
        
        # Limit results
        return potential_matches[:limit]
    
    except Exception as e:
        logger.error(f"Error in get_matches_for_user: {str(e)}")
        return User.objects.none()

def get_machine_learning_recommendations(user, limit=10):
    """
    Get recommendations for a user based on machine learning algorithms
    
    Args:
        user: The user to find recommendations for
        limit: Maximum number of recommendations to return
        
    Returns:
        List of user objects recommended by the algorithm
    """
    try:
        # In a real implementation, this would call a machine learning service
        # For now, we'll just return users with similar interests
        
        # Get user's interests
        user_interests = Interest.objects.filter(profile=user.profile).values_list('name', flat=True)
        
        if not user_interests:
            # If no interests, fall back to regular matching
            return get_matches_for_user(user, limit)
        
        # Find users with similar interests
        similar_users = User.objects.exclude(id=user.id).filter(
            profile__interests__name__in=user_interests
        ).distinct()
        
        # Exclude blocked users
        blocked_users = Block.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        ).values_list('from_user', 'to_user')
        
        blocked_ids = set()
        for from_id, to_id in blocked_users:
            if from_id != user.id:
                blocked_ids.add(from_id)
            if to_id != user.id:
                blocked_ids.add(to_id)
        
        similar_users = similar_users.exclude(id__in=blocked_ids)
        
        return similar_users[:limit]
    
    except Exception as e:
        logger.error(f"Error in get_machine_learning_recommendations: {str(e)}")
        return User.objects.none() 