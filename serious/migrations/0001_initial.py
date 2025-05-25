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
            name='SeriousProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('about_me', models.TextField(blank=True, help_text='Tell others about yourself')),
                ('looking_for', models.TextField(blank=True, help_text="Describe what you're looking for in a partner")),
                ('relationship_goals', models.CharField(blank=True, choices=[('DATING', 'Dating'), ('RELATIONSHIP', 'Serious Relationship'), ('MARRIAGE', 'Marriage'), ('FAMILY', 'Starting a Family')], max_length=20)),
                ('relationship_type', models.CharField(blank=True, choices=[('MONOGAMOUS', 'Monogamous'), ('POLYAMOROUS', 'Polyamorous'), ('OPEN', 'Open Relationship')], max_length=20)),
                ('want_children', models.BooleanField(blank=True, help_text='Do you want children?', null=True)),
                ('have_children', models.BooleanField(blank=True, help_text='Do you have children?', null=True)),
                ('smoking', models.BooleanField(blank=True, help_text='Do you smoke?', null=True)),
                ('drinking', models.CharField(blank=True, choices=[('NEVER', 'Never'), ('RARELY', 'Rarely'), ('SOCIALLY', 'Socially'), ('REGULARLY', 'Regularly')], max_length=20)),
                ('education', models.CharField(blank=True, choices=[('HIGH_SCHOOL', 'High School'), ('ASSOCIATES', "Associate's Degree"), ('BACHELORS', "Bachelor's Degree"), ('MASTERS', "Master's Degree"), ('DOCTORATE', 'Doctorate or Higher'), ('OTHER', 'Other')], max_length=20)),
                ('occupation', models.CharField(blank=True, max_length=100)),
                ('deal_breakers', models.TextField(blank=True, help_text='What are your relationship deal breakers?')),
                ('is_identity_verified', models.BooleanField(default=False)),
                ('is_background_checked', models.BooleanField(default=False)),
                ('verified_date', models.DateField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='serious_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]