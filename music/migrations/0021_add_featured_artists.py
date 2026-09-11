from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0020_usersongpurchase_downloads_remaining_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='featured_artists',
            field=models.ManyToManyField(
                blank=True,
                help_text='Select featured artists for this collaboration',
                related_name='featured_in_songs',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]