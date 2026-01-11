"""
OrderService - E-Commerce Microservice
=======================================
This microservice handles order management as a Dapr pub/sub subscriber.
It receives order events from CartService and publishes payment events.

Endpoints:
- GET  /health           - Health check endpoint
- GET  /orders           - List all orders
- GET  /orders/<id>      - Get order by ID
- GET  /orders/user/<id> - Get orders by user
- PUT  /orders/<id>/status - Update order status

Dapr Integration:
- Subscribes to 'order-events' topic (receives from CartService)
- Publishes to 'payment-events' topic (triggers PaymentService)
- Publishes to 'product-events' topic (stock updates)
"""

import os
import json
import logging
import uuid
from datetime import datetime
from flask import Flask, jsonify, request
import requests

# ============================================================================
# Configuration
# ============================================================================

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('OrderService')

# Dapr configuration
DAPR_HTTP_PORT = os.getenv('DAPR_HTTP_PORT', '3500')
DAPR_PUBSUB_NAME = os.getenv('DAPR_PUBSUB_NAME', 'pubsub')
PAYMENT_TOPIC = 'payment-events'
PRODUCT_TOPIC = 'product-events'

# Service port
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5003'))

# ============================================================================
# In-Memory Order Store (In production, use DynamoDB or RDS)
# ============================================================================

orders_db = {
    "order-sample001": {
        "order_id": "order-sample001",
        "user_id": "user-001",
        "items": [
            {
                "item_id": "cart-item-001",
                "product_id": "prod-001",
                "product_name": "Wireless Bluetooth Headphones",
                "quantity": 1,
                "unit_price": 149.99
            }
        ],
        "subtotal": 149.99,
        "tax": 12.00,
        "shipping": 5.99,
        "total": 167.98,
        "status": "completed",
        "payment_status": "paid",
        "shipping_address": {
            "street": "123 Main St",
            "city": "Seattle",
            "state": "WA",
            "zip": "98101",
            "country": "USA"
        },
        "created_at": "2026-01-10T14:30:00Z",
        "updated_at": "2026-01-10T15:00:00Z"
    }
}

# Order status flow
ORDER_STATUS_FLOW = [
    'pending',
    'confirmed',
    'payment_processing',
    'paid',
    'processing',
    'shipped',
    'delivered',
    'completed',
    'cancelled',
    'refunded'
]

# ============================================================================
# Dapr Pub/Sub Helper Functions
# ============================================================================

