from xml.etree.ElementTree import Comment
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

# Custom username validator that allows spaces
class UsernameWithSpacesValidator(UnicodeUsernameValidator):
    regex = r'^[\w.@+\-\s]+$'
    message = 'Enter a valid username. This value may contain letters, numbers, spaces, and @/./+/-/_ characters.'

# ============================================================
# CUSTOM USER MODEL
# ============================================================

# East African Countries
COUNTRY_CHOICES = [
    ('uganda', '🇺🇬 Uganda'),
    ('kenya', '🇰🇪 Kenya'),
    ('tanzania', '🇹🇿 Tanzania'),
    ('rwanda', '🇷🇼 Rwanda'),
    ('burundi', '🇧🇮 Burundi'),
    ('south_sudan', '🇸🇸 South Sudan'),
    ('other', '🌍 Other'),
]
class CustomUser(AbstractUser):
    # Professional & Identity Info
    is_artist = models.BooleanField(default=False, db_index=True)
    artist_color = models.CharField(max_length=7, default="#ffffff")
    is_pro = models.BooleanField(default=False, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    pro_expiry = models.DateTimeField(null=True, blank=True)
    subscription_plan = models.CharField(max_length=20, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')], blank=True, null=True)
    
    # Profile Display Fields
    display_name = models.CharField(max_length=100, blank=True, help_text="Name shown on your profile")
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    # Points & Ranking
    points = models.PositiveIntegerField(default=0, db_index=True)
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Add after whatsapp_number field
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    # User Type
    USER_TYPE_CHOICES = (
        ('user', 'Regular User'),
        ('artist', 'Artist'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    
    # Advertiser Request Fields
    wants_to_advertise = models.BooleanField(default=False)
    advertiser_business_name = models.CharField(max_length=200, blank=True)
    advertiser_message = models.TextField(blank=True)
    
    # Groups & Permissions
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='music_customuser_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='music_customuser_permissions',
        blank=True
    )
    
    # Track user activity
    last_active = models.DateTimeField(default=timezone.now, db_index=True)
    total_plays = models.PositiveIntegerField(default=0, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-points']),
            models.Index(fields=['-last_active']),
            models.Index(fields=['is_artist', '-points']),
        ]
    
    @property
    def rank(self):
        if self.points < 100:
            return "New Listener"
        elif self.points < 500:
            return "Bronze Fan"
        elif self.points < 2000:
            return "Silver Supporter"
        elif self.points < 5000:
            return "Gold General"
        else:
            return "Era Legend 🏆"
    
    @property
    def is_pro_active(self):
        """Check if user is PRO and not expired"""
        if not self.is_pro:
            return False
        if self.pro_expiry and self.pro_expiry < timezone.now():
            return False
        return True
    
    @property
    def get_display_name(self):
        """Return display name or username"""
        return self.display_name if self.display_name else self.username
    
    def get_absolute_url(self):
        return reverse('artist_detail', args=[str(self.id)])
    
    def __str__(self):
        return self.username
    
    @property
    def get_cover_url(self):
     if self.cover_image:
        return self.cover_image.url
     return '/static/images/eratunez-logo.png'


# ============================================================
# SONG MODEL
# ============================================================
class Song(models.Model):
    GENRE_CHOICES = [
        ('Afrobeat', 'Afrobeat'),
        ('Dancehall', 'Dancehall'),
        ('Gospel', 'Gospel'),
        ('Kadongo Kamu', 'Kadongo Kamu'),
        ('Hip Hop', 'Hip Hop'),
        ('R&B', 'R&B'),
        ('Amapiano', 'Amapiano'),
        ('Reggae', 'Reggae'),
        ('Zouk', 'Zouk'),
        ('Highlife', 'Highlife'),
        ('Soukous', 'Soukous'),
        ('Bongo Flava', 'Bongo Flava'),
        ('pop', 'Pop'),
    ]

    # Core fields
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=200, db_index=True)
    audio_file = models.FileField(upload_to='songs/')
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='Afrobeat', db_index=True)
    region = models.CharField(max_length=50, default='all', blank=True)
    # Metadata
    duration = models.PositiveIntegerField(default=0)
    release_date = models.DateField(default=timezone.now, db_index=True)
    
    # Engagement metrics
    play_count = models.PositiveIntegerField(default=0, db_index=True)
    download_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0, db_index=True)
    favorite_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    # Trending & Boost
    is_trending = models.BooleanField(default=False, db_index=True)
    trending_expiry = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # Boost payment tracking
    boost_paid = models.BooleanField(default=False)
    boost_requested_at = models.DateTimeField(null=True, blank=True)
    payment_screenshot = models.ImageField(upload_to='payments/', blank=True, null=True)
    
    # Status
    is_approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Relationships
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='song_likes', blank=True)
    favorites = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='song_favorites', blank=True)
    
    # Lyrics
    lyrics = models.TextField(blank=True, null=True)
    has_lyrics = models.BooleanField(default=False)
    lyrics_views = models.PositiveIntegerField(default=0)

    # Video Integration
    youtube_url = models.URLField(blank=True, null=True, help_text="YouTube video link (e.g., https://www.youtube.com/watch?v=...")
    has_video = models.BooleanField(default=False)

    # Add after existing fields
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    def get_youtube_embed_url(self):
        """Convert YouTube URL to embed URL"""
        if not self.youtube_url:
            return None
        
        # Handle youtu.be format
        if 'youtu.be' in self.youtube_url:
            video_id = self.youtube_url.split('/')[-1].split('?')[0]
        # Handle youtube.com/watch?v= format
        elif 'watch?v=' in self.youtube_url:
            video_id = self.youtube_url.split('v=')[1].split('&')[0]
        # Handle youtube.com/embed/ format
        elif 'youtube.com/embed/' in self.youtube_url:
            video_id = self.youtube_url.split('/embed/')[1].split('?')[0]
        else:
            return None
        
        return f"https://www.youtube.com/embed/{video_id}?autoplay=0&enablejsapi=1"
    def get_absolute_url(self):
        return reverse('song_detail', args=[str(self.id)])
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-play_count']),
            models.Index(fields=['genre', '-play_count']),
            models.Index(fields=['artist', '-created_at']),
            models.Index(fields=['is_trending', '-trending_expiry']),
            models.Index(fields=['is_approved', '-created_at']),
            models.Index(fields=['title']),
        ]
    
    def increment_play_count(self):
        from django.db.models import F
        Song.objects.filter(pk=self.pk).update(play_count=F('play_count') + 1)
        self.refresh_from_db()
    
    def __str__(self):
        return self.title


