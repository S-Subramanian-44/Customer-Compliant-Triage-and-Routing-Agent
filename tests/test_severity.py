import os
import pytest
from fastapi.testclient import TestClient

# Ensure app path
import sys
sys.path.insert(0, os.path.abspath('.'))

from app.main import app

client = TestClient(app)

sample_payloads = [
    {
        "customer_name": "Alice",
        "customer_email": "alice@example.com",
        "complaint_description": "My washing machine stopped working after two days. It's making a loud noise and won't spin.",
        "channel": "Web",
        "subject": "Washing machine malfunction"
    },
    {
        "customer_name": "Bob",
        "customer_email": "bob@example.com",
        "complaint_description": "I was charged twice for my subscription. Please refund the extra charge.",
        "channel": "Web",
        "subject": "Double charge"
    },
    {
        "customer_name": "Carol",
        "customer_email": "carol@example.com",
        "complaint_description": "My package was supposed to arrive last week and it's still not here.",
        "channel": "Web",
        "subject": "Late delivery"
    },
    {
        "customer_name": "Dan",
        "customer_email": "dan@example.com",
        "complaint_description": "Support person was rude and didn't resolve my issue.",
        "channel": "Web",
        "subject": "Bad support experience"
    },
    {
        "customer_name": "Eve",
        "customer_email": "eve@example.com",
        "complaint_description": "The app crashes on login with error code 500.",
        "channel": "Web",
        "subject": "App crash"
    }
]


def test_severity_and_keywords():
    ids = []
    for p in sample_payloads:
        r = client.post('/submit_complaint', json=p)
        assert r.status_code == 200
        data = r.json()
        assert 'id' in data
        ids.append(data['id'])

    # fetch each complaint detail via admin endpoint (use ADMIN_API_KEY env)
    api_key = os.getenv('ADMIN_API_KEY', 'secret_admin_key')
    headers = {'x-api-key': api_key}
    for cid in ids:
        r = client.get(f'/admin/complaint/{cid}', headers=headers)
        assert r.status_code == 200
        c = r.json()
        # Ensure severity is one of allowed values
        assert c['severity'] in [None, 'Low', 'Medium', 'High', 'Urgent']
        # keywords exists (string or None)
        assert 'keywords' in c
        # sentiment should be present
    assert 'sentiment' in c