from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from geopy.distance import geodesic
import json
from datetime import datetime, timedelta
from database import db, User, TechnicianProfile, Service, Booking, Review
from config import Config
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Load environment variables
load_dotenv()

# Initialize database and login manager
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    # Add some default services if none exist
    if Service.query.count() == 0:
        services = [
            Service(name='Plumbing', description='Fix leaks, install fixtures, clear drains'),
            Service(name='Electrical', description='Wiring, lighting, electrical repairs'),
            Service(name='HVAC', description='Heating, ventilation, air conditioning'),
            Service(name='Carpentry', description='Furniture, cabinets, structural work'),
            Service(name='Painting', description='Interior and exterior painting'),
            Service(name='Cleaning', description='Residential and commercial cleaning'),
            Service(name='Appliance Repair', description='Fix household appliances'),
            Service(name='General Handyman', description='Various home repairs'),
        ]
        for service in services:
            db.session.add(service)
        db.session.commit()

# Authentication Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'customer':
            return redirect(url_for('customer_dashboard'))
        else:
            return redirect(url_for('technician_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            login_user(user, remember=data.get('remember', False))
            return jsonify({'success': True, 'role': user.role})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            role=data['role'],
            phone=data.get('phone', ''),
            address=data.get('address', '')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # If registering as technician, create technician profile
        if data['role'] == 'technician':
            tech_profile = TechnicianProfile(
                user_id=user.id,
                service_type=data.get('service_type', 'General'),
                hourly_rate=data.get('hourly_rate', 25.0),
                description=data.get('description', ''),
                skills=data.get('skills', '')
            )
            db.session.add(tech_profile)
            db.session.commit()
        
        login_user(user)
        return jsonify({'success': True, 'role': user.role})
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Customer Routes
@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        return redirect(url_for('technician_dashboard'))
    
    # Get user's bookings
    bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.created_at.desc()).limit(5).all()
    return render_template('customer_dashboard.html', bookings=bookings)

@app.route('/find-technicians', methods=['GET', 'POST'])
@login_required
def find_technicians():
    if current_user.role != 'customer':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.get_json()
        user_lat = data.get('latitude')
        user_lon = data.get('longitude')
        service_type = data.get('service_type', '')
        max_distance = data.get('max_distance', 50)  # km
        
        # Get all available technicians
        technicians = TechnicianProfile.query.filter_by(is_available=True).all()
        
        results = []
        for tech in technicians:
            if service_type and service_type.lower() not in tech.service_type.lower():
                continue
            
            tech_user = User.query.get(tech.user_id)
            if not tech_user.latitude or not tech_user.longitude:
                continue
            
            # Calculate distance
            try:
                distance = geodesic((user_lat, user_lon), 
                                  (tech_user.latitude, tech_user.longitude)).kilometers
            except:
                continue
            
            if distance <= max_distance:
                results.append({
                    'id': tech.id,
                    'user_id': tech.user_id,
                    'name': tech_user.username,
                    'service_type': tech.service_type,
                    'experience_years': tech.experience_years,
                    'hourly_rate': tech.hourly_rate,
                    'rating': tech.rating or 0.0,
                    'total_reviews': tech.total_reviews or 0,
                    'description': tech.description,
                    'distance': round(distance, 2),
                    'skills': tech.skills.split(',') if tech.skills else []
                })
        
        # Sort by distance
        results.sort(key=lambda x: x['distance'])
        return jsonify({'technicians': results})
    
    return render_template('find_technicians.html')

@app.route('/book-technician', methods=['POST'])
@login_required
def book_technician():
    if current_user.role != 'customer':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    technician = User.query.get(data['technician_id'])
    
    if not technician or technician.role != 'technician':
        return jsonify({'error': 'Technician not found'}), 404
    
    # Parse date string
    scheduled_date = None
    if 'scheduled_date' in data:
        try:
            scheduled_date = datetime.fromisoformat(data['scheduled_date'].replace('Z', '+00:00'))
        except:
            scheduled_date = datetime.fromisoformat(data['scheduled_date'])
    
    booking = Booking(
        customer_id=current_user.id,
        technician_id=technician.id,
        service_type=data['service_type'],
        description=data['description'],
        address=data.get('address', current_user.address),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        scheduled_date=scheduled_date,
        estimated_hours=float(data['estimated_hours'])
    )
    
    # Calculate cost based on technician's rate
    tech_profile = TechnicianProfile.query.filter_by(user_id=technician.id).first()
    booking.total_cost = tech_profile.hourly_rate * booking.estimated_hours
    
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'booking_id': booking.id,
        'message': 'Booking request sent successfully'
    })

