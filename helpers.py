import os
import config

def get_required_env(name: str) -> str:
  value = os.getenv(name)
  if value is None or len(value) == 0:
    raise Exception(f'{name} is required.')
  return value

def get_cost_center() -> str:
  return get_required_env(config.COST_CENTER)
