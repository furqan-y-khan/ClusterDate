#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "super_dating_app.settings")
django.setup()

# After setting up Django, import the required models
from payments.models import Plan

def create_sample_plans():
    plans_data = [
        {
            'name': 'Basic',
            'description': 'Essential features to start your dating journey',
            'price': Decimal('9.99'),
            'interval': 'month',
            'features': {
                'Unlimited Likes': True,
                'See Who Likes You': False,
                'Priority Matching': False,
                'Unlimited Messaging': True,
                'No Ads': False,
                'Video Calls': False,
                'Advanced Filters': False,
                'Incognito Mode': False,
            }
        },
        {
            'name': 'Premium',
            'description': 'Enhanced features for serious daters',
            'price': Decimal('19.99'),
            'interval': 'month',
            'features': {
                'Unlimited Likes': True,
                'See Who Likes You': True,
                'Priority Matching': True,
                'Unlimited Messaging': True,
                'No Ads': True,
                'Video Calls': False,
                'Advanced Filters': True,
                'Incognito Mode': False,
            }
        },
        {
            'name': 'VIP',
            'description': 'Ultimate dating experience with all premium features',
            'price': Decimal('29.99'),
            'interval': 'month',
            'features': {
                'Unlimited Likes': True,
                'See Who Likes You': True,
                'Priority Matching': True,
                'Unlimited Messaging': True,
                'No Ads': True,
                'Video Calls': True,
                'Advanced Filters': True,
                'Incognito Mode': True,
            }
        },
        {
            'name': 'Premium Yearly',
            'description': 'Save 20% with our annual Premium plan',
            'price': Decimal('191.88'),  # 19.99 * 12 * 0.8 (20% discount)
            'interval': 'year',
            'features': {
                'Unlimited Likes': True,
                'See Who Likes You': True,
                'Priority Matching': True,
                'Unlimited Messaging': True,
                'No Ads': True,
                'Video Calls': False,
                'Advanced Filters': True,
                'Incognito Mode': False,
            }
        },
        {
            'name': 'VIP Yearly',
            'description': 'Save 25% with our annual VIP plan',
            'price': Decimal('269.88'),  # 29.99 * 12 * 0.75 (25% discount)
            'interval': 'year',
            'features': {
                'Unlimited Likes': True,
                'See Who Likes You': True,
                'Priority Matching': True,
                'Unlimited Messaging': True,
                'No Ads': True,
                'Video Calls': True,
                'Advanced Filters': True,
                'Incognito Mode': True,
            }
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    for plan_data in plans_data:
        # Check if plan already exists
        try:
            plan = Plan.objects.get(name=plan_data['name'])
            # Update existing plan
            plan.description = plan_data['description']
            plan.price = plan_data['price']
            plan.interval = plan_data['interval']
            plan.features = plan_data['features']
            plan.is_active = True
            plan.save()
            updated_count += 1
            print(f"Updated plan: {plan.name}")
        except Plan.DoesNotExist:
            # Create new plan
            plan = Plan.objects.create(
                name=plan_data['name'],
                description=plan_data['description'],
                price=plan_data['price'],
                interval=plan_data['interval'],
                features=plan_data['features'],
                is_active=True
            )
            created_count += 1
            print(f"Created plan: {plan.name}")
    
    return created_count, updated_count

if __name__ == "__main__":
    print("Creating sample subscription plans...")
    created, updated = create_sample_plans()
    print(f"Done! Created {created} new plans and updated {updated} existing plans.") 