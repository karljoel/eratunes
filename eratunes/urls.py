"""
URL configuration for eratunes project.
"""

import os
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# ========== SITEMAP IMPORTS ==========
from django.contrib.sitemaps.views import sitemap
from music.sitemaps import SongSitemap, ArtistSitemap

sitemaps = {
    'songs': SongSitemap,
    'artists': ArtistSitemap,
}

urlpatterns = [
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Music app
    path('', include('music.urls')),
    
    # Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # path('flutterwave/', include('flutterwavedjango.urls')),  # Commented out
]

# Static and media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()