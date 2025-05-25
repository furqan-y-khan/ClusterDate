from django.urls import reverse
from .utils import check_premium_access, get_upgrade_url

def common_context(request):
    """
    Context processor that provides common variables to all templates
    """
    context = {
        'app_urls': {
            'mainstream': 'mainstream:',
            'casual': 'casual:',
            'serious': 'serious:',
            'religion': 'religion:',
            'ethnic': 'ethnic:',
            'lgbtq': 'lgbtq:',
            'sugar': 'sugar:',
            'niche': 'niche:',
            'messaging': 'messaging:',
            'video_call': 'video_call:',
            'payments': 'payments:',
            'accounts': 'accounts:',
            'core': 'core:',
        },
        'has_premium': {},
        'upgrade_urls': {}
    }
    
    # If user is authenticated, add premium status checks
    if request.user.is_authenticated:
        features = ['video_call', 'messaging', 'advanced_search', 'profile_boost', 'see_likes', 'hide_ads']
        
        for feature in features:
            context['has_premium'][feature] = check_premium_access(request.user, feature)
            context['upgrade_urls'][feature] = get_upgrade_url(feature)
    
    return context 