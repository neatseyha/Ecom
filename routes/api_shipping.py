"""
Shipping & Logistics API Routes
Endpoints for Shipping tracking and management
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

# Create Blueprint
shipping_bp = Blueprint('api_shipping', __name__, url_prefix='/api/shipping')

def get_db():
    """Get database session"""
    return current_app.extensions['sqlalchemy'].session

def get_models():
    """Get model classes from app context"""
    return {
        'Shipping': current_app.shipping_model_class,
        'Order': current_app.order_model_class,
    }

# ============ CREATE SHIPPING ============
@shipping_bp.route('/create', methods=['POST'])
def create_shipping():
    """Create shipping record for order"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        carrier = data.get('carrier')  # UPS, FedEx, DHL, etc.
        tracking_number = data.get('tracking_number')
        status = data.get('status', 'pending')  # pending, in_transit, delivered, cancelled
        shipped_date = data.get('shipped_date')
        estimated_delivery = data.get('estimated_delivery')

        if not all([order_id, carrier, tracking_number]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        models = get_models()
        Shipping = models['Shipping']
        Order = models['Order']
        db = get_db()

        # Verify order exists
        order = db.query(Order).get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        # Check if shipping already exists
        existing = db.query(Shipping).filter_by(order_id=order_id).first()
        if existing:
            return jsonify({'success': False, 'message': 'Shipping already exists for this order'}), 400

        shipping = Shipping(
            order_id=order_id,
            carrier=carrier,
            tracking_number=tracking_number,
            status=status,
            shipped_date=datetime.fromisoformat(shipped_date) if shipped_date else None,
            delivered_date=None,
            estimated_delivery=datetime.fromisoformat(estimated_delivery) if estimated_delivery else None,
            created_at=datetime.utcnow()
        )
        db.add(shipping)

        # Update order
        order.tracking_number = tracking_number
        order.shipping_method = carrier

        db.commit()

        return jsonify({
            'success': True,
            'message': 'Shipping record created',
            'shipping_id': shipping.id,
            'tracking_number': tracking_number
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ GET SHIPPING BY ORDER ============
@shipping_bp.route('/order/<int:order_id>', methods=['GET'])
def get_shipping_by_order(order_id):
    """Get shipping info for specific order"""
    try:
        models = get_models()
        Shipping = models['Shipping']
        db = get_db()

        shipping = db.query(Shipping).filter_by(order_id=order_id).first()
        if not shipping:
            return jsonify({'success': False, 'message': 'No shipping found for this order'}), 404

        return jsonify({
            'success': True,
            'shipping': {
                'id': shipping.id,
                'order_id': shipping.order_id,
                'carrier': shipping.carrier,
                'tracking_number': shipping.tracking_number,
                'status': shipping.status,
                'shipped_date': shipping.shipped_date.isoformat() if shipping.shipped_date else None,
                'delivered_date': shipping.delivered_date.isoformat() if shipping.delivered_date else None,
                'estimated_delivery': shipping.estimated_delivery.isoformat() if shipping.estimated_delivery else None,
                'created_at': shipping.created_at.isoformat()
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ TRACK SHIPMENT ============
@shipping_bp.route('/track/<tracking_number>', methods=['GET'])
def track_shipment(tracking_number):
    """Track shipment by tracking number"""
    try:
        models = get_models()
        Shipping = models['Shipping']
        Order = models['Order']
        db = get_db()

        shipping = db.query(Shipping).filter_by(tracking_number=tracking_number).first()
        if not shipping:
            return jsonify({'success': False, 'message': 'Shipment not found'}), 404

        order = db.query(Order).get(shipping.order_id)

        return jsonify({
            'success': True,
            'tracking': {
                'tracking_number': shipping.tracking_number,
                'carrier': shipping.carrier,
                'status': shipping.status,
                'shipped_date': shipping.shipped_date.isoformat() if shipping.shipped_date else None,
                'estimated_delivery': shipping.estimated_delivery.isoformat() if shipping.estimated_delivery else None,
                'delivered_date': shipping.delivered_date.isoformat() if shipping.delivered_date else None,
                'order_id': shipping.order_id,
                'customer_name': order.customer_name if order else 'Unknown'
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ UPDATE SHIPPING STATUS ============
@shipping_bp.route('/<int:shipping_id>/status', methods=['PUT'])
def update_shipping_status(shipping_id):
    """Update shipping status"""
    try:
        data = request.get_json()
        status = data.get('status')  # pending, in_transit, delivered, cancelled
        delivered_date = data.get('delivered_date')

        valid_statuses = ['pending', 'in_transit', 'delivered', 'cancelled']
        if status not in valid_statuses:
            return jsonify({'success': False, 'message': f'Invalid status. Must be one of: {valid_statuses}'}), 400

        models = get_models()
        Shipping = models['Shipping']
        Order = models['Order']
        db = get_db()

        shipping = db.query(Shipping).get(shipping_id)
        if not shipping:
            return jsonify({'success': False, 'message': 'Shipping not found'}), 404

        shipping.status = status
        if status == 'delivered' and delivered_date:
            shipping.delivered_date = datetime.fromisoformat(delivered_date)
        shipping.updated_at = datetime.utcnow()

        # Update order status
        order = db.query(Order).get(shipping.order_id)
        if order:
            if status == 'delivered':
                order.status = 'delivered'
            elif status == 'in_transit':
                order.status = 'shipped'

        db.commit()

        return jsonify({
            'success': True,
            'message': 'Shipping status updated',
            'status': status
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ GET USER SHIPMENTS ============
@shipping_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_shipments(user_id):
    """Get all shipments for a user"""
    try:
        models = get_models()
        Shipping = models['Shipping']
        Order = models['Order']
        db = get_db()

        # Get orders for user
        orders = db.query(Order).filter_by(user_id=user_id).all()
        order_ids = [order.id for order in orders]

        # Get shipments for those orders
        shipments = db.query(Shipping).filter(Shipping.order_id.in_(order_ids)).all()

        shipments_data = []
        for shipment in shipments:
            shipments_data.append({
                'id': shipment.id,
                'order_id': shipment.order_id,
                'carrier': shipment.carrier,
                'tracking_number': shipment.tracking_number,
                'status': shipment.status,
                'shipped_date': shipment.shipped_date.isoformat() if shipment.shipped_date else None,
                'estimated_delivery': shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None
            })

        return jsonify({
            'success': True,
            'shipments': shipments_data,
            'count': len(shipments_data)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
