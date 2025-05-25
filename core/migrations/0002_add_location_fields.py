from django.db import migrations, models
from django.utils import timezone

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='last_location_update',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='receive_message_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='receive_match_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='receive_like_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='fcm_token',
            field=models.TextField(blank=True, null=True),
        ),
    ] 