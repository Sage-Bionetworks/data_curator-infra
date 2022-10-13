# aws-application-deployment-template

CDK-based template for deploying a containerized application to AWS


[Bootstrap](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) CDK in the AWS account.  See: 

Put AWS credentials into repository secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
TODO: substitute [GitHub-AWS OAuth integration](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

Edit .github/workflows/docker_deploy.yml, setting the parameters listed under `env`, including the choice of container (and version) to deploy.

Push the changes to your repo'. This will initiate the workflow and deploy the application.
