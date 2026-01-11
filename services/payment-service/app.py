"""
PaymentService - E-Commerce Microservice
=========================================
This microservice handles payment processing as a Dapr pub/sub subscriber.
It receives payment requests from OrderService and processes payments.

Endpoints:
- GET  /health             - Health check endpoint
- GET  /payments           - List all payments
- GET  /payments/<id>      - Get payment by ID
- POST /payments/process   - Process payment manually

Dapr Integration:
- Subscribes to 'payment-events' topic (receives from OrderService)
- Publishes payment completion/failure events back to 'payment-events'
"""

import os
import json
import logging
import uuid
import random
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
logger = logging.getLogger('PaymentService')

# Dapr configuration
DAPR_HTTP_PORT = os.getenv('DAPR_HTTP_PORT', '3500')
DAPR_PUBSUB_NAME = os.getenv('DAPR_PUBSUB_NAME', 'pubsub')
PAYMENT_TOPIC = 'payment-events'

# Service port
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5004'))

# Payment simulation configuration
SIMULATE_FAILURES = os.getenv('SIMULATE_FAILURES', 'false').lower() == 'true'
FAILURE_RATE = float(os.getenv('FAILURE_RATE', '0.1'))  # 10% failure rate

# ============================================================================
# In-Memory Payment Store (In production, use DynamoDB)
# ============================================================================

payments_db = {
    "pay-sample001": {
        "payment_id": "pay-sample001",
        "order_id": "order-sample001",
        "user_id": "user-001",
        "amount": 167.98,
        "currency": "USD",
        "status": "completed",
        "payment_method": "credit_card",
        "card_last_four": "4242",
        "transaction_id": "txn-abc123def456",
        "created_at": "2026-01-10T14:35:00Z",
        "processed_at": "2026-01-10T14:35:05Z"
    }
}

# Payment status values
PAYMENT_STATUS = ['pending', 'processing', 'completed', 'failed', 'refunded', 'cancelled']

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
        "source": "payment-service",
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
# Payment Processing Logic
# ============================================================================

