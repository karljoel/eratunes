from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, Song, Comment, Product, Playlist, PlaylistSong, Ad, DJMix, Podcast, ProRequest, Mood, SongMood

# ==================== PRODUCT ADMIN ====================
admin.site.register(Product)

# ==================== CUSTOM USER ADMIN ====================
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Artist & Fan Info', {
            'fields': (
                'is_artist', 'is_pro', 'is_verified', 'whatsapp_number', 
                'artist_color', 'profile_picture', 'bio', 'points'
            )
        }),
    )
    
    list_display = ['username', 'email', 'points', 'is_artist', 'is_pro', 'is_verified', 'is_staff']
    list_editable = ['points', 'is_verified', 'is_pro']

# Unregister default User if exists, then register CustomUser
if admin.site.is_registered(CustomUser):
    admin.site.unregister(CustomUser)
admin.site.register(CustomUser, CustomUserAdmin)

# ==================== SONG ADMIN ====================
@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'region', 'genre', 'is_approved', 'has_lyrics', 'has_video', 'is_trending', 'boost_paid', 'trending_expiry')
    list_filter = ('is_approved', 'is_trending', 'has_lyrics', 'has_video', 'boost_paid', 'region', 'genre')
    search_fields = ('title', 'artist__username', 'region')
    list_editable = ('region', 'is_approved', 'is_trending', 'has_lyrics', 'has_video')
    actions = ['approve_boost']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'artist', 'genre', 'region', 'release_date')
        }),
        ('Media', {
            'fields': ('audio_file', 'cover_image')
        }),
        ('Lyrics', {
            'fields': ('lyrics', 'has_lyrics', 'lyrics_views'),
            'classes': ('collapse',),
            'description': 'Add song lyrics here. You can use plain text or LRC format (with timestamps like [00:15.00] Line of lyrics)'
        }),
        ('Music Video', {
            'fields': ('youtube_url', 'has_video'),
            'classes': ('collapse',),
            'description': 'Add YouTube link to music video. Users can watch video while audio plays.'
        }),
        ('Status', {
            'fields': ('is_approved', 'is_trending', 'trending_expiry', 'boost_paid')
        }),
        ('Statistics', {
            'fields': ('play_count', 'download_count')
        }),
    )
    
    def approve_boost(self, request, queryset):
        for song in queryset:
            if song.boost_paid and not song.is_trending:
                song.is_trending = True
                song.trending_expiry = timezone.now() + timedelta(days=5)
                song.save()
        self.message_user(request, f"✅ {queryset.count()} song(s) boosted to TRENDING for 5 days!")
    approve_boost.short_description = "✅ Approve selected boost requests"

# ==================== COMMENT ADMIN ====================
admin.site.register(Comment)

# ==================== PLAYLIST ADMIN ====================
@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_public', 'song_count', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'user__username')
    
    def song_count(self, obj):
        return obj.song_count()
    song_count.short_description = 'Songs'

@admin.register(PlaylistSong)
class PlaylistSongAdmin(admin.ModelAdmin):
    list_display = ('playlist', 'song', 'added_at', 'order')
    list_filter = ('added_at',)
    search_fields = ('playlist__name', 'song__title')

# ==================== AD ADMIN ====================
@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ('title', 'ad_type', 'advertiser_name', 'amount_paid', 'is_active', 'display_order', 'clicks', 'impressions')
    list_filter = ('ad_type', 'is_active')
    search_fields = ('title', 'advertiser_name')
    list_editable = ('is_active', 'display_order')
    actions = ['activate_ads', 'deactivate_ads', 'reset_stats']
    
    fieldsets = (
        ('Ad Details', {
            'fields': ('title', 'ad_type', 'image', 'link_url', 'description', 'display_order')
        }),
        ('Advertiser Info', {
            'fields': ('advertiser_name', 'advertiser_contact', 'advertiser_email')
        }),
        ('Payment', {
            'fields': ('amount_paid', 'payment_reference', 'payment_date')
        }),
        ('Schedule', {
            'fields': ('end_date', 'is_active')
        }),
        ('Statistics', {
            'fields': ('clicks', 'impressions'),
            'classes': ('collapse',)
        }),
    )
    
    def activate_ads(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"✅ {count} ad(s) activated.")
    activate_ads.short_description = "Activate selected ads"
    
    def deactivate_ads(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"❌ {count} ad(s) deactivated.")
    deactivate_ads.short_description = "Deactivate selected ads"
    
    def reset_stats(self, request, queryset):
        for ad in queryset:
            ad.clicks = 0
            ad.impressions = 0
            ad.save()
        self.message_user(request, f"📊 Stats reset for {queryset.count()} ad(s).")
    reset_stats.short_description = "Reset click/impression stats"

# ==================== DJ MIX ADMIN ====================
@admin.register(DJMix)
class DJMixAdmin(admin.ModelAdmin):
    list_display = ('title', 'dj_name', 'play_count', 'is_featured', 'release_date')
    list_filter = ('is_featured', 'release_date')
    search_fields = ('title', 'dj_name')
    list_editable = ('is_featured',)

# ==================== PODCAST ADMIN ====================
@admin.register(Podcast)
class PodcastAdmin(admin.ModelAdmin):
    list_display = ('title', 'host_name', 'episode_number', 'season_number', 'play_count', 'is_featured', 'release_date')
    list_filter = ('is_featured', 'season_number', 'release_date')
    search_fields = ('title', 'host_name')
    list_editable = ('is_featured',)

# ==================== MOOD ADMIN ====================
@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'color', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)

# ==================== SONG MOOD ADMIN ====================
@admin.register(SongMood)
class SongMoodAdmin(admin.ModelAdmin):
    list_display = ('song', 'mood', 'created_at')
    list_filter = ('mood',)
    search_fields = ('song__title', 'mood__name')

# ==================== PRO REQUEST ADMIN ====================
@admin.register(ProRequest)
class ProRequestAdmin(admin.ModelAdmin):
    list_display = ('artist', 'plan', 'amount', 'status', 'request_date')
    list_filter = ('status', 'plan')
    search_fields = ('artist__username', 'payment_reference')
    list_editable = ('status',)
    actions = ['approve_requests', 'reject_requests']
    
    fieldsets = (
        ('Request Info', {
            'fields': ('artist', 'plan', 'amount', 'payment_reference', 'payment_screenshot')
        }),
        ('Status', {
            'fields': ('status', 'admin_notes')
        }),
    )
    
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        count = 0
        for pro_request in queryset:
            if pro_request.status == 'pending':
                artist = pro_request.artist
                
                # Update artist
                artist.is_pro = True
                artist.is_verified = True
                
                if pro_request.plan == 'monthly':
                    artist.pro_expiry = timezone.now() + timedelta(days=30)
                else:
                    artist.pro_expiry = timezone.now() + timedelta(days=365)
                
                artist.subscription_plan = pro_request.plan
                artist.save()  # This saves all fields
                
                # Update request
                pro_request.status = 'approved'
                pro_request.processed_date = timezone.now()
                pro_request.save()
                
                count += 1
                print(f"✅ Approved PRO for {artist.username}")
        
        self.message_user(request, f"✅ {count} PRO request(s) approved successfully!")
    approve_requests.short_description = "Approve selected PRO requests"
    
    def reject_requests(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f"❌ {count} PRO request(s) rejected.")
    reject_requests.short_description = "Reject selected PRO requests"