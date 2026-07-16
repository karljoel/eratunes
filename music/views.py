from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.http import FileResponse, Http404, JsonResponse
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.db import models
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import random
import re
import tempfile
import uuid
from .models import BlogPost

from .models import (
    Song, CustomUser, UserSongInteraction, Product, RecentlyPlayed, 
    Mood, SongMood, Comment, Playlist, PlaylistSong, Ad, DJMix, Podcast, 
    ProRequest, UserMix, MixSong, Follow, CommentLike, UserListeningHistory
)
from .forms import (
    SongForm, ArtistSignupForm, UserSignupForm, CustomLoginForm, 
    UserProfileForm, AdvertiserRequestForm
)


# ============================================================
# FREE DOWNLOAD VIEWS
# ============================================================

# 🔥 REMOVE @login_required
def download_song(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    song.download_count += 1
    song.save()
    return redirect(song.audio_file.url)
    # 2. Stream the file from Cloudflare R2 through Django to force an instant attachment download
    r = requests.get(song.audio_file.url, stream=True) # type: ignore
    
    response = StreamingHttpResponse(
        r.iter_content(chunk_size=8192),
        content_type=r.headers.get('content-type', 'audio/mpeg')
    )
    
    # Clean the title for the file name (removing quotes or odd characters)
    clean_title = song.title.replace('"', '').replace("'", "")
    
    # This header is the secret sauce that forces an instant device save-dialog
    response['Content-Disposition'] = f'attachment; filename="{clean_title}.mp3"'
    response['Content-Length'] = r.headers.get('content-length')
    
    return response

def blog_list(request):
    posts = BlogPost.objects.filter(published=True).order_by('-published_at')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/list.html', {'page_obj': page_obj, 'posts': page_obj})

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    return render(request, 'blog/detail.html', {'post': post})


@login_required
def track_download(request, song_id):
    """Track download for stats (AJAX)"""
    song = get_object_or_404(Song, id=song_id)
    song.download_count += 1
    song.save()
    return JsonResponse({'status': 'success', 'downloads': song.download_count})


# ============================================================
# HOME
# ============================================================

def home(request):
     # Debug: Check what user is
    print(f"User: {request.user}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    print(f"User type: {type(request.user)}")
    
    # ... rest of your code
    # pro_artists = CustomUser.objects.filter(
#     is_artist=True,
#     is_verified=True
# ).order_by('-points')[:10]
    query = request.GET.get('q')
    category = request.GET.get('category')
    page_number = request.GET.get('page', 1)
    region_page = request.GET.get('region_page', 1)
    
    categories = [
        "Afrobeat", "Dancehall", "Pop", "Reggae", "Remix", 
        "Gospel", "Kadongo Kamu", "Hip Hop", "R&B", "Rock", 
        "Jazz", "Classical", "Electronic", "Folk", "Country", 
        "Blues", "Metal", "Amapiano", "Zouk", "Highlife"
    ]
    
    songs = Song.objects.filter(is_approved=True)
    all_artists = CustomUser.objects.filter(is_artist=True).order_by('-is_pro', '-is_verified')
    shop_items = Product.objects.filter().select_related('artist').order_by('artist__username')
    pro_artists = CustomUser.objects.filter(
    is_artist=True,
    is_verified=True
).order_by('-points')[:10]

    featured_mixes = DJMix.objects.filter(is_featured=True)[:6]
    recent_mixes = DJMix.objects.all().order_by('-release_date')[:6]
    
    featured_podcasts = Podcast.objects.filter(is_featured=True)[:6]
    recent_podcasts = Podcast.objects.all().order_by('-release_date')[:6]
    
    trending_songs = Song.objects.filter(
        is_approved=True,
        is_trending=True,
        trending_expiry__gt=timezone.now()
    ).order_by('-play_count')[:10]
    
    recent_songs = []
    if request.user.is_authenticated:
        recent_plays = RecentlyPlayed.objects.filter(
            user=request.user
        ).select_related('song')[:5]
        recent_songs = [play.song for play in recent_plays]
    daily_mix = None
    weekly_mix = None
    daily_mix_songs = []
    weekly_mix_songs = []
    
    if request.user.is_authenticated:
        try:
            daily_mix, weekly_mix = get_or_create_mixes(request)
            if daily_mix:
                daily_mix_songs = daily_mix.mix_songs.select_related('song', 'song__artist').all()[:10]
            if weekly_mix:
                weekly_mix_songs = weekly_mix.mix_songs.select_related('song', 'song__artist').all()[:10]
        except Exception as e:
            print(f"Mix error: {e}")
    public_playlists = Playlist.objects.filter(is_public=True).order_by('-play_count')[:6]
    
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    ninety_days_ago = today - timedelta(days=90)
    
    new_releases = Song.objects.filter(
        is_approved=True,
        release_date__gte=thirty_days_ago
    ).order_by('-release_date')[:20]
    
    recent_releases = Song.objects.filter(
        is_approved=True,
        release_date__lt=thirty_days_ago,
        release_date__gte=ninety_days_ago
    ).order_by('-release_date')[:12]
    
    timeless_hits = Song.objects.filter(
        is_approved=True,
        release_date__lt=ninety_days_ago
    ).order_by('-play_count')[:12]
    
    central_all = Song.objects.filter(is_approved=True, region='central').order_by('-play_count')
    eastern_all = Song.objects.filter(is_approved=True, region='eastern').order_by('-play_count')
    western_all = Song.objects.filter(is_approved=True, region='western').order_by('-play_count')
    northern_all = Song.objects.filter(is_approved=True, region='northern').order_by('-play_count')
    kampala_all = Song.objects.filter(is_approved=True, region='kampala').order_by('-play_count')
    
    central_paginator = Paginator(central_all, 20)
    eastern_paginator = Paginator(eastern_all, 20)
    western_paginator = Paginator(western_all, 20)
    northern_paginator = Paginator(northern_all, 20)
    kampala_paginator = Paginator(kampala_all, 20)
    
    central_page = central_paginator.get_page(region_page)
    eastern_page = eastern_paginator.get_page(region_page)
    western_page = western_paginator.get_page(region_page)
    northern_page = northern_paginator.get_page(region_page)
    kampala_page = kampala_paginator.get_page(region_page)
    
    region_songs = {
        'central': central_page,
        'eastern': eastern_page,
        'western': western_page,
        'northern': northern_page,
        'kampala': kampala_page,
    }
    
    region_pagination = {
        'central': {'has_next': central_page.has_next(), 'has_prev': central_page.has_previous(), 'page_num': central_page.number, 'total_pages': central_paginator.num_pages},
        'eastern': {'has_next': eastern_page.has_next(), 'has_prev': eastern_page.has_previous(), 'page_num': eastern_page.number, 'total_pages': eastern_paginator.num_pages},
        'western': {'has_next': western_page.has_next(), 'has_prev': western_page.has_previous(), 'page_num': western_page.number, 'total_pages': western_paginator.num_pages},
        'northern': {'has_next': northern_page.has_next(), 'has_prev': northern_page.has_previous(), 'page_num': northern_page.number, 'total_pages': northern_paginator.num_pages},
        'kampala': {'has_next': kampala_page.has_next(), 'has_prev': kampala_page.has_previous(), 'page_num': kampala_page.number, 'total_pages': kampala_paginator.num_pages},
    }
    
    artists_found = None
    if query:
        songs = songs.filter(
            Q(title__icontains=query) | 
            Q(artist__username__icontains=query) | 
            Q(genre__icontains=query)
        ).distinct()
        
        artists_found = all_artists.filter(username__icontains=query)
        shop_items = shop_items.filter(
            Q(name__icontains=query) | Q(artist__username__icontains=query)
        )
    
    if category:
        songs = songs.filter(genre=category)
    
    songs = songs.order_by('-release_date', '-created_at')
    
    paginator = Paginator(songs, 12)
    page_obj = paginator.get_page(page_number)
    
    moods = Mood.objects.filter(is_active=True).prefetch_related('songs')
    
    context = {
        'page_obj': page_obj,
        'songs': page_obj,
        'new_releases': new_releases,
        'recent_releases': recent_releases,
        'timeless_hits': timeless_hits,
        'query': query,
        'current_category': category,
        'categories': categories,
        'pro_artists': pro_artists,
        'trending_songs': trending_songs,
        'recent_songs': recent_songs,
        'shop_items': shop_items,
        'artists_found': artists_found,
        'public_playlists': public_playlists,
        'region_songs': region_songs,
        'featured_mixes': featured_mixes,
        'recent_mixes': recent_mixes,
        'featured_podcasts': featured_podcasts,
        'recent_podcasts': recent_podcasts,
        'moods': moods,
        'daily_mix': daily_mix,        # ← ADD THIS
        'weekly_mix': weekly_mix,      # ← ADD THIS
        'daily_mix_songs': daily_mix_songs,
        'weekly_mix_songs': weekly_mix_songs,
    }
    
    return render(request, 'index.html', context)


# ============================================================
# SONG DETAIL
# ============================================================

def song_detail(request, song_id):
    song = get_object_or_404(Song, id=song_id, is_approved=True)
    comments = song.comments.all()
    
    all_songs_list = Song.objects.filter(is_approved=True).values('id', 'title', 'artist__username', 'audio_file', 'cover_image')
    
    all_song_ids = list(Song.objects.filter(is_approved=True).values_list('id', flat=True).order_by('-created_at'))
    current_index = all_song_ids.index(song_id) if song_id in all_song_ids else -1
    
    prev_song_id = all_song_ids[current_index + 1] if current_index + 1 < len(all_song_ids) else None
    next_song_id = all_song_ids[current_index - 1] if current_index - 1 >= 0 else None
    
    prev_song = Song.objects.get(id=prev_song_id) if prev_song_id else None
    next_song = Song.objects.get(id=next_song_id) if next_song_id else None
    
    context = {
        'song': song,
        'comments': comments,
        'prev_song': prev_song,
        'next_song': next_song,
        'all_songs_list': all_songs_list,
        'hide_sidebar': True,
    }
    return render(request, 'song_detail.html', context)


# ============================================================
# PLAY SONG
# ============================================================

def play_song(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    song.play_count += 1
    song.save()
    
    if request.user.is_authenticated:
        RecentlyPlayed.objects.filter(user=request.user, song=song).delete()
        RecentlyPlayed.objects.create(
            user=request.user,
            song=song,
            played_at=timezone.now()
        )
    
    return JsonResponse({'status': 'success', 'play_count': song.play_count})


# ============================================================
# RADIO VIEW
# ============================================================

def radio_view(request, song_id):
    seed_song = get_object_or_404(Song, id=song_id, is_approved=True)
    
    similar_songs = Song.objects.filter(
        is_approved=True
    ).exclude(id=song_id).filter(
        Q(genre=seed_song.genre) |
       Q(artist__username=seed_song.artist.username) |
        Q(is_trending=True)
    ).distinct().order_by('-play_count')[:50]
    
    radio_songs = []
    for song in similar_songs:
        radio_songs.append({
            'id': song.id,
            'title': song.title,
            'artist': song.artist.username,
            'img': song.cover_image.url if song.cover_image else '',
            'audio': song.audio_file.url
        })
    
    radio_songs.insert(0, {
        'id': seed_song.id,
        'title': seed_song.title,
        'artist': seed_song.artist.username,
        'img': seed_song.cover_image.url if seed_song.cover_image else '',
        'audio': seed_song.audio_file.url
    })
    
    return JsonResponse({'songs': radio_songs, 'seed_song': seed_song.title})


# ============================================================
# USER AUTHENTICATION
# ============================================================

def user_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            if user.user_type == 'artist' or user.is_artist:
                return redirect('artist_dashboard')
            else:
                return redirect('home')
    else:
        form = CustomLoginForm()
    
    return render(request, 'login.html', {'form': form})


def user_signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Account created successfully! Welcome to EraTunez.")
            return redirect('home')
    else:
        form = UserSignupForm()
    
    return render(request, 'signup.html', {'form': form})


def artist_signup(request):
    if request.method == 'POST':
        form = ArtistSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Artist account created! You can now upload your music.")
            return redirect('artist_dashboard')
    else:
        form = ArtistSignupForm()
    
    return render(request, 'artist_signup.html', {'form': form})


def user_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')


# ============================================================
# COMMENTS
# ============================================================

def add_comment(request, song_id):
    if request.method == "POST":
        song = get_object_or_404(Song, id=song_id)
        text = request.POST.get('text')
        
        if text and request.user.is_authenticated:
            Comment.objects.create(song=song, user=request.user, text=text)
            request.user.points += 5
            request.user.save()
            return JsonResponse({'status': 'success', 'message': 'Comment posted!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Comment cannot be empty'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
@require_POST
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.user != request.user and not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'You cannot edit this comment'}, status=403)
    
    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'status': 'error', 'message': 'Comment cannot be empty'}, status=400)
    
    comment.text = text
    comment.is_edited = True
    comment.save()
    
    return JsonResponse({'status': 'success', 'message': 'Comment updated'})


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.user != request.user and not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'You cannot delete this comment'}, status=403)
    
    comment.delete()
    return JsonResponse({'status': 'success', 'message': 'Comment deleted'})


