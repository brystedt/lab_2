import sys
import gym
import pylab
import random
import numpy as np
from collections import deque
from keras.layers import Dense
from keras.optimizers import Adam
from keras.models import Sequential
import pandas as pd
import os

EPISODES = 1000 #Maximum number of episodes

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return np.concatenate((ret[n - 1:], np.full(max(0,len(a) - ret[n - 1:].shape[0]), np.nan)), axis = None) / n

#DQN Agent for the Cartpole
#Q function approximation with NN, experience replay, and target network
class DQNAgent:
    #Constructor for the agent (invoked when DQN is first called in main)
    def __init__(self,
                 state_size,
                 action_size,
                 random = False,
                 discount_factor = 0.95,
                 learning_rate = 0.005,
                 memory_size = 1000,
                 target_update_frequency = 1,
                 number_of_layers = 1,
                 number_of_nodes = 32):
        self.random = random
        self.check_solve = False	#If True, stop if you satisfy solution confition
        self.render = False        #If you want to see Cartpole learning, then change to True

        #Get size of state and action
        self.state_size = state_size
        self.action_size = action_size

       # Modify here

        #Set hyper parameters for the DQN. Do not adjust those labeled as Fixed.
        self.discount_factor = discount_factor
        self.learning_rate = learning_rate
        self.epsilon = 0.02 #Fixed
        self.batch_size = 32 #Fixed
        self.memory_size = memory_size
        self.train_start = 1000 #Fixed
        self.target_update_frequency = target_update_frequency
        self.number_of_layers = number_of_layers
        self.number_of_nodes = number_of_nodes

        #Number of test states for Q value plots
        self.test_state_no = 10000

        #Create memory buffer using deque
        self.memory = deque(maxlen=self.memory_size)

        #Create main network and target network (using build_model defined below)
        self.model = self.build_model()
        self.target_model = self.build_model()

        #Initialize target network
        self.update_target_model()

    #Approximate Q function using Neural Network
    #State is the input and the Q Values are the output.
###############################################################################
###############################################################################
        #Edit the Neural Network model here
        #Tip: Consult https://keras.io/getting-started/sequential-model-guide/
    def build_model(self):
        model = Sequential()
        for i in range(self.number_of_layers):
            model.add(Dense(self.number_of_nodes, input_dim=self.state_size, activation='relu',
                            kernel_initializer='he_uniform'))
        model.add(Dense(self.action_size, activation='linear',
                        kernel_initializer='he_uniform'))
        model.summary()
        model.compile(loss='mse', optimizer=Adam(lr=self.learning_rate))
        return model
###############################################################################
###############################################################################

    #After some time interval update the target model to be same with model
    def update_target_model(self):
        self.target_model.set_weights(self.model.get_weights())

    #Get action from model using epsilon-greedy policy
    def get_action(self, state):
###############################################################################
###############################################################################
        #Insert your e-greedy policy code here
        #Tip 1: Use the random package to generate a random action.
        #Tip 2: Use keras.model.predict() to compute Q-values from the state.
        if self.random:
            action = random.randrange(self.action_size)
        else:
            if np.random.rand() < self.epsilon:
                action = np.random.choice(self.action_size)
            else:
                q = self.target_model.predict(state)
                action = np.argmax(q[0])
        return action

###############################################################################
###############################################################################
    #Save sample <s,a,r,s'> to the replay memory
    def append_sample(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) #Add sample to the end of the list

    #Sample <s,a,r,s'> from replay memory
    def train_model(self):
        if len(self.memory) < self.train_start: #Do not train if not enough memory
            return
        batch_size = min(self.batch_size, len(self.memory)) #Train on at most as many samples as you have in memory
        mini_batch = random.sample(self.memory, batch_size) #Uniformly sample the memory buffer
        #Preallocate network and target network input matrices.
        update_input = np.zeros((batch_size, self.state_size)) #batch_size by state_size two-dimensional array (not matrix!)
        update_target = np.zeros((batch_size, self.state_size)) #Same as above, but used for the target network
        action, reward, done = [], [], [] #Empty arrays that will grow dynamically

        for i in range(self.batch_size):
            update_input[i] = mini_batch[i][0] #Allocate s(i) to the network input array from iteration i in the batch
            action.append(mini_batch[i][1]) #Store a(i)
            reward.append(mini_batch[i][2]) #Store r(i)
            update_target[i] = mini_batch[i][3] #Allocate s'(i) for the target network array from iteration i in the batch
            done.append(mini_batch[i][4])  #Store done(i)

        target = self.model.predict(update_input) #Generate target values for training the inner loop network using the network model
        target_val = self.target_model.predict(update_target) #Generate the target values for training the outer loop target network

        #Q Learning: get maximum Q value at s' from target network
###############################################################################
###############################################################################
        #Insert your Q-learning code here
        #Tip 1: Observe that the Q-values are stored in the variable target
        #Tip 2: What is the Q-value of the action taken at the last state of the episode?
        if self.random:
            for i in range(self.batch_size): #For every batch
               target[i][action[i]] = random.randint(0,1)
        else:
            for i in range(self.batch_size):
                target[i][action[i]] = reward[i]
                if not done[i]:
                    target[i][action[i]] += self.discount_factor * np.max(target_val[i])

