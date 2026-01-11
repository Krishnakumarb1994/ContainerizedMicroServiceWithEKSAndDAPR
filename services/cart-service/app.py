"""
CartService - E-Commerce Microservice
======================================
This microservice handles shopping cart management and publishes cart events
using Dapr pub/sub messaging to AWS SNS/SQS.

Endpoints:
- GET  /health              - Health check endpoint
- GET  /carts/<user_id>     - Get user's cart
- POST /carts/<user_id>/items - Add item to cart (publishes event)
- PUT  /carts/<user_id>/items/<item_id> - Update cart item
- DELETE /carts/<user_id>/items/<item_id> - Remove item from cart
- DELETE /carts/<user_id>   - Clear cart
- POST /carts/<user_id>/checkout - Checkout cart (publishes order event)

Dapr Integration:
- Publishes to 'cart-events' topic
- Publishes to 'order-events' topic on checkout
- Subscribes to 'product-events' for price updates
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

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CartService')

# Dapr configuration
DAPR_HTTP_PORT = os.getenv('DAPR_HTTP_PORT', '3500')
DAPR_PUBSUB_NAME = os.getenv('DAPR_PUBSUB_NAME', 'pubsub')
CART_TOPIC = 'cart-events'
ORDER_TOPIC = 'order-events'

# Service port
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5002'))

# Product service URL for fetching product details
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:5001')

# ============================================================================
# In-Memory Cart Store (In production, use DynamoDB or ElastiCache Redis)
# ============================================================================

carts_db = {
    "user-001": {
        "user_id": "user-001",
        "items": [
            {
                "item_id": "cart-item-001",
                "product_id": "prod-001",
                "product_name": "Wireless Bluetooth Headphones",
                "quantity": 2,
                "unit_price": 149.99,
                "added_at": "2026-01-11T09:00:00Z"
            }
        ],
        "created_at": "2026-01-11T08:00:00Z",
        "updated_at": "2026-01-11T09:00:00Z"
    }
}

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
        "source": "cart-service",
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


def invoke_service(app_id: str, method: str, data: dict = None) -> dict:
    """
    Invoke another service using Dapr service invocation.
    """
    dapr_url = f"http://localhost:{DAPR_HTTP_PORT}/v1.0/invoke/{app_id}/method/{method}"
    
    try:
        if data:
            response = requests.post(dapr_url, json=data, timeout=5)
        else:
            response = requests.get(dapr_url, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Service invocation failed: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error invoking service: {str(e)}")
        return None

# ============================================================================
# Helper Functions
# ============================================================================

def calculate_cart_total(cart: dict) -> float:
    """Calculate total price of all items in cart."""
    return sum(item['unit_price'] * item['quantity'] for item in cart.get('items', []))


def get_or_create_cart(user_id: str) -> dict:
    """Get existing cart or create new one for user."""
    if user_id not in carts_db:
        timestamp = datetime.utcnow().isoformat() + "Z"
        carts_db[user_id] = {
            "user_id": user_id,
            "items": [],
            "created_at": timestamp,
            "updated_at": timestamp
        }
    return carts_db[user_id]

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes probes."""
    return jsonify({
        "status": "healthy",
        "service": "cart-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dapr_enabled": True
    }), 200

# ============================================================================
# Cart CRUD Endpoints
# ============================================================================

@app.route('/carts/<user_id>', methods=['GET'])
def get_cart(user_id):
    """
    Get user's shopping cart with calculated totals.
    """
    cart = get_or_create_cart(user_id)
    
    response = {
        **cart,
        "item_count": len(cart['items']),
        "total_quantity": sum(item['quantity'] for item in cart['items']),
        "subtotal": calculate_cart_total(cart)
    }
    
    logger.info(f"Retrieved cart for user: {user_id}")
    return jsonify(response), 200


