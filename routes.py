from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Service, Appointment
from datetime import datetime
from utils import notify_appointment

api = Blueprint('api', __name__)

@api.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Welcome to the Beauty Salon API! Access the endpoints at /api. See documentation for details.',
        'endpoints': {
            'register': '/api/register',
            'login': '/api/login',
            'services': '/api/services',
            'appointments': '/api/appointments',
            'admin_users': '/api/admin/users'
        }
    }), 200

# Registro e Login
@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 400
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token, 'is_admin': user.is_admin}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# CRUD Serviços
@api.route('/services', methods=['POST'])
@jwt_required()
def create_service():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403
    data = request.get_json()
    service = Service(name=data['name'], duration=data['duration'], price=data['price'])
    db.session.add(service)
    db.session.commit()
    return jsonify({'message': 'Service created', 'id': service.id}), 201

@api.route('/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([{'id': s.id, 'name': s.name, 'duration': s.duration, 'price': s.price} for s in services]), 200

@api.route('/services/<int:id>', methods=['PUT'])
@jwt_required()
def update_service(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403
    service = Service.query.get_or_404(id)
    data = request.get_json()
    service.name = data.get('name', service.name)
    service.duration = data.get('duration', service.duration)
    service.price = data.get('price', service.price)
    db.session.commit()
    return jsonify({'message': 'Service updated'}), 200

@api.route('/services/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_service(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Service deleted'}), 200

# CRUD Agendamentos
@api.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    user_id = get_jwt_identity()
    data = request.get_json()
    date_time = datetime.strptime(data['date_time'], '%Y-%m-%d %H:%M')
    
    # Verificar conflito de horário
    conflict = Appointment.query.filter_by(date_time=date_time).first()
    if conflict:
        return jsonify({'message': 'Time slot unavailable'}), 400
    
    appointment = Appointment(user_id=user_id, service_id=data['service_id'], date_time=date_time)
    db.session.add(appointment)
    db.session.commit()
    
    user = User.query.get(user_id)
    notify_appointment(user, appointment, 'confirmed')
    return jsonify({'message': 'Appointment created', 'id': appointment.id}), 201

@api.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    appointments = Appointment.query.filter_by(user_id=user_id).all() if not user.is_admin else Appointment.query.all()
    return jsonify([{
        'id': a.id,
        'user': a.user.username,
        'service': a.service.name,
        'date_time': a.date_time.strftime('%Y-%m-%d %H:%M'),
        'status': a.status
    } for a in appointments]), 200

@api.route('/appointments/<int:id>', methods=['PUT'])
@jwt_required()
def reschedule_appointment(id):
    user_id = get_jwt_identity()
    appointment = Appointment.query.get_or_404(id)
    if appointment.user_id != user_id and not User.query.get(user_id).is_admin:
        return jsonify({'message': 'Unauthorized'}), 403
    data = request.get_json()
    new_date_time = datetime.strptime(data['date_time'], '%Y-%m-%d %H:%M')
    
    # Verificar conflito
    conflict = Appointment.query.filter(Appointment.id != id, Appointment.date_time == new_date_time).first()
    if conflict:
        return jsonify({'message': 'Time slot unavailable'}), 400
    
    appointment.date_time = new_date_time
    appointment.status = 'rescheduled'
    db.session.commit()
    
    notify_appointment(appointment.user, appointment, 'rescheduled')
    return jsonify({'message': 'Appointment rescheduled'}), 200

@api.route('/appointments/<int:id>', methods=['DELETE'])
@jwt_required()
def cancel_appointment(id):
    user_id = get_jwt_identity()
    appointment = Appointment.query.get_or_404(id)
    if appointment.user_id != user_id and not User.query.get(user_id).is_admin:
        return jsonify({'message': 'Unauthorized'}), 403
    appointment.status = 'cancelled'
    db.session.commit()
    
    notify_appointment(appointment.user, appointment, 'cancelled')
    return jsonify({'message': 'Appointment cancelled'}), 200

# Painel Admin
@api.route('/admin/users', methods=['GET'])
@jwt_required()
def admin_users():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user.is_admin:
        return jsonify({'message': 'Admin access required'}), 403
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'email': u.email, 'is_admin': u.is_admin} for u in users]), 200