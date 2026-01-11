"""
ProductService - E-Commerce Microservice
=========================================
This microservice handles product catalog management and publishes product events
using Dapr pub/sub messaging to AWS SNS/SQS.

Endpoints:
- GET  /health          - Health check endpoint
- GET  /products        - List all products
- GET  /products/<id>   - Get product by ID
- POST /products        - Create new product (publishes event)
- PUT  /products/<id>   - Update product (publishes event)
- DELETE /products/<id> - Delete product (publishes event)

Dapr Integration:
- Publishes to 'product-events' topic on 'pubsub' component
- Events: product.created, product.updated, product.deleted
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

# Flask application instance
app = Flask(__name__)

# Configure structured logging for CloudWatch compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ProductService')

# Dapr configuration - sidecar runs on localhost:3500 by default
DAPR_HTTP_PORT = os.getenv('DAPR_HTTP_PORT', '3500')
DAPR_PUBSUB_NAME = os.getenv('DAPR_PUBSUB_NAME', 'pubsub')
PRODUCT_TOPIC = 'product-events'

# Service port configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5001'))

# ============================================================================
# In-Memory Product Store (In production, use DynamoDB or RDS)
# ============================================================================

products_db = {
    "prod-001": {
        "id": "prod-001",
        "name": "Wireless Bluetooth Headphones",
        "description": "Premium noise-cancelling wireless headphones",
        "price": 149.99,
        "category": "Electronics",
        "stock": 100,
        "created_at": "2026-01-10T10:00:00Z",
        "updated_at": "2026-01-10T10:00:00Z"
    },
    "prod-002": {
        "id": "prod-002",
        "name": "Smart Watch Pro",
        "description": "Advanced fitness tracking smartwatch",
        "price": 299.99,
        "category": "Electronics",
        "stock": 50,
        "created_at": "2026-01-10T10:00:00Z",
        "updated_at": "2026-01-10T10:00:00Z"
    },
    "prod-003": {
        "id": "prod-003",
        "name": "Organic Cotton T-Shirt",
        "description": "Comfortable eco-friendly t-shirt",
        "price": 29.99,
        "category": "Clothing",
        "stock": 200,
        "created_at": "2026-01-10T10:00:00Z",
        "updated_at": "2026-01-10T10:00:00Z"
    }
}

# ============================================================================
# Dapr Pub/Sub Helper Functions
# ============================================================================

def publish_event(topic: str, event_type: str, data: dict) -> bool:
    """
    Publish an event to Dapr pub/sub component (AWS SNS/SQS).
    
    Args:
        topic: The topic name to publish to
        event_type: Type of event (e.g., 'product.created')
        data: Event payload data
    
    Returns:
        bool: True if publish successful, False otherwise
    """
    dapr_url = f"http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/{DAPR_PUBSUB_NAME}/{topic}"
    
    # Construct CloudEvents-compliant message
    event = {
        "id": str(uuid.uuid4()),
        "source": "product-service",
        "type": event_type,
        "specversion": "1.0",
        "datacontenttype": "application/json",
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        logger.info(f"Publishing event to topic '{topic}': {event_type}")
        logger.debug(f"Event payload: {json.dumps(event)}")
        
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
            logger.error(f"❌ Failed to publish event: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error publishing event: {str(e)}")
        return False

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Kubernetes liveness/readiness probes.
    Returns service status and metadata.
    """
    return jsonify({
        "status": "healthy",
        "service": "product-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dapr_enabled": True
    }), 200

# ============================================================================
# Product CRUD Endpoints
# ============================================================================

@app.route('/products', methods=['GET'])
def list_products():
    """
    List all products in the catalog.
    Supports optional filtering by category.
    
    Query Parameters:
        category (optional): Filter products by category
    """
    category = request.args.get('category')
    
    if category:
        filtered = {k: v for k, v in products_db.items() if v['category'].lower() == category.lower()}
        logger.info(f"Listed {len(filtered)} products in category: {category}")
        return jsonify({"products": list(filtered.values()), "count": len(filtered)}), 200
    
    logger.info(f"Listed all {len(products_db)} products")
    return jsonify({"products": list(products_db.values()), "count": len(products_db)}), 200


@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """
    Get a specific product by ID.
    
    Args:
        product_id: The unique product identifier
    """
    if product_id not in products_db:
        logger.warning(f"Product not found: {product_id}")
        return jsonify({"error": "Product not found", "product_id": product_id}), 404
    
    logger.info(f"Retrieved product: {product_id}")
    return jsonify(products_db[product_id]), 200


