from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # --- Public Pages ---
    path('', views.home, name='home'),
    path('song/<int:song_id>/', views.song_detail, name='song_detail'),
    path('artist/<str:username>/', views.artist_profile, name='artist_profile'),

    # --- Auth URLs ---
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('customuser/signup/', views.artist_signup, name='artist_signup'),
    path('logout/', views.user_logout, name='logout'),

    # --- Logic Routes ---
    path('play-song/<int:song_id>/', views.play_song, name='play_song'),
    path('download/<int:song_id>/', views.download_song, name='download_song'),
    path('radio/<int:song_id>/', views.radio_view, name='radio_view'),
    path('track-download/<int:song_id>/', views.track_download, name='track_download'),

    # --- Comments ---
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('comment/add/<int:song_id>/', views.add_comment, name='add_comment'),
    path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comment/like/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('comment/pin/<int:comment_id>/', views.pin_comment, name='pin_comment'),
    path('comments/<int:song_id>/', views.get_comments, name='get_comments'),

    # --- Artist Dashboard & Actions ---
    path('dashboard/', views.artist_dashboard, name='artist_dashboard'),
    path('song/edit/<int:song_id>/', views.edit_song, name='edit_song'),
    path('song/delete/<int:song_id>/', views.delete_song, name='delete_song'),
    path('batch-upload/', views.batch_upload, name='batch_upload'),
    path('request-boost/<int:song_id>/', views.request_boost, name='request_boost'),
    path('upload-song/', views.upload_song, name='upload_song'),

    # --- Likes ---
    path('like-song/<int:song_id>/', views.like_song, name='like_song'),

    # --- Playlists ---
    path('playlists/', views.my_playlists, name='my_playlists'),
    path('playlist/<int:playlist_id>/', views.view_playlist, name='view_playlist'),
    path('playlist/create/', views.create_playlist, name='create_playlist'),
    path('playlist/<int:playlist_id>/delete/', views.delete_playlist, name='delete_playlist'),
    path('playlist/<int:playlist_id>/remove/<int:song_id>/', views.remove_from_playlist, name='remove_from_playlist'),
    path('playlist/add/<int:song_id>/', views.add_to_playlist, name='add_to_playlist'),

    # --- Browse & Discovery ---
    path('browse/', views.browse, name='browse'),
    path('releases/', views.releases_page, name='releases_page'),
    path('trending/', views.trending_page, name='trending_page'),
    path('charts/', views.charts_page, name='charts'),
    path('artists/', views.all_artists, name='all_artists'),
    path('mixes/', views.all_mixes, name='all_mixes'),
    path('podcasts/', views.all_podcasts, name='all_podcasts'),
    path('mix/<int:mix_id>/', views.view_mix, name='view_mix'),
    path('moods/', views.moods_page, name='moods'),
    path('mood/<slug:mood_slug>/', views.mood_playlist, name='mood_playlist'),
    path('region/<str:country>/', views.region_page, name='region_page'),

    # --- User Features ---
    path('profile/', views.user_profile, name='user_profile'),
    path('history/', views.listening_history, name='listening_history'),
    path('stats/', views.listening_stats, name='listening_stats'),
    path('feed/', views.following_feed, name='following_feed'),
    path('followers/<str:username>/', views.followers_list, name='followers_list'),
    path('following/<str:username>/', views.following_list, name='following_list'),
    path('request-pro/', views.request_pro, name='request_pro'),

    # --- Follow System ---
    path('follow/<int:artist_id>/', views.follow_artist, name='follow_artist'),
    path('unfollow/<int:artist_id>/', views.unfollow_artist, name='unfollow_artist'),
    path('follow-status/<int:artist_id>/', views.get_follow_status, name='follow_status'),

    # --- Ads & Advertising ---
    path('ad/click/<int:ad_id>/', views.track_ad_click, name='track_ad_click'),
    path('advertise/', views.advertise_request, name='advertise'),
    path('advertise/request', views.advertise_request, name='advertiser_request'),

    # --- API Routes ---
    path('api/region-songs/', views.api_region_songs, name='api_region_songs'),
    path('api/recommendations/', views.get_ai_recommendations, name='ai_recommendations'),
    path('api/song-video/<int:song_id>/', views.get_song_video, name='song_video'),
    path('api/lyrics/<int:song_id>/', views.get_song_lyrics, name='song_lyrics'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('api/country-counts/', views.get_country_counts, name='country_counts'),

    # --- Tracking Routes ---
    path('track-interaction/<int:song_id>/', views.track_song_interaction, name='track_interaction'),
    path('track-history/<int:song_id>/', views.track_listening_history, name='track_history'),
    path('track-completion/<int:song_id>/', views.track_completion, name='track_completion'),
    path('play-podcast/<int:podcast_id>/', views.track_podcast_play, name='track_podcast_play'),

    # --- Static Pages ---
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
   
]

# Static and media files for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)