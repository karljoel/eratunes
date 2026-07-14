from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Song, CustomUser

class SongSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Song.objects.filter(is_approved=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse('song_detail', args=[str(obj.id)])


class ArtistSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return CustomUser.objects.filter(is_artist=True)

    def lastmod(self, obj):
        return obj.last_active

    def location(self, obj):
        return reverse('artist_profile', args=[str(obj.username)])