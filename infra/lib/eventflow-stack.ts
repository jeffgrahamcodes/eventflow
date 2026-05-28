import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as events from "aws-cdk-lib/aws-events";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as pythonLambda from "@aws-cdk/aws-lambda-python-alpha";
import * as lambdaEventSources from "aws-cdk-lib/aws-lambda-event-sources";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";

export class EventFlowStack extends cdk.Stack {
  public readonly bus: events.EventBus;
  public readonly orderQueue: sqs.Queue;
  public readonly inventoryQueue: sqs.Queue;
  public readonly paymentQueue: sqs.Queue;
  public readonly notificationQueue: sqs.Queue;
  public readonly ordersTable: dynamodb.Table;
  public readonly inventoryTable: dynamodb.Table;
  public readonly paymentRecordsTable: dynamodb.Table;

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

    const orderHandler = new pythonLambda.PythonFunction(this, "OrderHandler", {
      entry: "../",
      index: "infra/lambda/order_handler.py",
      handler: "handler",
      runtime: lambda.Runtime.PYTHON_3_12,
      memorySize: 256,
      timeout: cdk.Duration.seconds(10),
      environment: {
        POWERTOOLS_SERVICE_NAME: "order-service",
      },
      bundling: {
        assetExcludes: [
          "infra/cdk.out",
          "infra/node_modules",
          "infra/dist",
          ".venv",
          ".git",
          "__pycache__",
          "*.pyc",
        ],
      },
    });

    orderHandler.addEventSource(
      new lambdaEventSources.SqsEventSource(this.orderQueue, {
        batchSize: 1,
      }),
    );

    this.bus.grantPutEventsTo(orderHandler);

    const inventoryHandler = new pythonLambda.PythonFunction(
      this,
      "InventoryHandler",
      {
        entry: "../",
        index: "infra/lambda/inventory_handler.py",
        handler: "handler",
        runtime: lambda.Runtime.PYTHON_3_12,
        memorySize: 256,
        timeout: cdk.Duration.seconds(10),
        environment: {
          POWERTOOLS_SERVICE_NAME: "inventory-service",
        },
        bundling: {
          assetExcludes: [
            "infra/cdk.out",
            "infra/node_modules",
            "infra/dist",
            ".venv",
            ".git",
            "__pycache__",
            "*.pyc",
          ],
        },
      },
    );

    inventoryHandler.addEventSource(
      new lambdaEventSources.SqsEventSource(this.inventoryQueue, {
        batchSize: 1,
      }),
    );

    this.bus.grantPutEventsTo(inventoryHandler);

    const paymentHandler = new pythonLambda.PythonFunction(
      this,
      "PaymentHandler",
      {
        entry: "../",
        index: "infra/lambda/payment_handler.py",
        handler: "handler",
        runtime: lambda.Runtime.PYTHON_3_12,
        memorySize: 256,
        timeout: cdk.Duration.seconds(10),
        environment: {
          POWERTOOLS_SERVICE_NAME: "payment-service",
        },
        bundling: {
          assetExcludes: [
            "infra/cdk.out",
            "infra/node_modules",
            "infra/dist",
            ".venv",
            ".git",
            "__pycache__",
            "*.pyc",
          ],
        },
      },
    );

    paymentHandler.addEventSource(
      new lambdaEventSources.SqsEventSource(this.paymentQueue, {
        batchSize: 1,
      }),
    );

    this.bus.grantPutEventsTo(paymentHandler);

    const notificationHandler = new pythonLambda.PythonFunction(
      this,
      "NotificationHandler",
      {
        entry: "../",
        index: "infra/lambda/notification_handler.py",
        handler: "handler",
        runtime: lambda.Runtime.PYTHON_3_12,
        memorySize: 256,
        timeout: cdk.Duration.seconds(10),
        environment: {
          POWERTOOLS_SERVICE_NAME: "notification-service",
        },
        bundling: {
          assetExcludes: [
            "infra/cdk.out",
            "infra/node_modules",
            "infra/dist",
            ".venv",
            ".git",
            "__pycache__",
            "*.pyc",
          ],
        },
      },
    );

    notificationHandler.addEventSource(
      new lambdaEventSources.SqsEventSource(this.notificationQueue, {
        batchSize: 1,
      }),
    );

    this.bus.grantPutEventsTo(notificationHandler);

    this.ordersTable = new dynamodb.Table(this, "OrdersTable", {
      tableName: "eventflow-orders",
      partitionKey: {
        name: "order_id",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.inventoryTable = new dynamodb.Table(this, "InventoryTable", {
      tableName: "eventflow-inventory",
      partitionKey: {
        name: "sku_id",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.paymentRecordsTable = new dynamodb.Table(this, "PaymentRecordsTable", {
      tableName: "eventflow-payment-records",
      partitionKey: {
        name: "payment_id",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "order_id",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.ordersTable.grantReadWriteData(orderHandler);
    this.inventoryTable.grantReadWriteData(inventoryHandler);
    this.paymentRecordsTable.grantReadWriteData(paymentHandler);

    orderHandler.addEnvironment(
      "ORDERS_TABLE_NAME",
      this.ordersTable.tableName,
    );
    inventoryHandler.addEnvironment(
      "INVENTORY_TABLE_NAME",
      this.inventoryTable.tableName,
    );
    paymentHandler.addEnvironment(
      "PAYMENT_RECORDS_TABLE_NAME",
      this.paymentRecordsTable.tableName,
    );

    const paymentSecret = new secretsmanager.Secret(
      this,
      "PaymentCredentials",
      {
        secretName: "eventflow/payment-credentials",
        description: "EventFlow payment service credentials",
        generateSecretString: {
          secretStringTemplate: JSON.stringify({
            api_key: "stub-api-key",
            endpoint: "https://stub-payment-processor.example.com",
          }),
          generateStringKey: "stub_secret",
        },
      },
    );

    paymentSecret.grantRead(paymentHandler);

    paymentHandler.addEnvironment(
      "PAYMENT_SECRET_ARN",
      paymentSecret.secretArn,
    );
  }
}
