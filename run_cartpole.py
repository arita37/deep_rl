import os
import gym
import time
import argparse
import numpy as np
import torch
from torch.utils.tensorboard import SummaryWriter

# Configurations
parser = argparse.ArgumentParser(description='RL algorithms with PyTorch in CartPole environment')
parser.add_argument('--algo', type=str, default='dqn', 
                    help='select an algorithm among dqn, ddqn, a2c')
parser.add_argument('--seed', type=int, default=0, 
                    help='seed for random number generators')
parser.add_argument('--training_eps', type=int, default=500, 
                    help='training episode number')
parser.add_argument('--eval_per_train', type=int, default=50, 
                    help='evaluation number per training')
parser.add_argument('--evaluation_eps', type=int, default=100,
                    help='evaluation episode number')
parser.add_argument('--max_step', type=int, default=500,
                    help='max episode step')
parser.add_argument('--threshold_return', type=int, default=495,
                    help='solved requirement for success in given environment')
args = parser.parse_args()

if args.algo == 'dqn':
    from agents.dqn import Agent
elif args.algo == 'ddqn': # Just replace the target of DQN with Double DQN
    from agents.dqn import Agent
elif args.algo == 'a2c':
    from agents.a2c import Agent

def main():
    """Main."""
    # Initialize environment
    env = gym.make('CartPole-v1')
    obs_dim = env.observation_space.shape[0]
    act_num = env.action_space.n
    print('State dimension:', obs_dim)
    print('Action number:', act_num)

    # Set a random seed
    env.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    # Create an agent
    agent = Agent(env, args, obs_dim, act_num)

    # Create a SummaryWriter object by TensorBoard
    dir_name = 'runs/' + 'CartPole-v1/' + args.algo + '/' + str(args.seed) + '_' + time.ctime()
    writer = SummaryWriter(log_dir=dir_name)

    start_time = time.time()

    train_num_steps = 0
    train_sum_returns = 0.
    train_num_episodes = 0

    # Runs a full experiment, spread over multiple training episodes
    for episode in range(1, args.training_eps+1):
        # Perform the training phase, during which the agent learns
        agent.eval_mode = False
        
        # Run one episode
        train_step_length, train_episode_return = agent.run(args.max_step)
        
        train_num_steps += train_step_length
        train_sum_returns += train_episode_return
        train_num_episodes += 1

        train_average_return = train_sum_returns / train_num_episodes if train_num_episodes > 0 else 0.0

        # Log experiment result for training episodes
        writer.add_scalar('Train/AverageReturns', train_average_return, episode)
        writer.add_scalar('Train/EpisodeReturns', train_episode_return, episode)

        # Perform the evaluation phase -- no learning
        if episode > 0 and episode % args.eval_per_train == 0:
            agent.eval_mode = True
            
            eval_sum_returns = 0.
            eval_num_episodes = 0

            for _ in range(args.evaluation_eps):
                # Run one episode
                eval_step_length, eval_episode_return = agent.run(args.max_step)

                eval_sum_returns += eval_episode_return
                eval_num_episodes += 1

                eval_average_return = eval_sum_returns / eval_num_episodes if eval_num_episodes > 0 else 0.0

                # Log experiment result for evaluation episodes
                writer.add_scalar('Eval/AverageReturns', eval_average_return, episode)
                writer.add_scalar('Eval/EpisodeReturns', eval_episode_return, episode)

            print('---------------------------------------')
            print('Episodes:', train_num_episodes)
            print('Steps:', train_num_steps)
            print('AverageReturn:', round(train_average_return, 2))
            print('EvalEpisodes:', eval_num_episodes)
            print('EvalAverageReturn:', round(eval_average_return, 2))
            print('OtherLogs:', agent.logger)
            print('Time:', int(time.time() - start_time))
            print('---------------------------------------')

            # Save a training model
            if eval_average_return >= args.threshold_return:
                if not os.path.exists('./tests/save_model'):
                    os.mkdir('./tests/save_model')
                
                ckpt_path = os.path.join('./tests/save_model/' + 'CartPole-v1/' + args.algo + '/' \
                                                                                + '_ep_' + str(train_num_episodes) \
                                                                                + '_rt_' + str(round(eval_average_return, 2)) \
                                                                                + '_t_' + str(int(time.time() - start_time)) + '.pt')
                
                if args.algo == 'dqn' or args.algo == 'ddqn':
                    torch.save(agent.qf.state_dict(), ckpt_path)
                else:
                    torch.save(agent.actor.state_dict(), ckpt_path)

if __name__ == "__main__":
    main()