@login_required
@require_POST
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    like, created = CommentLike.objects.get_or_create(
        user=request.user,
        comment=comment
    )
    
    if created:
        comment.likes += 1
        comment.save()
        return JsonResponse({'status': 'success', 'action': 'liked', 'likes': comment.likes})
    else:
        like.delete()
        comment.likes -= 1
        comment.save()
        return JsonResponse({'status': 'success', 'action': 'unliked', 'likes': comment.likes})


@login_required
@require_POST
def pin_comment(request, comment_id):
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Admin only'}, status=403)
    
    comment = get_object_or_404(Comment, id=comment_id)
    comment.is_pinned = not comment.is_pinned
    comment.save()
    
    return JsonResponse({'status': 'success', 'is_pinned': comment.is_pinned})


def get_comments(request, song_id):
    try:
        song = get_object_or_404(Song, id=song_id)
        
        comments = Comment.objects.filter(
            song=song
        ).select_related('user').order_by('-created_at')
        
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': comment.id,
                'text': comment.text,
                'user': comment.user.username,
                'user_avatar': comment.user.profile_picture.url if comment.user.profile_picture and hasattr(comment.user, 'profile_picture') else None,
                'created_at': comment.created_at.strftime("%b %d, %Y at %I:%M %p"),
                'likes': comment.likes,
                'is_pinned': False,
                'reply_count': 0,
                'replies': [],
            })
        
        return JsonResponse({'comments': comments_data})
    
    except Exception as e:
        print(f"Error in get_comments: {e}")
        return JsonResponse({'comments': [], 'error': str(e)})