def publish_event(topic: str, event_type: str, data: dict) -> bool:
    """
    Publish an event to Dapr pub/sub component (AWS SNS/SQS).
    """
    dapr_url = f"http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/{DAPR_PUBSUB_NAME}/{topic}"
    
    event = {
        "id": str(uuid.uuid4()),
        "source": "order-service",
        "type": event_type,
        "specversion": "1.0",
        "datacontenttype": "application/json",
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        logger.info(f"Publishing event to topic '{topic}': {event_type}")
        
        response = requests.post(
            dapr_url,
            json=event,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code in [200, 204]:
            logger.info(f"✅ Event published successfully: {event_type} (ID: {event['id']})")
            return True
        else:
            logger.error(f"❌ Failed to publish event: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error publishing event: {str(e)}")
        return False

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes probes."""
    return jsonify({
        "status": "healthy",
        "service": "order-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dapr_enabled": True,
        "subscriptions": ["order-events", "payment-events"]
    }), 200

# ============================================================================
# Order Endpoints
# ============================================================================

@app.route('/orders', methods=['GET'])
def list_orders():
    """
    List all orders with optional status filtering.
    
    Query Parameters:
        status (optional): Filter by order status
    """
    status = request.args.get('status')
    
    if status:
        filtered = {k: v for k, v in orders_db.items() if v['status'] == status}
        logger.info(f"Listed {len(filtered)} orders with status: {status}")
        return jsonify({"orders": list(filtered.values()), "count": len(filtered)}), 200
    
    logger.info(f"Listed all {len(orders_db)} orders")
    return jsonify({"orders": list(orders_db.values()), "count": len(orders_db)}), 200


@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """
    Get order details by ID.
    """
    if order_id not in orders_db:
        logger.warning(f"Order not found: {order_id}")
        return jsonify({"error": "Order not found", "order_id": order_id}), 404
    
    logger.info(f"Retrieved order: {order_id}")
    return jsonify(orders_db[order_id]), 200


@app.route('/orders/user/<user_id>', methods=['GET'])
def get_user_orders(user_id):
    """
    Get all orders for a specific user.
    """
    user_orders = [o for o in orders_db.values() if o['user_id'] == user_id]
    logger.info(f"Retrieved {len(user_orders)} orders for user: {user_id}")
    return jsonify({"orders": user_orders, "count": len(user_orders)}), 200


@app.route('/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """
    Update order status manually (admin endpoint).
    """
    if order_id not in orders_db:
        return jsonify({"error": "Order not found"}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ORDER_STATUS_FLOW:
        return jsonify({
            "error": "Invalid status",
            "valid_statuses": ORDER_STATUS_FLOW
        }), 400
    
    order = orders_db[order_id]
    old_status = order['status']
    order['status'] = new_status
    order['updated_at'] = datetime.utcnow().isoformat() + "Z"
    
    # Publish status change event
    publish_event('order-events', 'order.status_changed', {
        "order_id": order_id,
        "old_status": old_status,
        "new_status": new_status,
        "action": "status_changed"
    })
    
    logger.info(f"✅ Order {order_id} status: {old_status} → {new_status}")
    return jsonify(order), 200


@app.route('/orders', methods=['POST'])
def create_order():
    """
    Create order directly (alternative to pub/sub).
    """
    data = request.get_json()
    
    required_fields = ['user_id', 'items']
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": "Missing fields", "missing": missing}), 400
    
    order_id = f"order-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Calculate totals
    subtotal = sum(item.get('unit_price', 0) * item.get('quantity', 1) for item in data['items'])
    tax = round(subtotal * 0.08, 2)
    shipping = 5.99
    total = round(subtotal + tax + shipping, 2)
    
    order = {
        "order_id": order_id,
        "user_id": data['user_id'],
        "items": data['items'],
        "subtotal": subtotal,
        "tax": tax,
        "shipping": shipping,
        "total": total,
        "status": "pending",
        "payment_status": "pending",
        "shipping_address": data.get('shipping_address', {}),
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    orders_db[order_id] = order
    
    # Trigger payment processing
    publish_event(PAYMENT_TOPIC, 'payment.requested', {
        "order_id": order_id,
        "user_id": data['user_id'],
        "amount": total,
        "action": "payment_requested"
    })
    
    logger.info(f"✅ Created order: {order_id} for user: {data['user_id']}")
    return jsonify(order), 201

# ============================================================================
# Dapr Subscription Endpoints
# ============================================================================

@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    """
    Dapr subscription configuration.
    OrderService subscribes to order-events and payment-events topics.
    """
    subscriptions = [
        {
            "pubsubname": DAPR_PUBSUB_NAME,
            "topic": "order-events",
            "route": "/events/order"
        },
        {
            "pubsubname": DAPR_PUBSUB_NAME,
            "topic": "payment-events",
            "route": "/events/payment"
        }
    ]
    return jsonify(subscriptions), 200


@app.route('/events/order', methods=['POST'])
def handle_order_event():
    """
    Handle incoming order events from CartService.
    
    Event Types:
    - order.created: New order from checkout
    """
    event = request.get_json()
    event_type = event.get('type', 'unknown')
    event_data = event.get('data', {})
    
    logger.info(f"📥 Received order event: {event_type}")
    logger.info(f"   Event ID: {event.get('id', 'N/A')}")
    logger.info(f"   Source: {event.get('source', 'N/A')}")
    
    if event_type == 'order.created':
        # Process new order from cart checkout
        order_data = event_data.get('order', {})
        
        if not order_data:
            logger.error("Order data missing in event")
            return jsonify({"status": "error", "message": "Order data missing"}), 400
        
        order_id = order_data.get('order_id', f"order-{uuid.uuid4().hex[:8]}")
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Enrich order with additional fields
        order = {
            **order_data,
            "order_id": order_id,
            "status": "confirmed",
            "payment_status": "pending",
            "shipping": 5.99,
            "total": round(order_data.get('total', 0) + 5.99, 2),
            "updated_at": timestamp
        }
        
        # Store order
        orders_db[order_id] = order
        
        logger.info(f"✅ Order received and confirmed: {order_id}")
        logger.info(f"   User: {order.get('user_id')}")
        logger.info(f"   Items: {len(order.get('items', []))}")
        logger.info(f"   Total: ${order.get('total', 0):.2f}")
        
        # Trigger payment processing
        publish_event(PAYMENT_TOPIC, 'payment.requested', {
            "order_id": order_id,
            "user_id": order.get('user_id'),
            "amount": order.get('total', 0),
            "action": "payment_requested"
        })
        
        # Trigger stock reduction in ProductService
        publish_event(PRODUCT_TOPIC, 'order.placed', {
            "order_id": order_id,
            "items": order.get('items', []),
            "action": "stock_reduction_needed"
        })
        
        # Publish order confirmed event
        publish_event('order-events', 'order.confirmed', {
            "order_id": order_id,
            "status": "confirmed",
            "action": "order_confirmed"
        })
    
    return jsonify({"status": "processed", "event_type": event_type}), 200


@app.route('/events/payment', methods=['POST'])
def handle_payment_event():
    """
    Handle payment events from PaymentService.
    
    Event Types:
    - payment.completed: Payment successful
    - payment.failed: Payment failed
    """
    event = request.get_json()
    event_type = event.get('type', 'unknown')
    event_data = event.get('data', {})
    
    logger.info(f"📥 Received payment event: {event_type}")
    
    order_id = event_data.get('order_id')
    
    if not order_id or order_id not in orders_db:
        logger.warning(f"Order not found for payment event: {order_id}")
        return jsonify({"status": "error", "message": "Order not found"}), 404
    
    order = orders_db[order_id]
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    if event_type == 'payment.completed':
        order['payment_status'] = 'paid'
        order['status'] = 'paid'
        order['payment_id'] = event_data.get('payment_id')
        order['updated_at'] = timestamp
        
        logger.info(f"✅ Payment completed for order: {order_id}")
        
        # Publish order paid event
        publish_event('order-events', 'order.paid', {
            "order_id": order_id,
            "payment_id": event_data.get('payment_id'),
            "status": "paid",
            "action": "order_paid"
        })
        
    elif event_type == 'payment.failed':
        order['payment_status'] = 'failed'
        order['status'] = 'payment_failed'
        order['payment_error'] = event_data.get('error', 'Unknown error')
        order['updated_at'] = timestamp
        
        logger.error(f"❌ Payment failed for order: {order_id}")
    
    return jsonify({"status": "processed", "event_type": event_type}), 200

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("📦 Starting OrderService")
    logger.info(f"   Port: {SERVICE_PORT}")
    logger.info(f"   Dapr HTTP Port: {DAPR_HTTP_PORT}")
    logger.info(f"   Pub/Sub Component: {DAPR_PUBSUB_NAME}")
    logger.info(f"   Subscribing to: order-events, payment-events")
    logger.info(f"   Publishing to: payment-events, product-events")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)
