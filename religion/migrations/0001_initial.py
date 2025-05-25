# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReligionProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('religion', models.CharField(choices=[('CH', 'Christianity'), ('IS', 'Islam'), ('HI', 'Hinduism'), ('BU', 'Buddhism'), ('JU', 'Judaism'), ('SI', 'Sikhism'), ('OT', 'Other'), ('NO', 'Non-religious/Spiritual')], max_length=2)),
                ('denomination', models.CharField(blank=True, max_length=2)),
                ('religiosity', models.IntegerField(choices=[(1, 'Not religious at all'), (2, 'Slightly religious'), (3, 'Moderately religious'), (4, 'Religious'), (5, 'Very religious')])),
                ('practice_frequency', models.IntegerField(choices=[(1, 'Never'), (2, 'Only on special occasions'), (3, 'Monthly'), (4, 'Weekly'), (5, 'Daily')], default=1)),
                ('religious_values', models.TextField(blank=True, help_text='Describe your religious beliefs and values')),
                ('religion_preference', models.CharField(blank=True, choices=[('CH', 'Christianity'), ('IS', 'Islam'), ('HI', 'Hinduism'), ('BU', 'Buddhism'), ('JU', 'Judaism'), ('SI', 'Sikhism'), ('OT', 'Other'), ('NO', 'Non-religious/Spiritual')], max_length=2)),
                ('denomination_preference', models.CharField(blank=True, max_length=2)),
                ('min_religiosity_preference', models.IntegerField(choices=[(1, 'Not religious at all'), (2, 'Slightly religious'), (3, 'Moderately religious'), (4, 'Religious'), (5, 'Very religious')], default=1)),
                ('max_religiosity_preference', models.IntegerField(choices=[(1, 'Not religious at all'), (2, 'Slightly religious'), (3, 'Moderately religious'), (4, 'Religious'), (5, 'Very religious')], default=5)),
                ('interfaith_willingness', models.BooleanField(default=True, help_text='Are you open to dating someone of a different faith?')),
                ('available_for_worship', models.BooleanField(default=False, help_text='Available to attend worship services together')),
                ('available_for_prayer', models.BooleanField(default=False, help_text='Available for prayer or meditation together')),
                ('available_for_religious_study', models.BooleanField(default=False, help_text='Available for religious study together')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='religion_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ] 