# ============================================================
# PRODUCT/MERCH MODEL (Moved BEFORE Payment)
# ============================================================
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Clothing', 'Clothing'),
        ('Accessories', 'Accessories'),
        ('Tickets', 'Event Tickets'),
        ('Digital', 'Digital Downloads'),
        ('Other', 'Other Merch'),
    ]
    
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products', db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    image = models.ImageField(upload_to='products/')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Clothing', db_index=True)
    stock = models.PositiveIntegerField(default=0)
    sold_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['artist', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['-sold_count']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.artist.username}"


# ============================================================
# PRO REQUEST MODEL (Moved BEFORE Payment)
# ============================================================
class ProRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PLAN_CHOICES = [
        ('monthly', 'Monthly - UGX 20,000'),
        ('yearly', 'Yearly - UGX 200,000'),
    ]
    
    artist = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='pro_requests')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    payment_screenshot = models.ImageField(upload_to='pro_payments/', blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.artist.username} - {self.plan} - {self.status}"


# ============================================================
# PAYMENT MODEL (NOW all dependencies are defined above)
# ============================================================
class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_TYPE = [
        ('song_purchase', 'Song Purchase'),
        ('boost_song', 'Boost Song'),
        ('pro_subscription', 'PRO Subscription'),
        ('merch_purchase', 'Merchandise Purchase'),
        ('advertising', 'Advertising'),
        ('tip_artist', 'Tip Artist'),
    ]
    
    # User and transaction details
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments', db_index=True)
    transaction_ref = models.CharField(max_length=100, unique=True, db_index=True)
    flutterwave_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    currency = models.CharField(max_length=3, default='NGN')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE, db_index=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending', db_index=True)
    
    # Related items (now these models exist!)
    song = models.ForeignKey(Song, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    pro_request = models.ForeignKey(ProRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    # Payment metadata
    payment_method = models.CharField(max_length=50, blank=True)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # For song boosts
    boost_duration_days = models.IntegerField(default=7)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # Webhook verification
    webhook_verified = models.BooleanField(default=False)
    verification_attempts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['payment_type', '-created_at']),
            models.Index(fields=['paid_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} - {self.status}"
    
    @property
    def is_completed(self):
        return self.status == 'successful'
    
    


# ============================================================
# USER SONG PURCHASE MODEL
# ============================================================
class UserSongPurchase(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchased_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='purchased_by')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, related_name='purchases')
    purchased_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # 🆕 ADD THIS FIELD - Track how many downloads remaining
    downloads_remaining = models.IntegerField(default=1)  # Only 1 download allowed
    has_downloaded = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'song']
        ordering = ['-purchased_at']
    
    def can_download(self):
        """Check if user can still download this song"""
        return self.downloads_remaining > 0
    
    def use_download(self):
        """Use one download, returns True if successful"""
        if self.downloads_remaining > 0:
            self.downloads_remaining -= 1
            self.has_downloaded = True
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"{self.user.username} - {self.song.title} - {self.downloads_remaining} downloads left"

    class Meta:
        unique_together = ['user', 'song']
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.song.title}"
def mark_as_successful(self, flutterwave_data=None):
    """Mark payment as successful and update related records"""
    from django.conf import settings  # Keep this inside to avoid circular imports
    
    self.status = 'successful'
    self.paid_at = timezone.now()
    if flutterwave_data:
        self.flutterwave_id = flutterwave_data.get('id')
        self.payment_method = flutterwave_data.get('payment_type', '')
    self.save()
    
    # Update related records based on payment type
    if self.payment_type == 'song_purchase' and self.song:
        artist_earnings = float(self.amount) * (getattr(settings, 'ARTIST_EARNINGS_PERCENTAGE', 70) / 100)
        platform_fee = float(self.amount) * (getattr(settings, 'PLATFORM_FEE_PERCENTAGE', 10) / 100)
        
        Earning.objects.create(
            artist=self.song.artist,
            payment=self,
            amount=artist_earnings,
            platform_fee=platform_fee,
            total_amount=self.amount,  # ✅ FIXED: Added this
            song=self.song
        )
        
        UserSongPurchase.objects.get_or_create(
            user=self.user,
            song=self.song,
            defaults={'payment': self, 'purchased_at': timezone.now()}
        )
    
    elif self.payment_type == 'boost_song' and self.song:
        self.song.is_trending = True
        self.song.trending_expiry = timezone.now() + timezone.timedelta(days=self.boost_duration_days)
        self.song.boost_paid = True
        self.song.save()
    
    elif self.payment_type == 'pro_subscription' and self.pro_request:
        self.pro_request.status = 'approved'
        self.pro_request.processed_date = timezone.now()
        self.pro_request.save()
        
        user = self.pro_request.artist
        user.is_pro = True
        if self.pro_request.plan == 'monthly':
            user.pro_expiry = timezone.now() + timezone.timedelta(days=30)
        else:
            user.pro_expiry = timezone.now() + timezone.timedelta(days=365)
        user.subscription_plan = self.pro_request.plan
        user.save()

