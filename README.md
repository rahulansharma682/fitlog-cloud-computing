# FitLog - Serverless Gym Tracker

A simplified serverless workout tracking application built with AWS CDK.

## Architecture

**AWS Services Used:**
- **S3** - Frontend hosting (static website) and data storage
- **Lambda** - API backend with Function URL
- **SNS** - Workout notifications
- **Route53** - DNS management for rchemitiganti.com
- **CloudWatch** - Automatic logging (built-in with Lambda)
- **IAM** - Permissions (automatic with CDK)

## Quick Start

### Prerequisites
- AWS CLI configured with credentials
- Python 3.9+
- AWS CDK installed (`npm install -g aws-cdk`)
- Domain: rchemitiganti.com (with hosted zone in Route53)

### Deployment

1. **Bootstrap CDK (first time only)**
   ```bash
   cdk bootstrap aws://784450714003/us-east-1
   ```

2. **Deploy the stack**
   ```bash
   cdk deploy
   ```

   Deployment time: ~5-10 minutes

3. **Upload frontend files**
   ```bash
   aws s3 sync frontend/ s3://<frontend-bucket-name>/ --delete
   ```
   (Replace `<frontend-bucket-name>` with output from deployment)

### Configuration

Set optional context in `cdk.json`:
```json
{
  "context": {
    "notification_email": "your-email@example.com",
    "domain_name": "rchemitiganti.com"
  }
}
```

## Endpoints

After deployment:
- **Frontend**: http://rchemitiganti.com
- **API**: https://api.rchemitiganti.com
- **Direct Lambda URL**: (check CDK outputs)

## Clean Up

```bash
cdk destroy
```

## Project Structure

```
fitlog-cdk/
├── app.py                 # CDK app entry point
├── fitlog_stack/          # Stack definition
│   └── fitlog_stack.py
├── lambda/                # Lambda function code
│   └── workout_handler.py
├── frontend/              # Static website files
│   └── index.html
├── cdk.json              # CDK configuration
└── requirements.txt      # Python dependencies
```

## Key Features

- ✅ Serverless architecture
- ✅ Fast deployment (~5-10 min vs 30-45 min with CloudFront)
- ✅ HTTPS API via Lambda Function URL
- ✅ Custom domain support with Route53
- ✅ Email notifications for workouts
- ✅ Automatic CloudWatch logging
- ✅ CORS enabled for frontend