# ============================================================
# ARTIST DASHBOARD
# ============================================================

@login_required
def artist_dashboard(request):
    if not request.user.is_artist:
        messages.error(request, 'Access denied. Artist account required.')
        return redirect('home')
    
    if request.method == 'POST':
        form = SongForm(request.POST, request.FILES)
        if form.is_valid():
            song = form.save(commit=False)
            song.artist = request.user
            song.is_approved = False
            song.region = request.POST.get('region', 'all')
            
            youtube_url = request.POST.get('youtube_url')
            if youtube_url:
                song.youtube_url = youtube_url
                song.has_video = True
            
            lyrics = request.POST.get('lyrics')
            if lyrics and lyrics.strip():
                song.lyrics = lyrics.strip()
                song.has_lyrics = True
            
            song.save()
            
            selected_moods = request.POST.getlist('moods')
            for mood_id in selected_moods:
                try:
                    mood = Mood.objects.get(id=mood_id)
                    SongMood.objects.create(song=song, mood=mood)
                except Exception as e:
                    print(f"Error saving mood: {e}")
            
            messages.success(request, "Song uploaded! It will appear once approved by Admin.")
            return redirect('artist_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SongForm()
    
    my_songs = Song.objects.filter(artist=request.user).order_by('-created_at')
    
    total_plays = sum(s.play_count for s in my_songs)
    total_downloads = sum(s.download_count for s in my_songs)
    
    moods = Mood.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'songs': my_songs,
        'total_plays': total_plays,
        'total_downloads': total_downloads,
        'hide_sidebar': True,
        'moods': moods,
    }
    
    return render(request, 'artist_dashboard.html', context)


@login_required
def edit_song(request, song_id):
    song = get_object_or_404(Song, id=song_id, artist=request.user)
    if request.method == 'POST':
        form = SongForm(request.POST, request.FILES, instance=song)
        if form.is_valid():
            form.save()
            messages.success(request, "Song updated successfully!")
            return redirect('artist_dashboard')
    else:
        form = SongForm(instance=song)
    return render(request, 'edit_song.html', {'form': form, 'song': song})


@login_required
def delete_song(request, song_id):
    song = get_object_or_404(Song, id=song_id, artist=request.user)
    song.delete()
    messages.success(request, "Song deleted successfully!")
    return redirect('artist_dashboard')


def batch_upload(request):
    if request.method == 'POST' and request.user.is_authenticated:
        audio_files = request.FILES.getlist('audio_files')
        cover_image = request.FILES.get('cover_image')
        genre = request.POST.get('genre')
        region = request.POST.get('region', 'all')
        
        if not audio_files:
            messages.error(request, 'Please select at least one audio file.')
            return redirect('artist_dashboard')
        
        uploaded_count = 0
        failed_count = 0
        
        for audio in audio_files:
            if not audio.name.endswith('.mp3'):
                failed_count += 1
                continue
            
            duration = 180
            try:
                with tempfile.NamedTemporaryFile(delete=True, suffix='.mp3') as tmp_file:
                    for chunk in audio.chunks():
                        tmp_file.write(chunk)
                    tmp_file.flush()
                    
                    try:
                        from mutagen.mp3 import MP3
                        audio_mp3 = MP3(tmp_file.name)
                        duration = int(audio_mp3.info.length)
                    except:
                        pass
            except:
                pass
            
            song_title = audio.name.replace('.mp3', '').replace('_', ' ').replace('-', ' ')
            
            Song.objects.create(
                artist=request.user,
                title=song_title,
                audio_file=audio,
                cover_image=cover_image,
                genre=genre,
                region=region,
                duration=duration,
                is_approved=False,
                is_trending=False,
                play_count=0
            )
            uploaded_count += 1
        
        if uploaded_count > 0:
            messages.success(request, f'✅ Successfully uploaded {uploaded_count} songs! They will appear after admin approval.')
        if failed_count > 0:
            messages.warning(request, f'⚠️ {failed_count} file(s) were skipped (only MP3 files allowed).')
        
        return redirect('artist_dashboard')
    
    return redirect('artist_dashboard')


