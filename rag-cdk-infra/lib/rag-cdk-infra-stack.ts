import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as apigateway from "aws-cdk-lib/aws-apigateway";
// import * as sqs from 'aws-cdk-lib/aws-sqs';

import { AttributeType, BillingMode, Table } from "aws-cdk-lib/aws-dynamodb";
import {
  DockerImageFunction,
  DockerImageCode,
  FunctionUrlAuthType,
  Architecture,
} from "aws-cdk-lib/aws-lambda";
import { ManagedPolicy } from "aws-cdk-lib/aws-iam";


export class RagCdkInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // The code that defines your stack goes here

    // example resource
    // const queue = new sqs.Queue(this, 'RagCdkInfraQueue', {
    //   visibilityTimeout: cdk.Duration.seconds(300)
    // });

    // Create a DynamoDB table to store the query data and results.
    const ragQueryTable = new Table(this, "RagQueryTable", {
      partitionKey: { name: "query_id", type: AttributeType.STRING },
      billingMode: BillingMode.PAY_PER_REQUEST,
    });


    // Function to handle the API requests. Uses same base image, but different handler.
    const apiImageCode = cdk.aws_lambda.DockerImageCode.fromImageAsset("../image", {
      cmd: ["app_api_handler.handler"],
      platform: cdk.aws_ecr_assets.Platform.LINUX_AMD64,
      file: "Dockerfile",
      buildArgs: {
        provenance: "false",
        sbom: "false",
      },
    });
    const apiFunction = new cdk.aws_lambda.DockerImageFunction(this, "ApiFunc", {
      code: apiImageCode,
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
      architecture: Architecture.X86_64,
      environment: {
        DOCKER_DEFAULT_PLATFORM: "linux/amd64",
        TABLE_NAME: ragQueryTable.tableName,
      },
    });

    // Grant permissions for all resources to work together.
    ragQueryTable.grantReadWriteData(apiFunction);
    apiFunction.role?.addManagedPolicy(
      ManagedPolicy.fromAwsManagedPolicyName("AmazonBedrockFullAccess")
    );

    // Create API Gateway
    const api = new apigateway.RestApi(this, "RagApiGateway", {
      restApiName: "RAG API Gateway",
      deployOptions: {
        stageName: "prod", // Set deployment stage
      },
    });

    // Create a /submit_query resource endpoint
    const submit_queryResource = api.root.addResource("submit_query");

    // Create a /get_query resource endpoint
    const get_queryResource = api.root.addResource("get_query");

    // Attach Lambda function to API Gateway (POST method)
    submit_queryResource.addMethod("POST", new apigateway.LambdaIntegration(apiFunction), {
      apiKeyRequired: true, // Require API Key for authentication
    });

    // Attach Lambda function to API Gateway (GET method)
    get_queryResource.addMethod("GET", new apigateway.LambdaIntegration(apiFunction), {
      apiKeyRequired: true, // Require API Key for authentication
    })

    // Create an API Key for security
    const apiKey = new apigateway.ApiKey(this, "RagApiKey", {
      apiKeyName: "RagApiAccessKey",
      enabled: true, 
    });

    // Create a Usage Plan and attach API Key
    const usagePlan = api.addUsagePlan("RagUsagePlan", {
      name: "DefaultUsagePlan",
      apiStages: [{ api, stage: api.deploymentStage }],
    });
    usagePlan.addApiKey(apiKey);

    // Output the API Gateway URL
    new cdk.CfnOutput(this, "ApiGatewayUrl", {
      value: api.url,
    });
  }
}