@app.route('/customer/bookings')
@login_required
def customer_bookings():
    bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('bookings.html', bookings=bookings, user_role='customer')

# Technician Routes
@app.route('/technician/dashboard')
@login_required
def technician_dashboard():
    if current_user.role != 'technician':
        return redirect(url_for('customer_dashboard'))
    
    # Get technician's bookings
    bookings = Booking.query.filter_by(technician_id=current_user.id).order_by(Booking.created_at.desc()).limit(5).all()
    
    # Get technician profile
    profile = TechnicianProfile.query.filter_by(user_id=current_user.id).first()
    
    # Calculate stats
    total_completed = Booking.query.filter_by(technician_id=current_user.id, status='completed').count()
    total_earnings = db.session.query(db.func.sum(Booking.total_cost)).filter(
        Booking.technician_id == current_user.id,
        Booking.status == 'completed'
    ).scalar() or 0
    
    return render_template('technician_dashboard.html', 
                          bookings=bookings, 
                          profile=profile,
                          total_completed=total_completed,
                          total_earnings=total_earnings)

@app.route('/technician/bookings')
@login_required
def technician_bookings():
    bookings = Booking.query.filter_by(technician_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('bookings.html', bookings=bookings, user_role='technician')

@app.route('/update-booking-status', methods=['POST'])
@login_required
def update_booking_status():
    data = request.get_json()
    booking = Booking.query.get(data['booking_id'])
    
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    if booking.technician_id != current_user.id and booking.customer_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    booking.status = data['status']
    
    if data['status'] == 'completed':
        booking.completed_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/update-location', methods=['POST'])
@login_required
def update_location():
    data = request.get_json()
    current_user.latitude = data.get('latitude')
    current_user.longitude = data.get('longitude')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/update-availability', methods=['POST'])
@login_required
def update_availability():
    if current_user.role != 'technician':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    profile = TechnicianProfile.query.filter_by(user_id=current_user.id).first()
    if profile:
        profile.is_available = data['is_available']
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/submit-review', methods=['POST'])
@login_required
def submit_review():
    data = request.get_json()
    booking = Booking.query.get(data['booking_id'])
    
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    if booking.customer_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if booking.status != 'completed':
        return jsonify({'error': 'Can only review completed bookings'}), 400
    
    # Update booking with review
    booking.rating = float(data['rating'])
    booking.review = data.get('review', '')
    
    # Update technician's average rating
    tech_bookings = Booking.query.filter_by(
        technician_id=booking.technician_id,
        status='completed'
    ).all()
    
    completed_with_rating = [b for b in tech_bookings if b.rating]
    if completed_with_rating:
        avg_rating = sum(b.rating for b in completed_with_rating) / len(completed_with_rating)
        tech_profile = TechnicianProfile.query.filter_by(user_id=booking.technician_id).first()
        if tech_profile:
            tech_profile.rating = round(avg_rating, 1)
            tech_profile.total_reviews = len(completed_with_rating)
    
    db.session.commit()
    return jsonify({'success': True})

# API Routes
@app.route('/api/user-info')
@login_required
def get_user_info():
    profile = None
    if current_user.role == 'technician':
        profile = TechnicianProfile.query.filter_by(user_id=current_user.id).first()
    
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'profile': {
            'service_type': profile.service_type if profile else None,
            'hourly_rate': profile.hourly_rate if profile else None,
            'rating': profile.rating if profile else None
        }
    })

@app.route('/api/services')
def get_services():
    services = Service.query.all()
    service_list = list(set([s.name for s in services]))
    return jsonify({'services': service_list})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Don't run in debug mode on production
    app.run(host='0.0.0.0', port=port)