from django.conf import settings
from .models import Song
from .models import Ad
from django.utils import timezone

def admin_notifications(request):
    """Context processor for admin notifications on homepage"""
    pending_boost_count = 0
    pending_song_count = 0
    pending_ad_count = 0
    
    if request.user.is_authenticated and request.user.is_staff:
        # Count pending boost requests (paid but not trending)
        pending_boost_count = Song.objects.filter(boost_paid=True, is_trending=False).count()
        
        # Count pending song approvals (not approved)
        pending_song_count = Song.objects.filter(is_approved=False).count()
    
    return {
        'pending_boost_count': pending_boost_count,
        'pending_song_count': pending_song_count,
        'total_pending_count': pending_boost_count + pending_song_count,
    }

def ads_context(request):
    # Get active ads that haven't expired
    active_ads = Ad.objects.filter(is_active=True)
    
    # Filter out expired ads
    valid_ads = []
    for ad in active_ads:
        if ad.end_date and ad.end_date < timezone.now():
            continue
        valid_ads.append(ad)
    
    # Get ALL banner ads (no limit) - will rotate in template
    banner_ads = [ad for ad in valid_ads if ad.ad_type == 'banner']
    
    # Get sponsor ads for sidebar
    sponsor_ads = [ad for ad in valid_ads if ad.ad_type == 'sponsor'][:5]
    
    # Get in-feed ads
    infeed_ads = [ad for ad in valid_ads if ad.ad_type == 'infeed'][:3]
    
    # Get event ads
    event_ads = [ad for ad in valid_ads if ad.ad_type == 'event'][:6]
    
    # Increment impressions (skip admin pages)
    if not request.path.startswith('/admin/'):
        for ad in valid_ads:
            ad.impressions += 1
            ad.save()
    
    return {
        'sponsor_ads': sponsor_ads,
        'banner_ads': banner_ads,
        'infeed_ads': infeed_ads,
        'event_ads': event_ads,
    }

def user_context(request):
    if request.user.is_authenticated:
        return {'user': request.user}
    return {}

def payment_settings(request):
    """Make payment settings available in all templates - Uganda (200 UGX)"""
    return {
        # Price settings
        'song_price': 200,
        'song_price_formatted': 'UGX 200',
        
        # Revenue split (60/40)
        'artist_share': 120,  # 60% of 200 = 120 UGX
        'artist_share_formatted': 'UGX 120',
        'platform_share': 80,  # 40% of 200 = 80 UGX
        'platform_share_formatted': 'UGX 80',
        
        # Percentages
        'artist_percentage': 60,
        'platform_percentage': 40,
        
        # Currency
        'currency': 'UGX',
        'currency_symbol': 'UGX',
        
        # Withdrawal settings
        'min_withdrawal': 10000,
        'min_withdrawal_formatted': 'UGX 10,000',
        'downloads_needed_for_withdrawal': 84,  # 10,000 / 120 = 83.33 ≈ 84 downloads
    }