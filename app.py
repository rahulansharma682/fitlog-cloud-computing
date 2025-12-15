#!/usr/bin/env python3
import aws_cdk as cdk
from fitlog_stack.fitlog_stack import FitLogStack

app = cdk.App()

FitLogStack(
    app,
    "FitLogStack",
    description="FitLog Gym Tracker - Serverless workout tracking application",
    env=cdk.Environment(
        account="0123456789", # Your Account Number
        region="us-east-1"   # Your Region
    )
)

app.synth()
