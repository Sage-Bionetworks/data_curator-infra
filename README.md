# aws-application-deployment-template

CDK-based template for deploying a containerized application to AWS


[Bootstrap](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) CDK in the AWS account.

Create an IAM Role in the target AWS account with sufficient permissions for deployment and a trust relationship including this repo', e.g., use a trust relationship policy like:

```
{
    "Version": "2008-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::<account-number>:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "ForAllValues:StringEquals": {
                    "token.actions.githubusercontent.com:sub": [
                        "repo:Sage-Bionetworks/<repo-name>:ref:refs/heads/main"
                    ],
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                }
            }
        }
    ]
}
```

Edit `.github/workflows/docker_deploy.yml`, setting the parameters listed under `env`, including the choice of 
container (and version) to deploy. Enter the ARN of the IAM Role mentioned above in the `role-to-assume` field.


Edit `cdk/docker_fargate/docker_fargate_stack.py` as desired to set parameters like number of containers, CPU, memory, and to set up auto-scaling.

Push the changes to your repo'. This will initiate the workflow and deploy the application.
