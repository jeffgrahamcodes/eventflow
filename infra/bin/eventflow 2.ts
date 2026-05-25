#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { EventFlowStack } from '../lib/eventflow-stack';

const app = new cdk.App();
new EventFlowStack(app, 'EventFlowStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
