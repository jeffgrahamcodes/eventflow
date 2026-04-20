import * as cdk from "aws-cdk-lib";
import * as events from "aws-cdk-lib/aws-events";
import * as sqs from "aws-cdk-lib/aws-sqs";
import { Construct } from "constructs";

export class EventFlowStack extends cdk.Stack {
  public readonly bus: events.EventBus;
  public readonly orderQueue: sqs.Queue;
  public readonly inventoryQueue: sqs.Queue;
  public readonly paymentQueue: sqs.Queue;
  public readonly notificationQueue: sqs.Queue;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.bus = new events.EventBus(this, "Bus", {
      eventBusName: "eventflow-dev-bus",
    });

    this.bus.archive("Archive", {
      archiveName: "eventflow-dev-archive",
      description: "EventFlow event archive for replay",
      retention: cdk.Duration.days(30),
      eventPattern: {
        account: [cdk.Stack.of(this).account],
      },
    });

    new cdk.CfnOutput(this, "EventBusArn", {
      value: this.bus.eventBusArn,
      description: "EventFlow EventBridge bus ARN",
      exportName: "EventFlowBusArn",
    });

    const orderDlq = new sqs.Queue(this, "OrderDlq", {
      queueName: "eventflow-order-dlq",
    });

    this.orderQueue = new sqs.Queue(this, "OrderQueue", {
      queueName: "eventflow-order-queue",
      deadLetterQueue: {
        queue: orderDlq,
        maxReceiveCount: 3,
      },
      visibilityTimeout: cdk.Duration.seconds(60),
    });

    const inventoryDlq = new sqs.Queue(this, "InventoryDlq", {
      queueName: "eventflow-inventory-dlq",
    });

    this.inventoryQueue = new sqs.Queue(this, "InventoryQueue", {
      queueName: "eventflow-inventory-queue",
      deadLetterQueue: {
        queue: inventoryDlq,
        maxReceiveCount: 3,
      },
      visibilityTimeout: cdk.Duration.seconds(60),
    });

    const paymentDlq = new sqs.Queue(this, "PaymentDlq", {
      queueName: "eventflow-payment-dlq",
    });

    this.paymentQueue = new sqs.Queue(this, "PaymentQueue", {
      queueName: "eventflow-payment-queue",
      deadLetterQueue: {
        queue: paymentDlq,
        maxReceiveCount: 3,
      },
      visibilityTimeout: cdk.Duration.seconds(60),
    });

    const notificationDlq = new sqs.Queue(this, "NotificationDlq", {
      queueName: "eventflow-notification-dlq",
    });

    this.notificationQueue = new sqs.Queue(this, "NotificationQueue", {
      queueName: "eventflow-notification-queue",
      deadLetterQueue: {
        queue: notificationDlq,
        maxReceiveCount: 3,
      },
      visibilityTimeout: cdk.Duration.seconds(60),
    });
  }
}
