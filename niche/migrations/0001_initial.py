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
            name='Community',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(blank=True, max_length=120, unique=True)),
                ('description', models.TextField()),
                ('icon_class', models.CharField(default='fas fa-users', help_text='FontAwesome icon class', max_length=50)),
                ('cover_image', models.ImageField(blank=True, null=True, upload_to='community_covers/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_approved', models.BooleanField(default=True)),
                ('member_count', models.PositiveIntegerField(default=0)),
                ('suggested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='suggested_communities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Communities',
            },
        ),
        migrations.CreateModel(
            name='NicheProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primary_interest', models.CharField(blank=True, help_text='Your main interest or passion', max_length=100)),
                ('experience_level', models.CharField(blank=True, choices=[('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('ADVANCED', 'Advanced'), ('EXPERT', 'Expert')], max_length=15)),
                ('interest_description', models.TextField(blank=True, help_text='Describe your interest in more detail')),
                ('seeking_experience_levels', models.CharField(blank=True, help_text="Experience levels you're interested in (comma-separated)", max_length=255)),
                ('interest_based_preferences', models.TextField(blank=True, help_text='What are you looking for in a match based on interests?')),
                ('social_media_links', models.JSONField(blank=True, default=dict, help_text='Links to your social profiles related to your interests', null=True)),
                ('show_experience_level', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('communities', models.ManyToManyField(blank=True, related_name='profiles', to='niche.community')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='niche_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]