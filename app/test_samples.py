from app.routes.complaints import submit_complaint

sample_data = [
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


if __name__ == '__main__':
    for s in sample_data:
        print(submit_complaint(s))