@app.route('/products', methods=['POST'])
def create_product():
    """
    Create a new product and publish 'product.created' event.
    
    Request Body:
        name (required): Product name
        description (required): Product description
        price (required): Product price
        category (required): Product category
        stock (required): Initial stock quantity
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'description', 'price', 'category', 'stock']
    missing_fields = [f for f in required_fields if f not in data]
    
    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "missing_fields": missing_fields
        }), 400
    
    # Generate product ID and timestamps
    product_id = f"prod-{uuid.uuid4().hex[:6]}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Create product record
    product = {
        "id": product_id,
        "name": data['name'],
        "description": data['description'],
        "price": float(data['price']),
        "category": data['category'],
        "stock": int(data['stock']),
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    # Store in database
    products_db[product_id] = product
    
    # Publish product.created event via Dapr
    publish_event(PRODUCT_TOPIC, "product.created", {
        "product_id": product_id,
        "product": product,
        "action": "created"
    })
    
    logger.info(f"✅ Created product: {product_id} - {product['name']}")
    return jsonify(product), 201


@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """
    Update an existing product and publish 'product.updated' event.
    
    Args:
        product_id: The unique product identifier
    
    Request Body:
        Any product fields to update (name, description, price, category, stock)
    """
    if product_id not in products_db:
        logger.warning(f"Product not found for update: {product_id}")
        return jsonify({"error": "Product not found", "product_id": product_id}), 404
    
    data = request.get_json()
    product = products_db[product_id]
    
    # Track changes for event
    changes = {}
    
    # Update allowed fields
    updatable_fields = ['name', 'description', 'price', 'category', 'stock']
    for field in updatable_fields:
        if field in data:
            old_value = product.get(field)
            new_value = data[field]
            if field == 'price':
                new_value = float(new_value)
            elif field == 'stock':
                new_value = int(new_value)
            
            if old_value != new_value:
                changes[field] = {"old": old_value, "new": new_value}
                product[field] = new_value
    
    # Update timestamp
    product['updated_at'] = datetime.utcnow().isoformat() + "Z"
    
    # Publish product.updated event via Dapr
    if changes:
        publish_event(PRODUCT_TOPIC, "product.updated", {
            "product_id": product_id,
            "product": product,
            "changes": changes,
            "action": "updated"
        })
    
    logger.info(f"✅ Updated product: {product_id} - Changes: {list(changes.keys())}")
    return jsonify(product), 200


@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    Delete a product and publish 'product.deleted' event.
    
    Args:
        product_id: The unique product identifier
    """
    if product_id not in products_db:
        logger.warning(f"Product not found for deletion: {product_id}")
        return jsonify({"error": "Product not found", "product_id": product_id}), 404
    
    # Get product before deletion for event
    deleted_product = products_db.pop(product_id)
    
    # Publish product.deleted event via Dapr
    publish_event(PRODUCT_TOPIC, "product.deleted", {
        "product_id": product_id,
        "product": deleted_product,
        "action": "deleted"
    })
    
    logger.info(f"✅ Deleted product: {product_id} - {deleted_product['name']}")
    return jsonify({"message": "Product deleted", "product_id": product_id}), 200


@app.route('/products/<product_id>/stock', methods=['PATCH'])
def update_stock(product_id):
    """
    Update product stock level (used by order service for inventory management).
    Publishes 'product.stock_updated' event.
    
    Args:
        product_id: The unique product identifier
    
    Request Body:
        quantity: Quantity to add (positive) or subtract (negative)
    """
    if product_id not in products_db:
        return jsonify({"error": "Product not found", "product_id": product_id}), 404
    
    data = request.get_json()
    quantity = int(data.get('quantity', 0))
    
    product = products_db[product_id]
    old_stock = product['stock']
    new_stock = old_stock + quantity
    
    if new_stock < 0:
        return jsonify({
            "error": "Insufficient stock",
            "current_stock": old_stock,
            "requested_change": quantity
        }), 400
    
    product['stock'] = new_stock
    product['updated_at'] = datetime.utcnow().isoformat() + "Z"
    
    # Publish stock update event
    publish_event(PRODUCT_TOPIC, "product.stock_updated", {
        "product_id": product_id,
        "old_stock": old_stock,
        "new_stock": new_stock,
        "change": quantity,
        "action": "stock_updated"
    })
    
    logger.info(f"✅ Stock updated for {product_id}: {old_stock} → {new_stock}")
    return jsonify({"product_id": product_id, "old_stock": old_stock, "new_stock": new_stock}), 200

# ============================================================================
# Dapr Subscription Endpoint (for receiving events from other services)
# ============================================================================

@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    """
    Dapr subscription configuration endpoint.
    Tells Dapr which topics this service subscribes to.
    """
    subscriptions = [
        {
            "pubsubname": DAPR_PUBSUB_NAME,
            "topic": "order-events",
            "route": "/events/order"
        }
    ]
    return jsonify(subscriptions), 200


@app.route('/events/order', methods=['POST'])
def handle_order_event():
    """
    Handle order events (e.g., to update stock when orders are placed).
    This demonstrates bidirectional pub/sub communication.
    """
    event = request.get_json()
    logger.info(f"📥 Received order event: {json.dumps(event)}")
    
    event_data = event.get('data', {})
    event_type = event.get('type', 'unknown')
    
    # Handle stock reduction when order is placed
    if event_type == 'order.placed':
        items = event_data.get('items', [])
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            if product_id in products_db:
                products_db[product_id]['stock'] -= quantity
                logger.info(f"📦 Stock reduced for {product_id} by {quantity}")
    
    return jsonify({"status": "processed"}), 200

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 Starting ProductService")
    logger.info(f"   Port: {SERVICE_PORT}")
    logger.info(f"   Dapr HTTP Port: {DAPR_HTTP_PORT}")
    logger.info(f"   Pub/Sub Component: {DAPR_PUBSUB_NAME}")
    logger.info(f"   Publishing Topic: {PRODUCT_TOPIC}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)
