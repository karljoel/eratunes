from django.contrib.sitemaps import Sitemap
from .models import Song, CustomUser

class SongSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Song.objects.filter(is_approved=True)

    def lastmod(self, obj):
        return obj.created_at


class ArtistSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return CustomUser.objects.filter(is_artist=True)

    def lastmod(self, obj):
        return obj.last_active