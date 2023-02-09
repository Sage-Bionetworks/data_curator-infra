# aws-application-deployment-template

CDK-based template for deploying a containerized application to AWS

## Development

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.
An environment context is rquired, check [cdk.json](cdk.json) for available contexts.

```
$ cdk synth --context env=dev
```

## Testing

### Static Analysis
As a pre-deployment step we syntatically validate the CDK json, yaml and
python files with [pre-commit](https://pre-commit.com).

Please install pre-commit, once installed the file validations will
automatically run on every commit.  Alternatively you can manually
execute the validations by running `pre-commit run --all-files`.

### Python Tests
Tests are available in the tests folder. Execute the following to run tests:

```
python -m pytest tests/ -s -v
```

## Bootstrap AWS account

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
