from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    CfnOutput,
    RemovalPolicy,
    Duration,
)
from constructs import Construct


class FitLogStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get configuration from context
        notification_email = self.node.try_get_context("notification_email")
        domain_name = self.node.try_get_context("domain_name") or "rchemitiganti.com"

        # ==================== S3 Buckets ====================

        # Frontend bucket for static website hosting
        # Bucket name MUST match domain name for Route53 alias to work
        frontend_bucket = s3.Bucket(
            self,
            "FitLogFrontendBucket",
            bucket_name=domain_name,  # Must match domain for Route53 alias
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Data bucket for workout logs (private)
        data_bucket = s3.Bucket(
            self,
            "FitLogDataBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ==================== SNS Topic ====================

        notification_topic = sns.Topic(
            self,
            "FitLogNotificationTopic",
            display_name="FitLog Workout Notifications",
            topic_name="FitLogNotifications"
        )

        # Subscribe email if provided
        if notification_email:
            notification_topic.add_subscription(
                subscriptions.EmailSubscription(notification_email)
            )

        # ==================== Lambda Function ====================

        workout_handler = _lambda.Function(
            self,
            "WorkoutHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="workout_handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "DATA_BUCKET_NAME": data_bucket.bucket_name,
                "SNS_TOPIC_ARN": notification_topic.topic_arn,
            },
            timeout=Duration.seconds(30),
            memory_size=256,
        )

        # Grant permissions to Lambda
        data_bucket.grant_read_write(workout_handler)
        notification_topic.grant_publish(workout_handler)

        # Create Lambda Function URL (HTTPS endpoint)
        # Note: CORS is handled in Lambda code, not here, to avoid duplicate headers
        function_url = workout_handler.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE
        )

        # ==================== Route 53 DNS ====================

        # Lookup existing hosted zone for the domain
        hosted_zone = route53.HostedZone.from_lookup(
            self,
            "FitLogHostedZone",
            domain_name=domain_name
        )

        # A record for root domain pointing to S3 website
        route53.ARecord(
            self,
            "FitLogFrontendARecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(
                route53_targets.BucketWebsiteTarget(frontend_bucket)
            )
        )

        # CNAME record for api subdomain pointing to Lambda Function URL
        lambda_url_domain = function_url.url.replace("https://", "").replace("/", "")

        route53.CnameRecord(
            self,
            "FitLogAPICName",
            zone=hosted_zone,
            record_name="api",
            domain_name=lambda_url_domain
        )

        # ==================== Outputs ====================

        CfnOutput(
            self,
            "FrontendBucketName",
            value=frontend_bucket.bucket_name,
            description="Frontend S3 Bucket Name"
        )

        CfnOutput(
            self,
            "FrontendBucketWebsiteURL",
            value=frontend_bucket.bucket_website_url,
            description="Frontend S3 Website URL"
        )

        CfnOutput(
            self,
            "CustomDomainURL",
            value=f"http://{domain_name}",
            description="Custom Domain URL for Frontend (configure DNS first)"
        )

        CfnOutput(
            self,
            "LambdaFunctionURL",
            value=function_url.url,
            description="Lambda Function URL (Direct HTTPS endpoint)"
        )

        CfnOutput(
            self,
            "APIEndpoint",
            value=f"https://api.{domain_name}",
            description="API Endpoint via Route53 CNAME (after DNS propagation)"
        )

        CfnOutput(
            self,
            "DataBucketName",
            value=data_bucket.bucket_name,
            description="S3 Bucket for workout data"
        )

        CfnOutput(
            self,
            "SNSTopicArn",
            value=notification_topic.topic_arn,
            description="SNS Topic ARN for notifications"
        )

        CfnOutput(
            self,
            "HostedZoneId",
            value=hosted_zone.hosted_zone_id,
            description="Route 53 Hosted Zone ID"
        )
