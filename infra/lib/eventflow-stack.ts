import * as cdk from "aws-cdk-lib";
import * as events from "aws-cdk-lib/aws-events";
import { Construct } from "constructs";

export class EventFlowStack extends cdk.Stack {
  public readonly bus: events.EventBus;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.bus = new events.EventBus(this, "EventFlowBus", {
      eventBusName: "eventflow-dev-bus",
    });

    this.bus.archive("EventFlowArchive", {
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
  }
}
