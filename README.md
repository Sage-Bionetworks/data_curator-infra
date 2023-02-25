# data-curator_infra

CDK project for deploying the infrastructure for a containerized
application to AWS

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
$ pip install -r requirements.txt -r requirements-dev.txt
```

Install the cdk app

```
sudo npm install -g aws-cdk
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


## DNS and Certificates

Sage IT manages the creation of DNS records and TLS certificates in [org-formation](https://github.com/Sage-Bionetworks-IT/organizations-infra/tree/master/org-formation).
The DNS records are managed centrally in the SageIT account, and corresponding
wildcard TLS certificates are created in any application accounts that will
deploy applications with custom (non-AWS) domains.

When deploying a new application (or an existing application to a new account,
e.g. the first deploy to "prod"), first check that a certificate for the
desired domain has been created in the account the application will be deployed
to (e.g. [here for app.sagebionetworks.org](https://github.com/Sage-Bionetworks-IT/organizations-infra/blob/master/org-formation/100-shared-dns/_tasks.yaml#L24-L27)).
If a certificate is needed in a new account, make a request to the IT team
because there is a manual validation step that must be performed by an
administrator. Set the value of `ACM_CERT_ARN` context variable to the ARN of
the certificate in the target account. If the AWS ARN for an existing
certificate is not known, it can be requested from Sage IT.

Finally, a DNS CNAME must be created in org-formation after the initial
deployment of the application to make the application available at the desired
URL. The CDK application exports the DNS name of the Application Load Balancer
to be consumed in org-formation. [An example PR setting up a CNAME](https://github.com/Sage-Bionetworks-IT/organizations-infra/pull/739).
