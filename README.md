# aws-application-deployment-template

CDK-based template for deploying a containerized application to AWS

## Perequisites

AWS CDK projects require some bootstrapping before synthesis or deployment.
Please review the [bootstapping documentation](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_bootstrap)
before development.

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

## Secrets

We use the [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
to store secrets for this project.  An AWS best practice is to create secrets
with a unique ID to prevent conflicts when multiple instances of this project
is deployed to the same AWS account.  Our naming convention is
`<cfn stack id>/<environment id>/<secret name>`.  An example is `MyTestStack/dev/MySecret`
