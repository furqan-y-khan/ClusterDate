# Super Dating App

A comprehensive dating platform that caters to various types of relationships and preferences.

## Features

- **Multiple Dating Categories**: Mainstream, Casual, Sugar Dating, LGBTQ+, Religion-Based, Cultural/Ethnic, Serious Relationships, and Niche Dating
- **User Authentication**: Secure login and registration with Firebase Authentication
- **User Profiles**: Detailed user profiles with photos, interests, and preferences
- **Location-Based Matching**: Find users near you using Google Maps integration
- **Real-Time Messaging**: Chat with your matches in real-time
- **Video & Audio Calling**: Connect with matches through WebRTC-powered video and audio calls
- **Push Notifications**: Stay updated with Firebase Cloud Messaging notifications
- **Match System**: Like profiles and get matched when the interest is mutual
- **Privacy Controls**: Block users and report inappropriate behavior

## Technology Stack

- **Backend**: Django, Django Channels, Django REST Framework
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Firebase Authentication
- **Real-Time Communication**: WebSockets, WebRTC
- **Maps & Location**: Google Maps API
- **Push Notifications**: Firebase Cloud Messaging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/super-dating-app.git
cd super-dating-app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file with the following variables
SECRET_KEY=your_secret_key
DEBUG=True
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id
FIREBASE_APP_ID=your_firebase_app_id
FIREBASE_MEASUREMENT_ID=your_firebase_measurement_id
WEBPUSH_VAPID_PUBLIC_KEY=your_webpush_vapid_public_key
WEBPUSH_VAPID_PRIVATE_KEY=your_webpush_vapid_private_key
WEBPUSH_VAPID_ADMIN_EMAIL=your_webpush_vapid_admin_email
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Usage

1. Access the admin panel at `http://localhost:8000/admin/` to manage users, profiles, and other data.
2. Register a new account or log in with an existing one.
3. Complete your profile with photos, interests, and preferences.
4. Start discovering matches based on your preferences.
5. Like profiles and chat with your matches.
6. Enjoy video and audio calls with your matches.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Django](https://www.djangoproject.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Firebase](https://firebase.google.com/)
- [Google Maps](https://developers.google.com/maps)
- [WebRTC](https://webrtc.org/) 