def request_boost(request, song_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return redirect('login')
    
    song = get_object_or_404(Song, id=song_id, artist=request.user)
    
    if request.method == 'POST':
        screenshot = request.FILES.get('screenshot')
        
        if screenshot:
            song.payment_screenshot = screenshot
            song.boost_paid = True
            song.boost_requested_at = timezone.now()
            song.save()
            
            messages.success(request, f'✅ Payment proof submitted for "{song.title}"! Admin will review within 24 hours.')
        else:
            messages.error(request, '❌ Please upload a payment screenshot.')
        
        return redirect('artist_dashboard')
    
    return redirect('artist_dashboard')


# ============================================================
# UPLOAD SONG (Standalone)
# ============================================================

def upload_song(request):
    if not request.user.is_artist:
        messages.error(request, 'Only artists can upload songs')
        return redirect('home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        genre = request.POST.get('genre')
        audio_file = request.FILES.get('audio_file')
        cover_image = request.FILES.get('cover_image')
        lyrics = request.POST.get('lyrics')
        youtube_url = request.POST.get('youtube_url')
        
        region = request.user.country if request.user.country else 'all'
        
        song = Song.objects.create(
            artist=request.user,
            title=title,
            genre=genre,
            audio_file=audio_file,
            cover_image=cover_image,
            lyrics=lyrics,
            youtube_url=youtube_url,
            region=region,
            is_approved=False
        )
        
        messages.success(request, f'Song "{title}" uploaded successfully! It will appear after admin approval.')
        return redirect('artist_dashboard')
    
    return redirect('artist_dashboard')


# ============================================================
# ARTIST PROFILE
# ============================================================

def artist_profile(request, username):
    artist = get_object_or_404(CustomUser, username=username, is_artist=True)
    songs = Song.objects.filter(artist__username=artist.username, is_approved=True).order_by('-created_at')
    merch = Product.objects.filter(artist__username=artist.username)
    total_plays = songs.aggregate(total=Sum('play_count'))['total'] or 0
    
    context = {
        'artist': artist,
        'songs': songs,
        'merch': merch,
        'total_plays': total_plays,
        'hide_sidebar': True, 
    }
    return render(request, 'artist_profile.html', context)


# ============================================================
# PLAYLISTS
# ============================================================

@login_required
def my_playlists(request):
    playlists = Playlist.objects.filter(user=request.user)
    return render(request, 'playlists.html', {'playlists': playlists, 'hide_sidebar': True})


def view_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    if not playlist.is_public and playlist.user != request.user:
        messages.error(request, 'This playlist is private')
        return redirect('home')
    
    playlist_songs = playlist.playlist_songs.select_related('song').all()
    songs = [ps.song for ps in playlist_songs]
    
    return render(request, 'playlist_detail.html', {
        'playlist': playlist,
        'songs': songs,
        'hide_sidebar': True,
    })


@login_required
def create_playlist(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        is_public = request.POST.get('is_public') == 'on'
        cover = request.FILES.get('cover_image')
        
        if name:
            playlist = Playlist.objects.create(
                name=name,
                user=request.user,
                is_public=is_public,
                cover_image=cover
            )
            messages.success(request, f'Playlist "{name}" created!')
            return redirect('view_playlist', playlist_id=playlist.id)
    
    return render(request, 'create_playlist.html', {'hide_sidebar': True})


@login_required
def add_to_playlist(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    
    if request.method == 'POST':
        playlist_id = request.POST.get('playlist_id')
        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        
        existing = PlaylistSong.objects.filter(playlist=playlist, song=song).first()
        if existing:
            messages.warning(request, f'"{song.title}" already in {playlist.name}')
        else:
            PlaylistSong.objects.create(
                playlist=playlist,
                song=song,
                order=playlist.playlist_songs.count()
            )
            messages.success(request, f'Added "{song.title}" to {playlist.name}')
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def delete_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    name = playlist.name
    playlist.delete()
    messages.success(request, f'Playlist "{name}" deleted')
    return redirect('my_playlists')


@login_required
def remove_from_playlist(request, playlist_id, song_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    song = get_object_or_404(Song, id=song_id)
    
    PlaylistSong.objects.filter(playlist=playlist, song=song).delete()
    messages.success(request, f'Removed "{song.title}" from {playlist.name}')
    
    return redirect('view_playlist', playlist_id=playlist.id)


# ============================================================
# ADS
# ============================================================

def track_ad_click(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    ad.clicks += 1
    ad.save()
    return redirect(ad.link_url)


def _advertise_request(request):
    if request.method == 'POST':
        ad = Ad(
            title=request.POST.get('title'),
            ad_type=request.POST.get('ad_type'),
            image=request.FILES.get('image'),
            link_url=request.POST.get('link_url'),
            advertiser_name=request.POST.get('advertiser_name'),
            advertiser_contact=request.POST.get('advertiser_contact'),
            advertiser_email=request.POST.get('advertiser_email'),
            payment_reference=request.POST.get('payment_reference'),
            amount_paid=request.POST.get('amount_paid', 0),
            is_active=False,
        )
        ad.save()
        messages.success(request, "Ad request submitted! Admin will review and activate within 24 hours.")
        return redirect('home')
    
    return render(request, 'advertise.html')


def advertise_request(request):
    return _advertise_request(request)


# ============================================================
# USER PROFILE
# ============================================================

@login_required
def user_profile(request):
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=user)
    
    return render(request, 'user_profile.html', {
        'form': form,
        'user': user,
        'hide_sidebar': True,
    })


# ============================================================
# RELEASES & TRENDING
# ============================================================

def releases_page(request):
    filter_type = request.GET.get('filter', 'new')
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    ninety_days_ago = today - timedelta(days=90)
    
    if filter_type == 'new':
        songs = Song.objects.filter(
            is_approved=True,
            release_date__gte=thirty_days_ago
        ).order_by('-release_date')
    elif filter_type == 'recent':
        songs = Song.objects.filter(
            is_approved=True,
            release_date__lt=thirty_days_ago,
            release_date__gte=ninety_days_ago
        ).order_by('-release_date')
    elif filter_type == 'timeless':
        songs = Song.objects.filter(
            is_approved=True,
            release_date__lt=ninety_days_ago
        ).order_by('-play_count')
    else:
        songs = Song.objects.filter(is_approved=True).order_by('-release_date')
    
    context = {
        'songs': songs,
        'filter': filter_type,
    }
    return render(request, 'releases.html', context)


def trending_page(request):
    trending_songs = Song.objects.filter(
        is_approved=True,
        is_trending=True,
        trending_expiry__gt=timezone.now()
    ).order_by('-play_count')
    
    return render(request, 'trending.html', {'trending_songs': trending_songs})


# ============================================================
# API ENDPOINTS
# ============================================================

def api_region_songs(request):
    region = request.GET.get('region')
    page = int(request.GET.get('page', 1))
    
    songs = Song.objects.filter(is_approved=True, region=region).order_by('-play_count')
    paginator = Paginator(songs, 20)
    page_obj = paginator.get_page(page)
    
    songs_data = []
    for song in page_obj:
        songs_data.append({
            'id': song.id,
            'title': song.title,
            'artist': song.artist.username,
            'audio': song.audio_file.url,
        })
    
    return JsonResponse({
        'songs': songs_data,
        'pagination': {
            'has_next': page_obj.has_next(),
            'has_prev': page_obj.has_previous(),
            'page_num': page_obj.number,
            'total_pages': paginator.num_pages,
        }
    })


def get_song_video(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    return JsonResponse({
        'has_video': song.has_video and bool(song.youtube_url),
        'video_url': song.get_youtube_embed_url() if hasattr(song, 'get_youtube_embed_url') else None,
        'youtube_url': song.youtube_url,
    })


def get_song_lyrics(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    
    song.lyrics_views += 1
    song.save(update_fields=['lyrics_views'])
    
    lyrics_data = {
        'has_lyrics': song.has_lyrics,
        'lyrics': song.lyrics,
        'is_synced': is_lrc_format(song.lyrics) if song.lyrics else False,
    }
    
    if lyrics_data['is_synced']:
        lyrics_data['synced_lines'] = parse_lrc(song.lyrics)
    
    return JsonResponse(lyrics_data)


def is_lrc_format(lyrics):
    if not lyrics:
        return False
    return bool(re.search(r'\[\d{2}:\d{2}(?:\.\d{2})?\]', lyrics))


def parse_lrc(lyrics):
    lines = []
    pattern = r'\[(\d{2}):(\d{2})(?:\.(\d{2}))?\](.*)'
    
    for line in lyrics.split('\n'):
        match = re.search(pattern, line)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            milliseconds = int(match.group(3)) if match.group(3) else 0
            time_ms = (minutes * 60 + seconds) * 1000 + milliseconds
            text = match.group(4).strip()
            lines.append({
                'time': time_ms,
                'time_str': f"{minutes:02d}:{seconds:02d}",
                'text': text
            })
    
    return lines


# ============================================================
# AI RECOMMENDATIONS
# ============================================================

def get_ai_recommendations(request):
    try:
        if not request.user.is_authenticated:
            recommendations = Song.objects.filter(is_approved=True).order_by('-play_count')[:20]
        else:
            recommendations = get_recommendations_for_user(request)
            
            if recommendations is None or not recommendations.exists():
                recommendations = Song.objects.filter(is_approved=True).order_by('-play_count')[:20]
        
        recommendations_data = []
        for song in recommendations[:20]:
            recommendations_data.append({
                'id': song.id,
                'title': song.title,
                'artist': song.artist.username,
                'img': song.cover_image.url if song.cover_image else '/static/default-cover.png',
                'audio': song.audio_file.url,
                'reason': get_recommendation_reason(song, request.user) if request.user.is_authenticated else "Trending now"
            })
        
        return JsonResponse({'recommendations': recommendations_data})
    
    except Exception as e:
        print(f"Recommendation error: {e}")
        return JsonResponse({'recommendations': []})


def get_recommendations_for_user(request):
    try:
        liked_songs = UserSongInteraction.objects.filter(
            user=request.user, 
            interaction_type='like'
        ).values_list('song_id', flat=True)
        
        recent_plays = UserListeningHistory.objects.filter(
            user=request.user,
            played_at__gte=timezone.now() - timedelta(days=30)
        ).values_list('song_id', flat=True).distinct()
        
        user_songs = set(liked_songs) | set(recent_plays)
        
        if not user_songs:
            return None
        
        preferred_genres = Song.objects.filter(id__in=user_songs).values_list('genre', flat=True).distinct()
        preferred_artists = Song.objects.filter(id__in=user_songs).values_list('artist', flat=True).distinct()
        preferred_regions = Song.objects.filter(id__in=user_songs).values_list('region', flat=True).distinct()
        
        similar_songs = Song.objects.filter(
            is_approved=True
        ).exclude(
            id__in=user_songs
        ).filter(
            Q(genre__in=preferred_genres) |
            Q(artist__in=preferred_artists) |
            Q(region__in=preferred_regions)
        ).order_by('-play_count')[:30]
        
        return similar_songs
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return None


def get_recommendation_reason(song, user):
    try:
        user_genres = Song.objects.filter(
            userlisteninghistory__user=user
        ).values_list('genre', flat=True).distinct()
        
        if song.genre in user_genres:
            return f"Because you like {song.genre}"
        
        user_artists = Song.objects.filter(
            userlisteninghistory__user=user
        ).values_list('artist__username', flat=True).distinct()
        
        if song.artist.username in user_artists:
            return f"Because you listen to {song.artist.username}"
        
        user_regions = Song.objects.filter(
            userlisteninghistory__user=user
        ).values_list('region', flat=True).distinct()
        
        if song.region in user_regions and song.region != 'all':
            return f"Popular in your region"
            
    except:
        pass
    
    return "Recommended for you"


# ============================================================
# CHARTS
# ============================================================

def get_genre_color(genre):
    colors = {
        'Afrobeat': '#FF6B35',
        'Dancehall': '#F7C948',
        'Gospel': '#4CAF50',
        'Kadongo Kamu': '#8B4513',
        'Hip Hop': '#E91E63',
        'R&B': '#9C27B0',
        'Amapiano': '#00BCD4',
        'Reggae': '#FF5722',
        'Zouk': '#FF4081',
        'Highlife': '#FFC107',
        'Soukous': '#2196F3',
        'Bongo Flava': '#4CAF50',
        'pop': '#3F51B5',
    }
    return colors.get(genre, '#1DB954')


def charts_page(request):
    chart_type = request.GET.get('type', 'songs')
    period = request.GET.get('period', 'week')
    genre = request.GET.get('genre', 'all')
    
    today = timezone.now().date()
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=7)
    
    context = {
        'chart_type': chart_type,
        'period': period,
        'selected_genre': genre,
        'genres': Song.GENRE_CHOICES,
    }
    
    if chart_type == 'songs':
        songs_qs = Song.objects.filter(is_approved=True)
        
        if genre != 'all':
            songs_qs = songs_qs.filter(genre=genre)
        
        songs_with_plays = []
        for song in songs_qs:
            period_plays = RecentlyPlayed.objects.filter(
                song=song,
                played_at__date__gte=start_date
            ).count()
            songs_with_plays.append({
                'song': song,
                'period_plays': period_plays
            })
        
        songs_with_plays.sort(key=lambda x: x['period_plays'], reverse=True)
        
        songs = [item['song'] for item in songs_with_plays[:50]]
        
        for i, item in enumerate(songs_with_plays[:50]):
            songs[i].period_plays = item['period_plays']
        
        context['songs'] = songs
        
        songs_list = []
        for song in songs[:50]:
            songs_list.append({
                'id': song.id,
                'title': song.title,
                'artist': song.artist.username,
                'img': song.cover_image.url if song.cover_image else '/static/default-cover.png',
                'audio': song.audio_file.url,
            })
        context['page_songs_json'] = json.dumps(songs_list)
        
    elif chart_type == 'artists':
        artists = CustomUser.objects.filter(is_artist=True)
        artists_with_plays = []
        for artist in artists:
            period_plays = RecentlyPlayed.objects.filter(
                song__artist=artist,
                played_at__date__gte=start_date
            ).count()
            if period_plays > 0:
                artist.period_plays = period_plays
                artist.song_count = Song.objects.filter(artist__username=artist.username, is_approved=True).count()
                artists_with_plays.append(artist)
        
        artists_with_plays.sort(key=lambda x: x.period_plays, reverse=True)
        context['artists'] = artists_with_plays[:50]
        
    elif chart_type == 'genres':
        genres = []
        for genre_choice in Song.GENRE_CHOICES:
            genre_name = genre_choice[0]
            play_count = RecentlyPlayed.objects.filter(
                song__genre=genre_name,
                song__is_approved=True,
                played_at__date__gte=start_date
            ).count()
            
            genres.append({
                'name': genre_name,
                'play_count': play_count,
                'song_count': Song.objects.filter(genre=genre_name, is_approved=True).count(),
                'color': get_genre_color(genre_name)
            })
        
        genres.sort(key=lambda x: x['play_count'], reverse=True)
        context['genres'] = genres[:10]
    
    return render(request, 'charts.html', context)


# ============================================================
# LISTENING HISTORY & STATS
# ============================================================

def listening_history(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to view your listening history')
        return redirect('login')
    
    filter_type = request.GET.get('filter', 'all')
    
    today = timezone.now().date()
    if filter_type == 'week':
        start_date = today - timedelta(days=7)
    elif filter_type == 'month':
        start_date = today - timedelta(days=30)
    elif filter_type == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = None
    
    history = UserListeningHistory.objects.filter(
        user=request.user
    ).select_related('song', 'song__artist')
    
    if start_date:
        history = history.filter(played_at__date__gte=start_date)
    
    history = history.order_by('-played_at')
    
    paginator = Paginator(history, 20)
    page_number = request.GET.get('page', 1)
    history_page = paginator.get_page(page_number)
    
    total_songs = history.count()
    unique_songs = history.values('song').distinct().count()
    unique_artists = history.values('song__artist').distinct().count()
    
    total_minutes = total_songs * 3.5
    total_hours = round(total_minutes / 60, 1)
    
    completed_count = history.filter(completed=True).count()
    completion_rate = round((completed_count / total_songs * 100), 1) if total_songs > 0 else 0
    
    context = {
        'history': history_page,
        'filter': filter_type,
        'total_songs': total_songs,
        'unique_songs': unique_songs,
        'unique_artists': unique_artists,
        'total_hours': total_hours,
        'completion_rate': completion_rate,
    }
    
    return render(request, 'listening_history.html', context)


def listening_stats(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to view your stats')
        return redirect('login')
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    all_history = UserListeningHistory.objects.filter(user=request.user)
    total_plays = all_history.count()
    unique_songs = all_history.values('song').distinct().count()
    unique_artists = all_history.values('song__artist').distinct().count()
    
    week_history = all_history.filter(played_at__date__gte=week_ago)
    week_plays = week_history.count()
    
    month_history = all_history.filter(played_at__date__gte=month_ago)
    month_plays = month_history.count()
    
    most_played_songs = all_history.values(
        'song__id', 'song__title', 'song__artist__username', 'song__cover_image', 'song__audio_file'
    ).annotate(
        play_count=Count('id')
    ).order_by('-play_count')[:10]
    
    most_played_artists = all_history.values(
        'song__artist__id', 'song__artist__username'
    ).annotate(
        play_count=Count('id')
    ).order_by('-play_count')[:10]
    
    hour_counts = {}
    for record in all_history:
        hour = record.played_at.hour
        hour_str = str(hour).zfill(2)
        hour_counts[hour_str] = hour_counts.get(hour_str, 0) + 1
    
    hour_stats = [{'hour': k, 'count': v} for k, v in sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)][:5]
    
    day_counts = {}
    for record in all_history:
        weekday = record.played_at.weekday() + 1
        day_counts[weekday] = day_counts.get(weekday, 0) + 1
    
    day_stats = [{'weekday': k, 'count': v} for k, v in sorted(day_counts.items(), key=lambda x: x[1], reverse=True)]
    
    listening_dates = all_history.dates('played_at', 'day').distinct()
    listening_dates = [date for date in listening_dates]
    
    current_streak = 0
    longest_streak = 0
    streak = 0
    last_date = None
    
    for date in sorted(listening_dates, reverse=True):
        if last_date is None:
            streak = 1
        elif (last_date - date).days == 1:
            streak += 1
        else:
            break
        last_date = date
        current_streak = streak
    
    streak = 0
    last_date = None
    for date in sorted(listening_dates):
        if last_date is None:
            streak = 1
        elif (date - last_date).days == 1:
            streak += 1
        else:
            streak = 1
        longest_streak = max(longest_streak, streak)
        last_date = date
    
    context = {
        'total_plays': total_plays,
        'unique_songs': unique_songs,
        'unique_artists': unique_artists,
        'week_plays': week_plays,
        'month_plays': month_plays,
        'most_played_songs': most_played_songs,
        'most_played_artists': most_played_artists,
        'hour_stats': hour_stats,
        'day_stats': day_stats,
        'current_streak': current_streak,
        'longest_streak': longest_streak,
    }
    
    return render(request, 'listening_stats.html', context)


# ============================================================
# DJ MIXES & PODCASTS
# ============================================================

def all_mixes(request):
    mixes = DJMix.objects.all().order_by('-release_date')
    
    context = {
        'mixes': mixes,
        'hide_sidebar': True,
    }
    return render(request, 'all_mixes.html', context)


def all_podcasts(request):
    podcasts = Podcast.objects.all().order_by('-season_number', '-episode_number')
    
    context = {
        'podcasts': podcasts,
        'hide_sidebar': True,
    }
    return render(request, 'all_podcasts.html', context)


@csrf_exempt
def track_podcast_play(request, podcast_id):
    if request.method == 'POST':
        try:
            podcast = Podcast.objects.get(id=podcast_id)
            podcast.play_count += 1
            podcast.save()
            return JsonResponse({'status': 'success'})
        except Podcast.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def track_song_interaction(request, song_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error'}, status=401)
    
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                interaction_type = data.get('type')
            else:
                interaction_type = request.POST.get('type')
            
            song = get_object_or_404(Song, id=song_id)
            
            UserSongInteraction.objects.create(
                user=request.user,
                song=song,
                interaction_type=interaction_type
            )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def track_listening_history(request, song_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error'}, status=401)
    
    if request.method == 'POST':
        try:
            song = get_object_or_404(Song, id=song_id)
            
            UserListeningHistory.objects.create(
                user=request.user,
                song=song,
                played_at=timezone.now()
            )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def track_completion(request, song_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error'}, status=401)
    
    if request.method == 'POST':
        try:
            song = get_object_or_404(Song, id=song_id)
            
            history = UserListeningHistory.objects.filter(
                user=request.user,
                song=song
            ).last()
            
            if history:
                history.completed = True
                history.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)


# ============================================================
# ALL ARTISTS
# ============================================================

# THE FIX - add list() to force evaluation:
def all_artists(request):
    filter_type = request.GET.get('filter', 'all')
    page_number = request.GET.get('page', 1)

    if filter_type == 'pro':
        artists_list = list(CustomUser.objects.filter(
            is_artist=True,
            is_pro=True
        ).order_by('-points'))
    elif filter_type == 'verified':
        artists_list = list(CustomUser.objects.filter(
            is_artist=True,
            is_verified=True
        ).order_by('-points'))
    else:
        artists_list = list(CustomUser.objects.filter(
            is_artist=True
        ).order_by('-is_pro', '-is_verified', '-points'))

    for artist in artists_list:
        artist.song_count = Song.objects.filter(
            artist__username=artist.username, is_approved=True
        ).count()
        total_plays = Song.objects.filter(
            artist__username=artist.username, is_approved=True
        ).aggregate(total=Sum('play_count'))['total']
        artist.total_plays = total_plays if total_plays else 0

    paginator = Paginator(artists_list, 20)
    artists = paginator.get_page(page_number)

    context = {
        'artists': artists,
        'filter': filter_type,
    }
    return render(request, 'all_artists.html', context)
    context = {
        'artists': artists,
        'filter': filter_type,
    }

# ============================================================
# DAILY/WEEKLY MIXES
# ============================================================

def generate_daily_mix(user):
    recent_plays = UserListeningHistory.objects.filter(
        user=user,
        played_at__gte=timezone.now() - timedelta(days=7)
    ).values_list('song_id', flat=True).distinct()
    
    liked_songs = UserSongInteraction.objects.filter(
        user=user,
        interaction_type='like'
    ).values_list('song_id', flat=True)
    
    user_songs = set(recent_plays) | set(liked_songs)
    
    if not user_songs:
        return Song.objects.filter(is_approved=True).order_by('-play_count')[:25]
    
    favorite_genres = Song.objects.filter(id__in=user_songs).values_list('genre', flat=True).distinct()
    favorite_artists = Song.objects.filter(id__in=user_songs).values_list('artist', flat=True).distinct()
    
    recommended = Song.objects.filter(
        is_approved=True
    ).exclude(
        id__in=user_songs
    ).filter(
        Q(genre__in=favorite_genres) | Q(artist__in=favorite_artists)
    ).order_by('-play_count')[:25]
    
    if recommended.count() < 25:
        trending = Song.objects.filter(
            is_approved=True
        ).exclude(
            id__in=user_songs
        ).order_by('-play_count')[:25 - recommended.count()]
        recommended = list(recommended) + list(trending)
    
    return recommended[:25]


def generate_weekly_mix(user):
    all_plays = UserListeningHistory.objects.filter(
        user=user
    ).values_list('song_id', flat=True).distinct()
    
    liked_songs = UserSongInteraction.objects.filter(
        user=user,
        interaction_type='like'
    ).values_list('song_id', flat=True)
    
    user_songs = set(all_plays) | set(liked_songs)
    
    if not user_songs:
        return Song.objects.filter(is_approved=True).order_by('-play_count')[:50]
    
    genre_counts = Song.objects.filter(id__in=user_songs).values('genre').annotate(
        count=Count('id')
    ).order_by('-count')
    
    artist_counts = Song.objects.filter(id__in=user_songs).values('artist').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    recommended = []
    
    for artist in artist_counts:
        artist_songs = Song.objects.filter(
            is_approved=True,
            artist_id=artist['artist']
        ).exclude(
            id__in=user_songs
        ).order_by('-play_count')[:10]
        recommended.extend(list(artist_songs))
    
    for genre in genre_counts[:3]:
        genre_songs = Song.objects.filter(
            is_approved=True,
            genre=genre['genre']
        ).exclude(
            id__in=user_songs
        ).exclude(
            id__in=[s.id for s in recommended]
        ).order_by('-play_count')[:10]
        recommended.extend(list(genre_songs))
    
    seen = set()
    unique_recommended = []
    for song in recommended:
        if song.id not in seen:
            seen.add(song.id)
            unique_recommended.append(song)
    
    return unique_recommended[:50]


def get_or_create_mixes(request):
    
    # If user is not logged in, return nothing
    if not request.user.is_authenticated:
        return None, None
    
    # Get the actual user object
    current_user = request.user
    
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    
    daily_mix = UserMix.objects.filter(
        user=current_user,  # ← Use current_user instead of request.user
        mix_type='daily',
        created_at__date=today
    ).first()
    
    if not daily_mix:
        daily_mix = UserMix.objects.create(
            user=current_user,  # ← Use current_user here too
            mix_type='daily',
            name=f"Daily Mix • {today.strftime('%b %d')}",
            expires_at=today_start + timedelta(days=1)
        )
        
        songs = generate_daily_mix(current_user)  # ← Pass current_user
        for i, song in enumerate(songs):
            MixSong.objects.create(
                mix=daily_mix,
                song=song,
                order=i,
                reason=get_mix_reason(song, current_user)  # ← Pass current_user
            )
    
    days_since_monday = today.weekday()
    monday_date = today - timedelta(days=days_since_monday)
    monday_start = timezone.make_aware(datetime.combine(monday_date, datetime.min.time()))
    
    weekly_mix = UserMix.objects.filter(
        user=current_user,  # ← Use current_user
        mix_type='weekly',
        created_at__date__gte=monday_date
    ).first()
    
    if not weekly_mix:
        weekly_mix = UserMix.objects.create(
            user=current_user,  # ← Use current_user
            mix_type='weekly',
            name=f"Weekly Mix • Week of {monday_date.strftime('%b %d')}",
            expires_at=monday_start + timedelta(days=7)
        )
        
        songs = generate_weekly_mix(current_user)  # ← Pass current_user
        for i, song in enumerate(songs):
            MixSong.objects.create(
                mix=weekly_mix,
                song=song,
                order=i,
                reason=get_mix_reason(song, current_user)  # ← Pass current_user
            )
    
    return daily_mix, weekly_mix


def get_mix_reason(song, user):
    if UserListeningHistory.objects.filter(user=user, song=song).exists():
        return "Because you listened to similar songs"
    elif UserSongInteraction.objects.filter(user=user, song__genre=song.genre).exists():
        return f"Because you like {song.genre}"
    else:
        return "Recommended based on your taste"


def view_mix(request, mix_id):
    mix = get_object_or_404(UserMix, id=mix_id)
    
    if mix.user != request.user:
        messages.error(request, "This mix doesn't belong to you")
        return redirect('home')
    
    mix_songs = mix.mix_songs.select_related('song', 'song__artist').all()
    
    mix_songs_json = []
    for item in mix_songs:
        mix_songs_json.append({
            'id': item.song.id,
            'title': item.song.title,
            'artist': item.song.artist.username,
            'img': item.song.cover_image.url if item.song.cover_image else '/static/default-cover.png',
            'audio': item.song.audio_file.url,
        })
    
    context = {
        'mix': mix,
        'mix_songs': mix_songs,
        'mix_songs_json': json.dumps(mix_songs_json),
    }
    return render(request, 'mix_detail.html', context)


# ============================================================
# FOLLOW SYSTEM
# ============================================================

@login_required
@require_POST
def follow_artist(request, artist_id):
    try:
        artist = CustomUser.objects.get(id=artist_id, is_artist=True)
        
        if request.user == artist:
            return JsonResponse({'status': 'error', 'message': 'You cannot follow yourself'}, status=400)
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=artist
        )
        
        if created:
            return JsonResponse({'status': 'success', 'action': 'followed', 'message': f'You are now following {artist.username}'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Already following this artist'}, status=400)
            
    except CustomUser.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Artist not found'}, status=404)


@login_required
@require_POST
def unfollow_artist(request, artist_id):
    try:
        artist = CustomUser.objects.get(id=artist_id, is_artist=True)
        
        deleted, _ = Follow.objects.filter(
            follower=request.user,
            following=artist
        ).delete()
        
        if deleted:
            return JsonResponse({'status': 'success', 'action': 'unfollowed', 'message': f'You unfollowed {artist.username}'})
        else:
            return JsonResponse({'status': 'error', 'message': 'You were not following this artist'}, status=400)
            
    except CustomUser.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Artist not found'}, status=404)


def get_follow_status(request, artist_id):
    if not request.user.is_authenticated:
        return JsonResponse({'is_following': False})
    
    try:
        artist = CustomUser.objects.get(id=artist_id, is_artist=True)
        is_following = Follow.objects.filter(
            follower=request.user,
            following=artist
        ).exists()
        return JsonResponse({'is_following': is_following})
    except CustomUser.DoesNotExist:
        return JsonResponse({'is_following': False})


def following_feed(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to see your feed')
        return redirect('login')
    
    following_artists = Follow.objects.filter(
        follower=request.user
    ).values_list('following', flat=True)
    
    feed_songs = Song.objects.filter(
        artist__in=following_artists,
        is_approved=True
    ).order_by('-created_at')
    
    paginator = Paginator(feed_songs, 20)
    page_number = request.GET.get('page', 1)
    songs_page = paginator.get_page(page_number)
    
    context = {
        'feed_songs': songs_page,
        'total_following': following_artists.count(),
    }
    return render(request, 'following_feed.html', context)


def followers_list(request, username):
    artist = get_object_or_404(CustomUser, username=username, is_artist=True)
    followers = Follow.objects.filter(following=artist).select_related('follower')
    
    context = {
        'artist': artist,
        'followers': followers,
        'total_followers': followers.count(),
    }
    return render(request, 'followers_list.html', context)


def following_list(request, username):
    user = get_object_or_404(CustomUser, username=username)
    following = Follow.objects.filter(follower=user).select_related('following')
    
    context = {
        'profile_user': user,
        'following': following,
        'total_following': following.count(),
    }
    return render(request, 'following_list.html', context)


# ============================================================
# BROWSE & OTHER
# ============================================================

def browse(request):
    songs = Song.objects.filter(is_approved=True).order_by('-created_at')
    paginator = Paginator(songs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    trending_songs = Song.objects.filter(is_approved=True, is_trending=True).order_by('-play_count')[:10]
    
    recommended_songs = []
    if request.user.is_authenticated:
        recent_plays = RecentlyPlayed.objects.filter(user=request.user).select_related('song')[:5]
        if recent_plays:
            genres = [play.song.genre for play in recent_plays if play.song.genre]
            if genres:
                recommended_songs = Song.objects.filter(
                    is_approved=True,
                    genre__in=genres
                ).exclude(play_count=0).order_by('-play_count')[:10]
    
    if not recommended_songs:
        recommended_songs = Song.objects.filter(is_approved=True).order_by('-play_count')[:10]
    
    return render(request, 'browse.html', {
        'page_obj': page_obj,
        'songs': page_obj,
        'trending_songs': trending_songs,
        'recommended_songs': recommended_songs,
        'hide_sidebar': True,
    })


def like_song(request, song_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    
    song = get_object_or_404(Song, id=song_id)
    
    if request.user in song.likes.all():
        song.likes.remove(request.user)
        liked = False
    else:
        song.likes.add(request.user)
        liked = True
    
    return JsonResponse({'liked': liked, 'count': song.likes.count()})


def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    songs = Song.objects.filter(
        Q(title__icontains=query) | Q(artist__username__icontains=query),
        is_approved=True
    ).distinct()[:5]
    
    for song in songs:
        results.append({
            'title': song.title,
            'subtitle': f"Song by {song.artist.username} • {song.play_count} plays",
            'icon': 'bi bi-music-note-beamed',
            'type': 'Song',
            'url': f'/song/{song.id}/'
        })
    
    artists = CustomUser.objects.filter(
        Q(username__icontains=query),
        is_artist=True
    )[:5]
    
    for artist in artists:
        song_count = Song.objects.filter(artist__username=artist.username, is_approved=True).count()
        results.append({
            'title': artist.username,
            'subtitle': f"Artist • {song_count} songs • {artist.followers.count()} followers",
            'icon': 'bi bi-mic',
            'type': 'Artist',
            'url': f'/artist/{artist.username}/'
        })
    
    if request.user.is_authenticated:
        playlists = Playlist.objects.filter(
            Q(name__icontains=query),
            user=request.user
        )[:3]
        
        for playlist in playlists:
            results.append({
                'title': playlist.name,
                'subtitle': f"Playlist • {playlist.song_count()} songs",
                'icon': 'bi bi-music-note-list',
                'type': 'Playlist',
                'url': f'/playlist/{playlist.id}/'
            })
    
    mixes = DJMix.objects.filter(
        Q(title__icontains=query) | Q(dj_name__icontains=query)
    )[:3]
    
    for mix in mixes:
        results.append({
            'title': mix.title,
            'subtitle': f"DJ Mix by {mix.dj_name}",
            'icon': 'bi bi-vinyl-fill',
            'type': 'DJ Mix',
            'url': f'/mixes/'
        })
    
    podcasts = Podcast.objects.filter(
        Q(title__icontains=query) | Q(host_name__icontains=query)
    )[:3]
    
    for podcast in podcasts:
        results.append({
            'title': podcast.title,
            'subtitle': f"Podcast by {podcast.host_name} • S{podcast.season_number} E{podcast.episode_number}",
            'icon': 'bi bi-mic-fill',
            'type': 'Podcast',
            'url': f'/podcasts/'
        })
    
    return JsonResponse({'results': results})


@login_required
def request_pro(request):
    if not request.user.is_artist:
        messages.error(request, 'Only artists can request PRO status')
        return redirect('artist_dashboard')
    
    if request.method == 'POST':
        plan = request.POST.get('plan')
        payment_reference = request.POST.get('payment_reference')
        screenshot = request.FILES.get('screenshot')
        
        if plan == 'monthly':
            amount = 20000
        elif plan == 'yearly':
            amount = 200000
        else:
            messages.error(request, 'Invalid plan selected')
            return redirect('artist_dashboard')
        
        pro_request = ProRequest.objects.create(
            artist=request.user,
            plan=plan,
            payment_reference=payment_reference,
            payment_screenshot=screenshot,
            amount=amount,
            status='pending'
        )
        
        messages.success(request, f'PRO request submitted! Admin will review within 24 hours.')
        return redirect('artist_dashboard')
    
    return redirect('artist_dashboard')


def moods_page(request):
    moods = Mood.objects.filter(is_active=True)
    return render(request, 'moods.html', {'moods': moods})


def mood_playlist(request, mood_slug):
    mood = get_object_or_404(Mood, slug=mood_slug, is_active=True)
    
    song_moods = SongMood.objects.filter(mood=mood).select_related('song', 'song__artist')
    
    songs = []
    for sm in song_moods:
        songs.append(sm.song)
    
    songs_json = []
    for song in songs:
        songs_json.append({
            'id': song.id,
            'title': song.title,
            'artist': song.artist.username,
            'img': song.cover_image.url if song.cover_image else '/static/default-cover.png',
            'audio': song.audio_file.url,
        })
    
    context = {
        'mood': mood,
        'songs': songs,
        'songs_json': json.dumps(songs_json),
        'hide_sidebar': True,
    }
    return render(request, 'mood_playlist.html', context)


def region_page(request, country):
    country_info = {
        'uganda': {'name': 'Uganda', 'flag': '🇺🇬'},
        'kenya': {'name': 'Kenya', 'flag': '🇰🇪'},
        'tanzania': {'name': 'Tanzania', 'flag': '🇹🇿'},
        'rwanda': {'name': 'Rwanda', 'flag': '🇷🇼'},
        'burundi': {'name': 'Burundi', 'flag': '🇧🇮'},
        'south-sudan': {'name': 'South Sudan', 'flag': '🇸🇸'},
    }
    
    info = country_info.get(country, {'name': country.title(), 'flag': '🌍'})
    
    songs = Song.objects.filter(
        is_approved=True,
        region__icontains=info['name'].lower()
    ).order_by('-play_count')[:50]
    
    if not songs:
        songs = Song.objects.filter(is_approved=True).order_by('-play_count')[:20]
    
    context = {
        'songs': songs,
        'region_name': info['name'],
        'region_flag': info['flag'],
        'hide_sidebar': True,
    }
    return render(request, 'region_page.html', context)


def get_country_counts(request):
    countries = ['uganda', 'kenya', 'tanzania', 'rwanda', 'burundi', 'south-sudan']
    country_names = {'uganda': 'uganda', 'kenya': 'kenya', 'tanzania': 'tanzania', 
                     'rwanda': 'rwanda', 'burundi': 'burundi', 'south-sudan': 'south sudan'}
    
    counts = {}
    for country in countries:
        counts[country] = Song.objects.filter(
            is_approved=True, 
            region__icontains=country_names[country]
        ).count()
    
    return JsonResponse(counts)


# ============================================================
# LEGAL PAGES
# ============================================================

def privacy_policy(request):
    context = {
        'title': 'Privacy Policy',
        'last_updated': 'May 27, 2026',
        'hide_sidebar': True,
    }
    return render(request, 'legal/privacy_policy.html', context)


def terms_of_service(request):
    context = {
        'title': 'Terms of Service',
        'last_updated': 'May 27, 2026',
        'hide_sidebar': True,
    }
    return render(request, 'legal/terms_of_service.html', context)


def about_us(request):
    context = {
        'title': 'About EraTunez',
        'hide_sidebar': True,
    }
    return render(request, 'legal/about_us.html', context)


def contact_us(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        return redirect('contact_us')
    
    context = {
        'title': 'Contact Us',
        'hide_sidebar': True,
    }
    return render(request, 'legal/contact_us.html', context)


def cookie_policy(request):
    context = {
        'title': 'Cookie Policy',
        'last_updated': 'May 27, 2026',
        'hide_sidebar': True,
    }
    return render(request, 'legal/cookie_policy.html', context)