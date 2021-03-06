"""

This script collects policies with which to make some batch RL data. 

Medium/Optimal are per BearQL: https://arxiv.org/pdf/1906.00949.pdf

Performance targets:

Environment     Medium    Optimal      Super-optimal
HalfCheetah:    4000      12000        16700
Walker:         500       3000         6600
Hopper:         1000      2500         4200
Ant:            750       5000         6900

E.g.:
PYTHONPATH=./ python experiments/batch_rl/collect_policies.py --parent_folder {YOUR FOLDER}/batchrl/ --env Ant-v3 --num_envs 4
PYTHONPATH=./ python experiments/batch_rl/collect_policies.py --parent_folder {YOUR FOLDER}/batchrl/ --env HalfCheetah-v3 --num_envs 4
...

"""

from mrl.import_all import *
from mrl.configs.make_continuous_agents import *
from experiments.mega.make_env import make_env

import time
import os
import gym
import numpy as np
import torch

CHECKPOINT_DICT = {
  'HalfCheetah-v3': [4000, 12000],
  'Walker2d-v3': [500, 3000],
  'Hopper-v3': [1000, 2500],
  'Ant-v3': [750, 5000]
}

config = spinning_up_sac_config()
config.batch_size = 500
config.optimize_every = 2
config.save_replay_buf = True

def main(args):
  if args.alg.lower() == 'ddpg':
    make = make_ddpg_agent
    conf = spinning_up_ddpg_config
  elif args.alg.lower() == 'td3':
    make = make_td3_agent
    conf = spinning_up_td3_config
  elif args.alg.lower() == 'sac':
    make = make_sac_agent
    conf = spinning_up_sac_config

  config = make(base_config=conf, args=args, agent_name_attrs=['env', 'alg', 'seed', 'tb'])

  # use the old replay buffer, since it adds experience to buffer immediately and don't need HER
  del config.module_replay
  config.module_replay = OldReplayBuffer()

  # dont use state normalizer on basic mujoco task
  del config.module_state_normalizer

  torch.set_num_threads(min(4, args.num_envs))
  torch.set_num_interop_threads(min(4, args.num_envs))

  agent  = mrl.config_to_agent(config)
  
  res = agent.eval(num_episodes=20).rewards
  agent.logger.log_color('Initial test reward ({} eps): {:.2f}'.format(len(res), np.mean(res)))

  max_perf = 0

  for epoch in range(int(args.max_steps // args.epoch_len)):
    t = time.time()
    agent.train(num_steps=args.epoch_len)

    # EVALUATE
    res = agent.eval(num_episodes=20).rewards
    agent.logger.log_color('Test reward ({} eps): {:.2f}'.format(len(res), np.mean(res)))
    res = int(np.mean(res))
    agent.logger.log_color('Epoch time:', '{:.2f}'.format(time.time() - t), color='yellow')

    if CHECKPOINT_DICT[args.env] and (res > CHECKPOINT_DICT[args.env][0]):
      CHECKPOINT_DICT[args.env] = CHECKPOINT_DICT[args.env][1:]
      print("**********")
      print("Saving agent at epoch {}".format(epoch))
      agent.save(f'performance_{res}')
      print("Reloading agent to confirm it works...")
      agent.load(f'performance_{res}')
      print("**********")
      max_perf = max(max_perf, res)
    elif res > max_perf:
      print("**********")
      print("NEW MAX PERFORMANCE!")
      print("Saving agent at epoch {}".format(epoch))
      agent.save('performance_MAX')
      print("Reloading agent to confirm it works...")
      agent.load('performance_MAX')
      print("**********")
      max_perf = max(max_perf, res)

# 3. Declare args for modules (also parent_folder is required!)
if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description="Train DDPG", formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, max_help_position=100, width=120))
  parser.add_argument('--parent_folder', default='/tmp/batchrl', type=str, help='where to save progress')
  parser.add_argument('--prefix', type=str, default='batchrl', help='Prefix for agent name (subfolder where it is saved)')
  parser.add_argument('--env', default="HalfCheetah-v3", type=str, help="gym environment")
  parser.add_argument('--max_steps', default=2500000, type=int, help="maximum number of training steps")
  parser.add_argument('--alg', default='sac', type=str, help='algorithm to use (DDPG or TD3)')
  parser.add_argument('--layers', nargs='+', default=(512, 512, 512), type=int, help='hidden layers for actor/critic')
  parser.add_argument('--tb', default='2', type=str, help='a tag for the agent name / tensorboard')
  parser.add_argument('--epoch_len', default=5000, type=int, help='number of steps between evals')
  parser.add_argument('--num_envs', default=None, type=int, help='number of envs (defaults to procs - 1)')

  parser = add_config_args(parser, config)
  args = parser.parse_args()

  import subprocess, sys
  args.launch_command = sys.argv[0] + ' ' + subprocess.list2cmdline(sys.argv[1:])

  main(args)