@app.route('/carts/<user_id>/items', methods=['POST'])
def add_to_cart(user_id):
    """
    Add an item to user's cart.
    
    Request Body:
        product_id (required): Product to add
        quantity (optional, default=1): Quantity to add
    """
    data = request.get_json()
    
    if 'product_id' not in data:
        return jsonify({"error": "product_id is required"}), 400
    
    product_id = data['product_id']
    quantity = int(data.get('quantity', 1))
    
    if quantity < 1:
        return jsonify({"error": "Quantity must be at least 1"}), 400
    
    cart = get_or_create_cart(user_id)
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Check if product already in cart
    existing_item = next(
        (item for item in cart['items'] if item['product_id'] == product_id),
        None
    )
    
    if existing_item:
        # Update existing item quantity
        existing_item['quantity'] += quantity
        logger.info(f"Updated quantity for {product_id} in cart: {existing_item['quantity']}")
    else:
        # Fetch product details via Dapr service invocation
        product = invoke_service('product-service', f'products/{product_id}')
        
        if not product:
            # Fallback: use provided data or defaults
            product_name = data.get('product_name', f'Product {product_id}')
            unit_price = float(data.get('unit_price', 0))
        else:
            product_name = product.get('name', f'Product {product_id}')
            unit_price = float(product.get('price', 0))
        
        # Add new item to cart
        new_item = {
            "item_id": f"cart-item-{uuid.uuid4().hex[:8]}",
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "added_at": timestamp
        }
        cart['items'].append(new_item)
        logger.info(f"Added new item {product_id} to cart")
    
    cart['updated_at'] = timestamp
    
    # Publish cart.item_added event
    publish_event(CART_TOPIC, "cart.item_added", {
        "user_id": user_id,
        "product_id": product_id,
        "quantity": quantity,
        "cart_total": calculate_cart_total(cart),
        "action": "item_added"
    })
    
    logger.info(f"✅ Item added to cart for user: {user_id}")
    return jsonify({
        "message": "Item added to cart",
        "cart": cart,
        "subtotal": calculate_cart_total(cart)
    }), 201


@app.route('/carts/<user_id>/items/<item_id>', methods=['PUT'])
def update_cart_item(user_id, item_id):
    """
    Update quantity of a cart item.
    """
    if user_id not in carts_db:
        return jsonify({"error": "Cart not found"}), 404
    
    data = request.get_json()
    quantity = int(data.get('quantity', 1))
    
    cart = carts_db[user_id]
    item = next((i for i in cart['items'] if i['item_id'] == item_id), None)
    
    if not item:
        return jsonify({"error": "Item not found in cart"}), 404
    
    old_quantity = item['quantity']
    item['quantity'] = quantity
    cart['updated_at'] = datetime.utcnow().isoformat() + "Z"
    
    # Publish cart.item_updated event
    publish_event(CART_TOPIC, "cart.item_updated", {
        "user_id": user_id,
        "item_id": item_id,
        "product_id": item['product_id'],
        "old_quantity": old_quantity,
        "new_quantity": quantity,
        "action": "item_updated"
    })
    
    logger.info(f"✅ Updated cart item {item_id} quantity: {old_quantity} → {quantity}")
    return jsonify({"message": "Cart item updated", "item": item}), 200


@app.route('/carts/<user_id>/items/<item_id>', methods=['DELETE'])
def remove_from_cart(user_id, item_id):
    """
    Remove an item from cart.
    """
    if user_id not in carts_db:
        return jsonify({"error": "Cart not found"}), 404
    
    cart = carts_db[user_id]
    item = next((i for i in cart['items'] if i['item_id'] == item_id), None)
    
    if not item:
        return jsonify({"error": "Item not found in cart"}), 404
    
    cart['items'].remove(item)
    cart['updated_at'] = datetime.utcnow().isoformat() + "Z"
    
    # Publish cart.item_removed event
    publish_event(CART_TOPIC, "cart.item_removed", {
        "user_id": user_id,
        "item_id": item_id,
        "product_id": item['product_id'],
        "action": "item_removed"
    })
    
    logger.info(f"✅ Removed item {item_id} from cart")
    return jsonify({"message": "Item removed from cart"}), 200


