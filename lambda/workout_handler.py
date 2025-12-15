import json
import boto3
import os
from datetime import datetime
import random

s3 = boto3.client('s3')
sns = boto3.client('sns')

# Get environment variables
DATA_BUCKET_NAME = os.environ.get('DATA_BUCKET_NAME')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

# Motivational messages
MOTIVATIONAL_MESSAGES = [
    "Great workout! Keep pushing! 💪",
    "You're crushing it! Consistency is key! 🔥",
    "Workout logged! Your dedication is impressive! 🌟",
    "Another step closer to your goals! Keep it up! 🚀",
    "Fantastic effort! Your future self will thank you! 💯",
    "Beast mode activated! Well done! 🦁",
    "Progress over perfection! You're doing amazing! ⭐",
    "Every rep counts! Great job today! 🏋️",
]


def lambda_handler(event, context):
    """
    Lambda function to handle workout logging.
    Supports Lambda Function URLs, ALB, and API Gateway.
    """

    print(f"Received event: {json.dumps(event)}")

    try:
        # Handle OPTIONS preflight request for CORS
        request_method = event.get('requestContext', {}).get('http', {}).get('method') or event.get('httpMethod')
        if request_method == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight'})

        # Handle health check requests
        if 'rawPath' in event and event.get('rawPath') == '/health':
            return create_response(200, {'status': 'healthy', 'message': 'Lambda is running'})
        if 'path' in event and event.get('path') == '/health':
            return create_response(200, {'status': 'healthy', 'message': 'Lambda is running'})

        # Parse request body (works for Function URL, ALB, and API Gateway)
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        # Extract workout details
        user_id = body.get('userId', 'anonymous')
        exercise = body.get('exercise')
        sets = body.get('sets')
        reps = body.get('reps')
        weight = body.get('weight')
        notes = body.get('notes', '')

        # Validate required fields
        if not exercise:
            return create_response(400, {'error': 'Exercise name is required'})

        # Create workout record
        timestamp = datetime.utcnow()
        workout_data = {
            'userId': user_id,
            'exercise': exercise,
            'sets': int(sets) if sets else None,
            'reps': int(reps) if reps else None,
            'weight': float(weight) if weight else None,
            'notes': notes,
            'timestamp': timestamp.isoformat(),
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M:%S')
        }

        # Save to S3
        file_key = f"{user_id}/{timestamp.strftime('%Y/%m')}/{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"

        print(f"Saving workout to S3: {DATA_BUCKET_NAME}/{file_key}")

        s3.put_object(
            Bucket=DATA_BUCKET_NAME,
            Key=file_key,
            Body=json.dumps(workout_data, indent=2),
            ContentType='application/json',
            Metadata={
                'user-id': user_id,
                'exercise': exercise,
                'date': workout_data['date']
            }
        )

        # Send SNS notification
        message = random.choice(MOTIVATIONAL_MESSAGES)

        workout_summary = f"""
{message}

Workout Details:
━━━━━━━━━━━━━━━━━━
Exercise: {exercise}
Sets: {sets or 'N/A'}
Reps: {reps or 'N/A'}
Weight: {weight or 'N/A'} lbs
Date: {workout_data['date']}
Time: {workout_data['time']}
"""

        if notes:
            workout_summary += f"\nNotes: {notes}"

        print(f"Publishing to SNS: {SNS_TOPIC_ARN}")

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f'FitLog: Workout Logged - {exercise}',
            Message=workout_summary
        )

        # Return success response
        return create_response(200, {
            'message': 'Workout logged successfully!',
            'data': workout_data,
            'motivation': message
        })

    except Exception as e:
        print(f"Error processing workout: {str(e)}")
        import traceback
        traceback.print_exc()

        return create_response(500, {
            'error': 'Failed to log workout',
            'details': str(e)
        })


def create_response(status_code, body):
    """Helper function to create Lambda response with CORS headers (works for Function URLs, ALB, and API Gateway)"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body)
    }
