"""
First, follow install instructions here: https://github.com/rail-berkeley/offline_rl
(First commit requires clone and local install.)
"""

import gym
import offline_rl # Import required to register environments

DATASET_NAMES = [
  'halfcheetah-random-v0',
  'halfcheetah-medium-v0',
  'halfcheetah-expert-v0',
  #'halfcheetah-mixed-v0', # NO PERMISSION
  'halfcheetah-medium-expert-v0',
  'walker2d-random-v0',
  'walker2d-medium-v0',
  'walker2d-expert-v0',
  #'walker2d-mixed-v0', # NO PERMISSION
  'walker2d-medium-expert-v0',
  'hopper-random-v0',
  'hopper-medium-v0',
  'hopper-expert-v0',
  #'hopper-mixed-v0', # NO PERMISSION
  'hopper-medium-expert-v0'
]

if __name__ == '__main__':
  for env in DATASET_NAMES:
    e = gym.make(env)
    d = e.get_dataset()
    print(f'Got dataset for {env}! It has shape {d["observations"].shape}!')