###############################################################################
###############################################################################

        #Train the inner loop network
        self.model.fit(update_input, target, batch_size=self.batch_size,
                       epochs=1, verbose=0)
        return
    #Plots the score per episode as well as the maximum q value per episode, averaged over precollected states.
    def plot_data(self, episodes, scores, max_q_mean, title = ""):
        pylab.figure(0)
        pylab.plot(episodes, max_q_mean, label = title)
        pylab.xlabel("Episodes")
        pylab.ylabel("Average Q Value")
        pylab.legend()
        pylab.savefig("qvalues" + title + ".png")
        pylab.figure(1)
        pylab.plot(episodes, scores, 'b')
        pylab.plot(episodes, moving_average(scores, 20), 'r', label = 'moving_average')
        pylab.xlabel("Episodes")
        pylab.ylabel("Score")
        pylab.legend()
        pylab.savefig("scores_epsilon-greedy_" + title + ".png")
        pylab.close(1)
###############################################################################
###############################################################################

def sign(d):
    result = ''
    for key, value in d.items():
        result = result + key + '_' + str(value) + '_'
    return result

if __name__ == "__main__":
    is_random = False
    #For CartPole-v0, maximum episode length is 200
    env = gym.make('CartPole-v0') #Generate Cartpole-v0 environment object from the gym library
    #Get state and action sizes from the environment
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n
    # param_name = 'number_of_nodes'
    # param_values = [2**i for i in range(3, 8)]
    # param_name = 'number_of_layers'
    # param_values = [i for i in range(1,4)]
    # param_name = 'discount_factor'
    # param_values = [0.8,0.9,0.95,0.98,0.99]
    # param_name = 'learning_rate'
    # param_values = [0.05,0.01,0.005,0.001,0.0005]
    param_name = 'target_update_frequency'
    param_values = [1,2,4,8]
    params = [{param_name: i} for i in param_values]
    result_mean = []
    result_std = []
    for param_dict in params:
    # for number_of_layers in [1,2,3]:
        #Create agent, see the DQNAgent __init__ method for details
        agent = DQNAgent(state_size,
                         action_size,
                         random = is_random,
                         memory_size=3000,
                         **param_dict
                         )

        #Collect test states for plotting Q values using uniform random policy
        test_states = np.zeros((agent.test_state_no, state_size))
        max_q = np.zeros((EPISODES, agent.test_state_no))
        max_q_mean = np.zeros((EPISODES,1))

        done = True
        for i in range(agent.test_state_no):
            if done:
                done = False
                state = env.reset()
                state = np.reshape(state, [1, state_size])
                test_states[i] = state
            else:
                action = random.randrange(action_size)
                next_state, reward, done, info = env.step(action)
                next_state = np.reshape(next_state, [1, state_size])
                test_states[i] = state
                state = next_state

        scores, episodes = [], [] #Create dynamically growing score and episode counters
        for e in range(EPISODES):
            done = False
            score = 0
            state = env.reset() #Initialize/reset the environment
            state = np.reshape(state, [1, state_size]) #Reshape state so that to a 1 by state_size two-dimensional array ie. [x_1,x_2] to [[x_1,x_2]]
            #Compute Q values for plotting
            tmp = agent.model.predict(test_states)
            max_q[e][:] = np.max(tmp, axis=1)
            max_q_mean[e] = np.mean(max_q[e][:])

            while not done:
                if agent.render:
                    env.render() #Show cartpole animation

                #Get action for the current state and go one step in environment
                action = agent.get_action(state)
                next_state, reward, done, info = env.step(action)
                next_state = np.reshape(next_state, [1, state_size]) #Reshape next_state similarly to state

                #Save sample <s, a, r, s'> to the replay memory
                agent.append_sample(state, action, reward, next_state, done)
                #Training step
                agent.train_model()
                score += reward #Store episodic reward
                state = next_state #Propagate state

                if done:
                    #At the end of very episode, update the target network
                    if e % agent.target_update_frequency == 0:
                        agent.update_target_model()
                    #Plot the play time for every episode
                    scores.append(score)
                    episodes.append(e)

                    print("episode:", e, "  score:", score," q_value:", max_q_mean[e],"  memory length:",
                          len(agent.memory))

                    # if the mean of scores of last 100 episodes is bigger than 195
                    # stop training
                    if agent.check_solve:
                        if np.mean(scores[-min(100, len(scores)):]) >= 195:
                            print("solved after", e-100, "episodes")
                            agent.plot_data(episodes,scores,max_q_mean[:e+1])
                            sys.exit()
        agent.plot_data(episodes,scores,max_q_mean,sign(param_dict))
        result_mean.append(np.mean(scores[-100:]))
        result_std.append(np.std(scores[-100:]))
    pd.DataFrame({param_name: param_values,
                  'mean': result_mean,
                  'std': result_std}).to_latex('result' + param_name + '.ltx.txt')
    pd.DataFrame({param_name: param_values,
                  'mean'    : result_mean,
                  'std'     : result_std}).to_csv('result' + param_name + '.csv')