# ============================================================
# EARNING MODEL
# ============================================================
class Earning(models.Model):
    WITHDRAWAL_STATUS = [
        ('pending', 'Pending'),
        ('withdrawn', 'Withdrawn'),
        ('cancelled', 'Cancelled'),
    ]
    
    artist = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='earnings', db_index=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='earnings')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='earnings', null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ✅ Added default=0
    
    status = models.CharField(max_length=20, choices=WITHDRAWAL_STATUS, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # ... rest of the class
# ============================================================
# WITHDRAWAL MODEL
# ============================================================
class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    artist = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='withdrawals', db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200)
    
    transfer_reference = models.CharField(max_length=100, unique=True, blank=True, null=True)
    flutterwave_transfer_id = models.CharField(max_length=100, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    admin_notes = models.TextField(blank=True)
    
    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['artist', '-requested_at']),
            models.Index(fields=['status', '-requested_at']),
            models.Index(fields=['-requested_at']),
        ]
    
    def __str__(self):
        return f"{self.artist.username} - {self.amount} - {self.status}"
    
    def approve(self, transfer_ref=None):
        self.status = 'processing'
        self.processed_at = timezone.now()
        if transfer_ref:
            self.transfer_reference = transfer_ref
        self.save()
    
    def complete(self, flutterwave_id=None):
        self.status = 'completed'
        self.completed_at = timezone.now()
        if flutterwave_id:
            self.flutterwave_transfer_id = flutterwave_id
        self.save()
        Earning.objects.filter(artist=self.artist, status='pending').update(status='withdrawn')
    
    def reject(self, reason=''):
        self.status = 'rejected'
        self.admin_notes = reason
        self.processed_at = timezone.now()
        self.save()


