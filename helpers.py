import aws_cdk
import config

def get_app_config(app: aws_cdk.App) -> dict:
  context = app.node.try_get_context('env')
  if context is None or context not in config.CONTEXT_ENVS:
    raise ValueError(
      "ERROR: CDK env context not provide or is invalid. "
      "Try passing in one of the available contexts: "
      + ', '.join(config.CONTEXT_ENVS))

  app_config = app.node.try_get_context(context)
  return context, app_config
