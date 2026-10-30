import boto3
from django.core.management.base import BaseCommand
from django.conf import settings
from music.models import Song, CustomUser
import urllib.parse

class Command(BaseCommand):
    help = 'Rebuild database from Cloudflare R2 MP3 files'

    def handle(self, *args, **kwargs):
        s3 = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.stdout.write(f"Scanning bucket: {bucket_name}...")

        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix='songs/')

        count = 0
        skipped = 0
        
        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                key = obj['Key']
                
                if key.endswith('/') or not key.endswith('.mp3'):
                    continue
                
                filename = key.split('/')[-1]
                clean_name = filename.replace('.mp3', '').replace('_', ' ')
                clean_name = clean_name.replace('eratunez.com', '').strip()
                
                if ' - ' in clean_name:
                    artist_name, title = clean_name.split(' - ', 1)
                else:
                    artist_name = "Unknown Artist"
                    title = clean_name
                
                # THE FIX: Truncate strings to fit the database limits
                # Title max is 200, Artist username max is 150
                title = title.strip()[:195]
                artist_name = artist_name.strip()[:145]
                
                if not title or not artist_name:
                    skipped += 1
                    continue

                safe_username = artist_name.replace(' ', '_').lower()
                fake_email = f"{safe_username}@eratunez-recovery.com"
                
                artist_obj, _ = CustomUser.objects.get_or_create(
                    username=artist_name,
                    defaults={
                        'email': fake_email[:254], # Email max is 254
                        'is_artist': True,
                        'user_type': 'artist'
                    }
                )
                
                audio_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{urllib.parse.quote(key)}"

                song, created = Song.objects.get_or_create(
                    title=title,
                    artist=artist_obj, 
                    defaults={
                        'audio_file': audio_url,
                        'cover_image': 'https://pub-bee61826af38438db4045c84ae0bc301.r2.dev/covers/11716.jpg',
                        'is_approved': True,
                    }
                )
                
                if created:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully rebuilt {count} songs! Skipped: {skipped}"))