# ============================================================
# WALLET MODEL
# ============================================================
class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wallet', db_index=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_index=True)
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-balance']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Balance: {self.balance}"
    
    def add_earnings(self, amount):
        from django.db.models import F
        self.balance = F('balance') + amount
        self.total_earned = F('total_earned') + amount
        self.save(update_fields=['balance', 'total_earned'])
        self.refresh_from_db()
    
    def subtract_balance(self, amount):
        if self.balance >= amount:
            from django.db.models import F
            self.balance = F('balance') - amount
            self.total_withdrawn = F('total_withdrawn') + amount
            self.save(update_fields=['balance', 'total_withdrawn'])
            self.refresh_from_db()
            return True
        return False


# ============================================================
# PLAYLIST MODELS
# ============================================================
class Playlist(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playlists', db_index=True)
    cover_image = models.ImageField(upload_to='playlist_covers/', null=True, blank=True)
    is_public = models.BooleanField(default=True, db_index=True)
    play_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_public', '-play_count']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.user.username}"
    
    def song_count(self):
        return self.playlist_songs.count()


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='playlist_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='playlist_songs')
    added_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'added_at']
        unique_together = ['playlist', 'song']
    
    def __str__(self):
        return f"{self.song.title} in {self.playlist.name}"


# ============================================================
# COMMENT MODEL
# ============================================================
class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='comments', db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField(max_length=500)
    likes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['song', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['parent', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} on {self.song.title}"
    
    @property
    def reply_count(self):
        return self.replies.count()


class CommentLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
    
    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id}"


# ============================================================
# RECENTLY PLAYED
# ============================================================
class RecentlyPlayed(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, db_index=True)
    played_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ['-played_at']
        indexes = [
            models.Index(fields=['user', '-played_at']),
            models.Index(fields=['song', '-played_at']),
            models.Index(fields=['-played_at']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['user', 'song'], name='unique_user_song_once')
        ]
    
    @classmethod
    def add_play(cls, user, song):
        cls.objects.create(user=user, song=song, played_at=timezone.now())
        from django.db.models import F
        user.total_plays = F('total_plays') + 1
        user.save(update_fields=['total_plays'])
        song.increment_play_count()
        recent_ids = cls.objects.filter(user=user).values_list('id', flat=True)[:50]
        cls.objects.filter(user=user).exclude(id__in=recent_ids).delete()
    
    def __str__(self):
        return f"{self.user.username} - {self.song.title}"


# ============================================================
# AD MODEL
# ============================================================
class Ad(models.Model):
    AD_TYPES = [
        ('sponsor', 'Sponsor Ad (Sidebar)'),
        ('banner', 'Banner Ad (Top/Bottom)'),
        ('infeed', 'In-Feed Ad (Between Songs)'),
        ('event', 'Event Ad'),
    ]
    
    title = models.CharField(max_length=200)
    ad_type = models.CharField(max_length=20, choices=AD_TYPES, default='sponsor')
    image = models.ImageField(upload_to='ads/')
    link_url = models.URLField(help_text="Where users go when they click the ad")
    description = models.TextField(blank=True)
    
    display_order = models.IntegerField(default=0, help_text="Lower numbers show first")
    
    advertiser_name = models.CharField(max_length=200)
    advertiser_contact = models.CharField(max_length=100, help_text="WhatsApp or Phone number")
    advertiser_email = models.EmailField(blank=True)
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    clicks = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.advertiser_name}"
    
    @property
    def is_expired(self):
        if self.end_date and timezone.now() > self.end_date:
            return True
        return False


