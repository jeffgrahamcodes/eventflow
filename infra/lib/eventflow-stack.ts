import * as cdk from "aws-cdk-lib";
import * as events from "aws-cdk-lib/aws-events";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as pythonLambda from "@aws-cdk/aws-lambda-python-alpha";
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

    new events.Rule(this, "OrderValidated", {
      eventBus: this.bus,
      ruleName: "eventflow-order-validated",
      eventPattern: {
        detailType: ["order.validated"],
      },
      targets: [new targets.SqsQueue(this.inventoryQueue)],
    });

    new events.Rule(this, "StockReserved", {
      eventBus: this.bus,
      ruleName: "eventflow-stock-reserved",
      eventPattern: {
        detailType: ["stock.reserved"],
      },
      targets: [new targets.SqsQueue(this.paymentQueue)],
    });

    new events.Rule(this, "PaymentCharged", {
      eventBus: this.bus,
      ruleName: "eventflow-payment-charged",
      eventPattern: {
        detailType: ["payment.charged"],
      },
      targets: [new targets.SqsQueue(this.orderQueue)],
    });

    new events.Rule(this, "OrderConfirmed", {
      eventBus: this.bus,
      ruleName: "eventflow-order-confirmed",
      eventPattern: {
        detailType: ["order.confirmed"],
      },
      targets: [new targets.SqsQueue(this.notificationQueue)],
    });

    new events.Rule(this, "PaymentFailedToOrder", {
      eventBus: this.bus,
      ruleName: "eventflow-payment-failed-to-order",
      eventPattern: {
        detailType: ["payment.failed"],
      },
      targets: [new targets.SqsQueue(this.orderQueue)],
    });

    new events.Rule(this, "PaymentFailedToNotification", {
      eventBus: this.bus,
      ruleName: "eventflow-payment-failed-to-notification",
      eventPattern: {
        detailType: ["payment.failed"],
      },
      targets: [new targets.SqsQueue(this.notificationQueue)],
    });

    new events.Rule(this, "StockInsufficientToOrder", {
      eventBus: this.bus,
      ruleName: "eventflow-stock-insufficient-to-order",
      eventPattern: {
        detailType: ["stock.insufficient"],
      },
      targets: [new targets.SqsQueue(this.orderQueue)],
    });

    new events.Rule(this, "StockInsufficientToNotification", {
      eventBus: this.bus,
      ruleName: "eventflow-stock-insufficient-to-notification",
      eventPattern: {
        detailType: ["stock.insufficient"],
      },
      targets: [new targets.SqsQueue(this.notificationQueue)],
    });

    new events.Rule(this, "OrderCancelledToInventory", {
      eventBus: this.bus,
      ruleName: "eventflow-order-cancelled-to-inventory",
      eventPattern: {
        detailType: ["order.cancelled"],
      },
      targets: [new targets.SqsQueue(this.inventoryQueue)],
    });

    new events.Rule(this, "OrderCancelledToNotification", {
      eventBus: this.bus,
      ruleName: "eventflow-order-cancelled-to-notification",
      eventPattern: {
        detailType: ["order.cancelled"],
      },
      targets: [new targets.SqsQueue(this.notificationQueue)],
    });
  }
}