def process_payment(order_id: str, user_id: str, amount: float, 
                   payment_method: str = "credit_card") -> dict:
    """
    Process a payment transaction.
    
    In production, this would integrate with:
    - Stripe, Square, or other payment processors
    - AWS Payment Cryptography for secure transactions
    - PCI-compliant payment handling
    
    Returns:
        dict: Payment result with status and details
    """
    payment_id = f"pay-{uuid.uuid4().hex[:8]}"
    transaction_id = f"txn-{uuid.uuid4().hex[:12]}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    logger.info(f"💳 Processing payment for order: {order_id}")
    logger.info(f"   Amount: ${amount:.2f}")
    logger.info(f"   Method: {payment_method}")
    
    # Simulate payment processing delay (in production, actual API call)
    # time.sleep(random.uniform(0.5, 2.0))
    
    # Simulate payment success/failure
    if SIMULATE_FAILURES and random.random() < FAILURE_RATE:
        # Simulate payment failure
        payment = {
            "payment_id": payment_id,
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "currency": "USD",
            "status": "failed",
            "payment_method": payment_method,
            "error_code": "CARD_DECLINED",
            "error_message": "The card was declined",
            "created_at": timestamp,
            "processed_at": timestamp
        }
        logger.error(f"❌ Payment failed: {payment_id} - Card declined")
    else:
        # Simulate successful payment
        payment = {
            "payment_id": payment_id,
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "currency": "USD",
            "status": "completed",
            "payment_method": payment_method,
            "card_last_four": str(random.randint(1000, 9999)),
            "transaction_id": transaction_id,
            "created_at": timestamp,
            "processed_at": timestamp
        }
        logger.info(f"✅ Payment successful: {payment_id}")
        logger.info(f"   Transaction ID: {transaction_id}")
    
    # Store payment record
    payments_db[payment_id] = payment
    
    return payment

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes probes."""
    return jsonify({
        "status": "healthy",
        "service": "payment-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dapr_enabled": True,
        "subscriptions": ["payment-events"],
        "simulate_failures": SIMULATE_FAILURES
    }), 200

# ============================================================================
# Payment Endpoints
# ============================================================================

@app.route('/payments', methods=['GET'])
def list_payments():
    """
    List all payments with optional status filtering.
    """
    status = request.args.get('status')
    
    if status:
        filtered = {k: v for k, v in payments_db.items() if v['status'] == status}
        return jsonify({"payments": list(filtered.values()), "count": len(filtered)}), 200
    
    logger.info(f"Listed {len(payments_db)} payments")
    return jsonify({"payments": list(payments_db.values()), "count": len(payments_db)}), 200


@app.route('/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    """
    Get payment details by ID.
    """
    if payment_id not in payments_db:
        return jsonify({"error": "Payment not found"}), 404
    
    return jsonify(payments_db[payment_id]), 200


@app.route('/payments/order/<order_id>', methods=['GET'])
def get_payment_by_order(order_id):
    """
    Get payment for a specific order.
    """
    payment = next((p for p in payments_db.values() if p['order_id'] == order_id), None)
    
    if not payment:
        return jsonify({"error": "Payment not found for order"}), 404
    
    return jsonify(payment), 200


@app.route('/payments/process', methods=['POST'])
def process_payment_endpoint():
    """
    Process a payment manually (API endpoint).
    
    Request Body:
        order_id (required): Order to process payment for
        user_id (required): User making the payment
        amount (required): Payment amount
        payment_method (optional): Payment method (default: credit_card)
    """
    data = request.get_json()
    
    required = ['order_id', 'user_id', 'amount']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": "Missing fields", "missing": missing}), 400
    
    # Process payment
    payment = process_payment(
        order_id=data['order_id'],
        user_id=data['user_id'],
        amount=float(data['amount']),
        payment_method=data.get('payment_method', 'credit_card')
    )
    
    # Publish result event
    if payment['status'] == 'completed':
        publish_event(PAYMENT_TOPIC, 'payment.completed', {
            "payment_id": payment['payment_id'],
            "order_id": payment['order_id'],
            "user_id": payment['user_id'],
            "amount": payment['amount'],
            "transaction_id": payment.get('transaction_id'),
            "action": "payment_completed"
        })
    else:
        publish_event(PAYMENT_TOPIC, 'payment.failed', {
            "payment_id": payment['payment_id'],
            "order_id": payment['order_id'],
            "user_id": payment['user_id'],
            "amount": payment['amount'],
            "error": payment.get('error_message', 'Payment failed'),
            "action": "payment_failed"
        })
    
    status_code = 200 if payment['status'] == 'completed' else 402
    return jsonify(payment), status_code


@app.route('/payments/<payment_id>/refund', methods=['POST'])
def refund_payment(payment_id):
    """
    Refund a completed payment.
    """
    if payment_id not in payments_db:
        return jsonify({"error": "Payment not found"}), 404
    
    payment = payments_db[payment_id]
    
    if payment['status'] != 'completed':
        return jsonify({"error": "Can only refund completed payments"}), 400
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    refund_id = f"ref-{uuid.uuid4().hex[:8]}"
    
    payment['status'] = 'refunded'
    payment['refund_id'] = refund_id
    payment['refunded_at'] = timestamp
    
    # Publish refund event
    publish_event(PAYMENT_TOPIC, 'payment.refunded', {
        "payment_id": payment_id,
        "refund_id": refund_id,
        "order_id": payment['order_id'],
        "amount": payment['amount'],
        "action": "payment_refunded"
    })
    
    logger.info(f"💰 Payment refunded: {payment_id} → {refund_id}")
    return jsonify(payment), 200

# ============================================================================
# Dapr Subscription Endpoints
# ============================================================================

@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    """
    Dapr subscription configuration.
    PaymentService subscribes to payment-events topic.
    """
    subscriptions = [
        {
            "pubsubname": DAPR_PUBSUB_NAME,
            "topic": "payment-events",
            "route": "/events/payment"
        }
    ]
    return jsonify(subscriptions), 200


@app.route('/events/payment', methods=['POST'])
def handle_payment_event():
    """
    Handle incoming payment events.
    
    Event Types:
    - payment.requested: Process new payment request from OrderService
    """
    event = request.get_json()
    event_type = event.get('type', 'unknown')
    event_data = event.get('data', {})
    
    logger.info(f"📥 Received payment event: {event_type}")
    logger.info(f"   Event ID: {event.get('id', 'N/A')}")
    logger.info(f"   Source: {event.get('source', 'N/A')}")
    
    if event_type == 'payment.requested':
        # Process payment request from OrderService
        order_id = event_data.get('order_id')
        user_id = event_data.get('user_id')
        amount = event_data.get('amount', 0)
        
        if not all([order_id, user_id, amount]):
            logger.error("Missing required payment data in event")
            return jsonify({"status": "error", "message": "Missing payment data"}), 400
        
        logger.info(f"💳 Processing payment request for order: {order_id}")
        
        # Process the payment
        payment = process_payment(
            order_id=order_id,
            user_id=user_id,
            amount=float(amount)
        )
        
        # Publish result back to the same topic for OrderService to consume
        if payment['status'] == 'completed':
            publish_event(PAYMENT_TOPIC, 'payment.completed', {
                "payment_id": payment['payment_id'],
                "order_id": order_id,
                "user_id": user_id,
                "amount": payment['amount'],
                "transaction_id": payment.get('transaction_id'),
                "action": "payment_completed"
            })
            logger.info(f"✅ Payment completed for order: {order_id}")
        else:
            publish_event(PAYMENT_TOPIC, 'payment.failed', {
                "payment_id": payment['payment_id'],
                "order_id": order_id,
                "user_id": user_id,
                "amount": payment['amount'],
                "error": payment.get('error_message', 'Payment processing failed'),
                "action": "payment_failed"
            })
            logger.error(f"❌ Payment failed for order: {order_id}")
        
        return jsonify({
            "status": "processed",
            "payment_status": payment['status'],
            "payment_id": payment['payment_id']
        }), 200
    
    # Handle other event types (pass through)
    logger.info(f"Event type '{event_type}' acknowledged")
    return jsonify({"status": "acknowledged", "event_type": event_type}), 200

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("💳 Starting PaymentService")
    logger.info(f"   Port: {SERVICE_PORT}")
    logger.info(f"   Dapr HTTP Port: {DAPR_HTTP_PORT}")
    logger.info(f"   Pub/Sub Component: {DAPR_PUBSUB_NAME}")
    logger.info(f"   Subscribing to: payment-events")
    logger.info(f"   Simulate Failures: {SIMULATE_FAILURES}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)