# ============================================================
# DJ MIX MODEL
# ============================================================
class DJMix(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    dj_name = models.CharField(max_length=100)
    cover_image = models.ImageField(upload_to='dj_mixes/')
    audio_file = models.FileField(upload_to='dj_mixes/audio/')
    duration = models.IntegerField(default=0)
    play_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    release_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', '-release_date']
    
    def __str__(self):
        return f"{self.title} by {self.dj_name}"


# ============================================================
# PODCAST MODEL
# ============================================================
class Podcast(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    host_name = models.CharField(max_length=100, null=True, blank=True, default='Unknown Host')
    cover_image = models.ImageField(upload_to='podcasts/covers/')
    audio_file = models.FileField(upload_to='podcasts/audio/')
    duration = models.IntegerField(default=0)
    play_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    episode_number = models.IntegerField(default=1)
    season_number = models.IntegerField(default=1)
    release_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-season_number', '-episode_number', '-release_date']
    
    def __str__(self):
        return f"S{self.season_number} E{self.episode_number}: {self.title}"


# ============================================================
# USER LISTENING HISTORY
# ============================================================
class UserListeningHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listening_history')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    played_at = models.DateTimeField(auto_now_add=True)
    play_duration = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-played_at']
        indexes = [
            models.Index(fields=['user', '-played_at']),
            models.Index(fields=['song', '-played_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.song.title}"


# ============================================================
# USER SONG INTERACTION
# ============================================================
class UserSongInteraction(models.Model):
    INTERACTION_TYPES = [
        ('play', 'Play'),
        ('like', 'Like'),
        ('favorite', 'Favorite'),
        ('download', 'Download'),
        ('share', 'Share'),
        ('skip', 'Skip'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='song_interactions')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['song', 'interaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.song.title}"


# ============================================================
# USER MIX MODELS
# ============================================================
class UserMix(models.Model):
    MIX_TYPES = [
        ('daily', 'Daily Mix'),
        ('weekly', 'Weekly Mix'),
        ('genre', 'Genre Mix'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mixes')
    mix_type = models.CharField(max_length=20, choices=MIX_TYPES)
    name = models.CharField(max_length=100)
    genre = models.CharField(max_length=50, blank=True, null=True)
    cover_image = models.ImageField(upload_to='mix_covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"


class MixSong(models.Model):
    mix = models.ForeignKey(UserMix, on_delete=models.CASCADE, related_name='mix_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.mix.name}: {self.song.title}"


# ============================================================
# FOLLOW MODEL
# ============================================================
class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['follower', '-created_at']),
            models.Index(fields=['following', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# ============================================================
# MOOD MODELS
# ============================================================
class Mood(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='bi-emoji-smile')
    color = models.CharField(max_length=20, default='#1db954')
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='moods/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_icon_html(self):
        return f'<i class="bi {self.icon}"></i>'


class SongMood(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='moods')
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE, related_name='songs')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['song', 'mood']
    
    def __str__(self):
        return f"{self.song.title} - {self.mood.name}"


# ============================================================
# SIGNALS (Auto-create wallet for new users)
# ============================================================
@receiver(post_save, sender=CustomUser)
def create_user_wallet(sender, instance, created, **kwargs):
    """Automatically create a wallet for every new user"""
    if created:
        Wallet.objects.get_or_create(user=instance)


@receiver(post_save, sender=Earning)
def update_wallet_on_earning(sender, instance, created, **kwargs):
    """Update wallet balance when earnings are added"""
    if created and instance.status == 'pending':
        wallet, _ = Wallet.objects.get_or_create(user=instance.artist)
        wallet.add_earnings(instance.amount)
        
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=300, blank=True, help_text="Short summary for the blog listing")
    cover_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    tags = models.CharField(max_length=200, blank=True, help_text="Comma separated: ugandan-music, afrobeats, etc")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog_detail', args=[self.slug])  

    class LiveStream(models.Model):
     title = models.CharField(max_length=200, default="EraTunez Live DJ Mix")
    embed_url = models.URLField(
        help_text="Paste your Facebook Live or YouTube embed link here"
    )
    is_live = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Ensures only one stream is marked as LIVE at a time
        if self.is_live:
            LiveStream.objects.filter(is_live=True).exclude(pk=self.pk).update(is_live=False)
        super().save(*args, **kwargs)

    def __str__(self):
        status = "LIVE" if self.is_live else "OFFLINE"
        return f"{self.title} [{status}]"     