@app.route('/carts/<user_id>', methods=['DELETE'])
def clear_cart(user_id):
    """
    Clear all items from user's cart.
    """
    if user_id not in carts_db:
        return jsonify({"error": "Cart not found"}), 404
    
    cart = carts_db[user_id]
    item_count = len(cart['items'])
    cart['items'] = []
    cart['updated_at'] = datetime.utcnow().isoformat() + "Z"
    
    # Publish cart.cleared event
    publish_event(CART_TOPIC, "cart.cleared", {
        "user_id": user_id,
        "items_removed": item_count,
        "action": "cart_cleared"
    })
    
    logger.info(f"✅ Cleared cart for user: {user_id} ({item_count} items removed)")
    return jsonify({"message": "Cart cleared", "items_removed": item_count}), 200


@app.route('/carts/<user_id>/checkout', methods=['POST'])
def checkout(user_id):
    """
    Process cart checkout - creates order and publishes to OrderService.
    """
    if user_id not in carts_db:
        return jsonify({"error": "Cart not found"}), 404
    
    cart = carts_db[user_id]
    
    if not cart['items']:
        return jsonify({"error": "Cart is empty"}), 400
    
    # Generate order details
    order_id = f"order-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    order = {
        "order_id": order_id,
        "user_id": user_id,
        "items": cart['items'].copy(),
        "subtotal": calculate_cart_total(cart),
        "tax": round(calculate_cart_total(cart) * 0.08, 2),  # 8% tax
        "total": round(calculate_cart_total(cart) * 1.08, 2),
        "status": "pending",
        "created_at": timestamp
    }
    
    # Publish order.created event to OrderService
    publish_event(ORDER_TOPIC, "order.created", {
        "order": order,
        "action": "order_created"
    })
    
    # Clear cart after checkout
    cart['items'] = []
    cart['updated_at'] = timestamp
    
    # Publish cart.checkout_completed event
    publish_event(CART_TOPIC, "cart.checkout_completed", {
        "user_id": user_id,
        "order_id": order_id,
        "total": order['total'],
        "action": "checkout_completed"
    })
    
    logger.info(f"✅ Checkout completed for user: {user_id}, Order: {order_id}")
    return jsonify({
        "message": "Checkout successful",
        "order_id": order_id,
        "total": order['total'],
        "status": "pending"
    }), 201

# ============================================================================
# Dapr Subscription Endpoints
# ============================================================================

@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    """Dapr subscription configuration."""
    subscriptions = [
        {
            "pubsubname": DAPR_PUBSUB_NAME,
            "topic": "product-events",
            "route": "/events/product"
        }
    ]
    return jsonify(subscriptions), 200


@app.route('/events/product', methods=['POST'])
def handle_product_event():
    """
    Handle product events (e.g., price updates).
    Updates cart item prices when products are modified.
    """
    event = request.get_json()
    logger.info(f"📥 Received product event: {event.get('type', 'unknown')}")
    
    event_data = event.get('data', {})
    event_type = event.get('type', 'unknown')
    
    # Update cart prices when product is updated
    if event_type == 'product.updated':
        product = event_data.get('product', {})
        product_id = product.get('id')
        new_price = product.get('price')
        
        if product_id and new_price:
            for cart in carts_db.values():
                for item in cart['items']:
                    if item['product_id'] == product_id:
                        item['unit_price'] = float(new_price)
                        logger.info(f"📦 Updated price for {product_id} in cart")
    
    return jsonify({"status": "processed"}), 200

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🛒 Starting CartService")
    logger.info(f"   Port: {SERVICE_PORT}")
    logger.info(f"   Dapr HTTP Port: {DAPR_HTTP_PORT}")
    logger.info(f"   Pub/Sub Component: {DAPR_PUBSUB_NAME}")
    logger.info(f"   Publishing Topics: {CART_TOPIC}, {ORDER_TOPIC}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)
