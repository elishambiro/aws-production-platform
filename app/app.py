import time
import uuid
import os
from datetime import datetime

import boto3
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['endpoint']
)
ITEMS_CREATED = Counter('items_created_total', 'Total items created')

# AWS / LocalStack config
AWS_ENDPOINT = os.getenv('AWS_ENDPOINT_URL', 'http://localstack:4566')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
TABLE_NAME = os.getenv('DYNAMODB_TABLE', 'aws-production-platform-dev')
QUEUE_URL = os.getenv('SQS_QUEUE_URL', '')


def get_dynamodb():
    return boto3.resource(
        'dynamodb',
        endpoint_url=AWS_ENDPOINT,
        region_name=AWS_REGION,
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )


def get_sqs():
    return boto3.client(
        'sqs',
        endpoint_url=AWS_ENDPOINT,
        region_name=AWS_REGION,
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )


@app.route('/health')
def health():
    start = time.time()
    REQUEST_COUNT.labels(method='GET', endpoint='/health', status='200').inc()
    REQUEST_LATENCY.labels(endpoint='/health').observe(time.time() - start)
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})


@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/items', methods=['GET'])
def get_items():
    start = time.time()
    try:
        table = get_dynamodb().Table(TABLE_NAME)
        result = table.scan()
        REQUEST_COUNT.labels(method='GET', endpoint='/items', status='200').inc()
        REQUEST_LATENCY.labels(endpoint='/items').observe(time.time() - start)
        return jsonify({'items': result.get('Items', []), 'count': result.get('Count', 0)})
    except Exception as e:
        REQUEST_COUNT.labels(method='GET', endpoint='/items', status='500').inc()
        return jsonify({'error': str(e)}), 500


@app.route('/items', methods=['POST'])
def create_item():
    start = time.time()
    try:
        data = request.get_json()
        item = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            **data
        }
        get_dynamodb().Table(TABLE_NAME).put_item(Item=item)

        if QUEUE_URL:
            get_sqs().send_message(QueueUrl=QUEUE_URL, MessageBody=str(item))

        ITEMS_CREATED.inc()
        REQUEST_COUNT.labels(method='POST', endpoint='/items', status='201').inc()
        REQUEST_LATENCY.labels(endpoint='/items').observe(time.time() - start)
        return jsonify(item), 201
    except Exception as e:
        REQUEST_COUNT.labels(method='POST', endpoint='/items', status='500').inc()
        return jsonify({'error': str(e)}), 500


@app.route('/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    start = time.time()
    try:
        table = get_dynamodb().Table(TABLE_NAME)
        result = table.scan(FilterExpression='id = :id', ExpressionAttributeValues={':id': item_id})
        items = result.get('Items', [])
        if not items:
            return jsonify({'error': 'Item not found'}), 404
        table.delete_item(Key={'id': items[0]['id'], 'timestamp': items[0]['timestamp']})
        REQUEST_COUNT.labels(method='DELETE', endpoint='/items', status='200').inc()
        REQUEST_LATENCY.labels(endpoint='/items').observe(time.time() - start)
        return jsonify({'deleted': item_id})
    except Exception as e:
        REQUEST_COUNT.labels(method='DELETE', endpoint='/items', status='500').inc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
