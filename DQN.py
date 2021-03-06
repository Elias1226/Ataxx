# -*- coding: utf-8 -*-
"""
Created on Sat Mar 18 10:01:09 2017

@author: Elias
"""

import tensorflow as tf 
import numpy as np 
import random
from collections import deque 

##parameters
# Hyper Parameters:
FRAME_PER_ACTION = 1
GAMMA = 0.8 # decay rate of past observations
OBSERVE = 1000. # timesteps to observe before training
EXPLORE = 200000. # frames over which to anneal epsilon
FINAL_EPSILON = 0#0.001 # final value of epsilon
INITIAL_EPSILON = 0#0.01 # starting value of epsilon
REPLAY_MEMORY = 50000 # number of previous transitions to remember
BATCH_SIZE = 500 # size of minibatch
UPDATE_TIME = 100



##
class BrainDQN0:
    def __init__(self,actions):
        # init replay memory
        self.Recurrent_Time_0=0
        self.replayMemory = deque()
        # init some parameters
        self.timeStep = 0
        self.epsilon = INITIAL_EPSILON
        self.actions = actions
        # init Q network
        self.stateInput,self.QValue,self.W_conv1,self.b_conv1,self.W_conv2,self.b_conv2,self.W_fc1,self.b_fc1,self.W_fc2,self.b_fc2 = self.createQNetwork()
        # init Target Q Network
        self.stateInputT,self.QValueT,self.W_conv1T,self.b_conv1T,self.W_conv2T,self.b_conv2T,self.W_fc1T,self.b_fc1T,self.W_fc2T,self.b_fc2T = self.createQNetwork()
        self.copyTargetQNetworkOperation = [self.W_conv1T.assign(self.W_conv1),self.b_conv1T.assign(self.b_conv1),self.W_conv2T.assign(self.W_conv2),self.b_conv2T.assign(self.b_conv2),self.W_fc1T.assign(self.W_fc1),self.b_fc1T.assign(self.b_fc1),self.W_fc2T.assign(self.W_fc2),self.b_fc2T.assign(self.b_fc2)]
        self.createTrainingMethod()
        # saving and loading networks
        self.saver = tf.train.Saver()
        self.session = tf.InteractiveSession()
        self.session.run(tf.initialize_all_variables())
        checkpoint = tf.train.get_checkpoint_state("saved_networks0")
        if checkpoint and checkpoint.model_checkpoint_path:
            self.saver.restore(self.session, checkpoint.model_checkpoint_path)
            print ("Successfully loaded:", checkpoint.model_checkpoint_path)
        else:
            print ("Could not find old network weights")

    def createQNetwork(self):
        # network weights
        W_conv1 = self.weight_variable([4,4,1,32])
        b_conv1 = self.bias_variable([32])

        W_conv2 = self.weight_variable([3,3,32,64])
        b_conv2 = self.bias_variable([64])

        W_fc1 = self.weight_variable([64,256])
        b_fc1 = self.bias_variable([256])

        W_fc2 = self.weight_variable([256,self.actions])
        b_fc2 = self.bias_variable([self.actions])

        # input layer

        stateInput = tf.placeholder("float",[None,7,7,1])

        # hidden layers
        h_conv1 = tf.nn.tanh(self.conv2d(stateInput,W_conv1,1) + b_conv1)
  
        h_conv2 = tf.nn.tanh(self.conv2d(h_conv1,W_conv2,1) + b_conv2)
        h_pool2 = self.max_pool_2x2(h_conv2)
              
        h_conv2_flat = tf.reshape(h_pool2,[-1,64])
        h_fc1 = tf.nn.tanh(tf.matmul(h_conv2_flat,W_fc1) + b_fc1)

        # Q Value layer
        QValue = tf.matmul(h_fc1,W_fc2) + b_fc2

        return stateInput,QValue,W_conv1,b_conv1,W_conv2,b_conv2,W_fc1,b_fc1,W_fc2,b_fc2

    def copyTargetQNetwork(self):
        self.session.run(self.copyTargetQNetworkOperation)

    def createTrainingMethod(self):
        self.actionInput = tf.placeholder("float",[None,self.actions])
        self.yInput = tf.placeholder("float", [None]) 
        Q_Action = tf.reduce_sum(tf.multiply(self.QValue, self.actionInput), reduction_indices = 1)
        self.cost = tf.reduce_mean(tf.square(self.yInput - Q_Action))
        self.trainStep = tf.train.AdamOptimizer(1e-6).minimize(self.cost)
        

    def trainQNetwork(self):

		
        # Step 1: obtain random minibatch from replay memory
        minibatch = random.sample(self.replayMemory,BATCH_SIZE)
        state_batch = [data[0] for data in minibatch]
        action_batch = [data[1] for data in minibatch]
        reward_batch = [data[2] for data in minibatch]
        nextState_batch = [data[3] for data in minibatch]

        # Step 2: calculate y 
        y_batch = []
        QValue_batch = self.QValueT.eval(feed_dict={self.stateInputT:nextState_batch})
        for i in range(0,BATCH_SIZE):
            terminal = minibatch[i][4]
            if terminal:
                y_batch.append(reward_batch[i])
            else:
                y_batch.append(reward_batch[i] + GAMMA * np.max(QValue_batch[i]))

        self.trainStep.run(feed_dict={self.yInput : y_batch,self.actionInput : action_batch,self.stateInput : state_batch})
        print('Cost0:',self.cost.eval(feed_dict={self.yInput : y_batch,self.actionInput : action_batch,self.stateInput : state_batch}))
        # save network every 100000 iteration
        if self.timeStep % 10000 == 0:
            self.saver.save(self.session, 'C:/Users/peter/Desktop/Ataxx/saved_networks0/' + 'network' + '-dqn', global_step = self.timeStep)

        if self.timeStep % UPDATE_TIME == 0:
            self.copyTargetQNetwork()


    def setPerception(self,nextObservation,action,reward,terminal):
        #newState = np.append(nextObservation,self.currentState[:,:,1:],axis = 2)
        newState = nextObservation
        self.replayMemory.append((self.currentState,action,reward,newState,terminal))
        if len(self.replayMemory) > REPLAY_MEMORY:
            self.replayMemory.popleft()
        if self.timeStep > OBSERVE:
            # Train the network
            self.trainQNetwork()

        # print info
        state = ""

        if self.timeStep <= OBSERVE:
            state = "observe"
        elif self.timeStep > OBSERVE and self.timeStep <= OBSERVE + EXPLORE:
            state = "explore"
        else:
            state = "train"

        print ("TIMESTEP", self.timeStep, "/ STATE", state, \
        "/ EPSILON", self.epsilon)
        
        self.currentState = newState
        self.timeStep += 1

    def getQValue(self):
        QValue = self.QValue.eval(feed_dict= {self.stateInput:[self.currentState]})
#        action = np.zeros([self.actions,4],dtype='int64')
#        for i in range(1,self.actions):
#            action[i]=action[i-1].copy()
#            action[i,0]+=1
#            for j in range(4):
#                if action[i,j]==7 and j!=3:
#                    action[i,j]=0
#                    action[i,j+1]+=1
#            
#        action_index = 0
#        if random.random() <= self.epsilon:
#            action_index = random.randrange(self.actions)
#        else:
#            action_index = np.argmax(QValue)

        # change episilon
        if self.epsilon > FINAL_EPSILON and self.timeStep > OBSERVE:
            self.epsilon -= (INITIAL_EPSILON - FINAL_EPSILON)/EXPLORE

        return(QValue)

    def setInitState(self,observation):
        self.currentState = observation

    def weight_variable(self,shape):
        initial = tf.truncated_normal(shape, stddev = 0.1)
        return tf.Variable(initial)

    def bias_variable(self,shape):
        initial = tf.constant(0.1, shape = shape)
        return tf.Variable(initial)

    def conv2d(self,x, W, stride):
        return tf.nn.conv2d(x, W, strides = [1, stride, stride, 1], padding = "VALID")

    def max_pool_2x2(self,x):
        return tf.nn.max_pool(x, ksize = [1, 2, 2, 1], strides = [1, 1, 1, 1], padding = "VALID")

class BrainDQN1:
    def __init__(self,actions):
        # init replay memory
        self.replayMemory = deque()
        self.Recurrent_Time_1=0
        # init some parameters
        self.timeStep = 0
        self.epsilon = INITIAL_EPSILON
        self.actions = actions
        # init Q network
        self.stateInput,self.QValue,self.W_conv1,self.b_conv1,self.W_conv2,self.b_conv2,self.W_fc1,self.b_fc1,self.W_fc2,self.b_fc2 = self.createQNetwork()
        # init Target Q Network
        self.stateInputT,self.QValueT,self.W_conv1T,self.b_conv1T,self.W_conv2T,self.b_conv2T,self.W_fc1T,self.b_fc1T,self.W_fc2T,self.b_fc2T = self.createQNetwork()
        self.copyTargetQNetworkOperation = [self.W_conv1T.assign(self.W_conv1),self.b_conv1T.assign(self.b_conv1),self.W_conv2T.assign(self.W_conv2),self.b_conv2T.assign(self.b_conv2),self.W_fc1T.assign(self.W_fc1),self.b_fc1T.assign(self.b_fc1),self.W_fc2T.assign(self.W_fc2),self.b_fc2T.assign(self.b_fc2)]
        self.createTrainingMethod()
        # saving and loading networks
        self.saver = tf.train.Saver()
        self.session = tf.InteractiveSession()
        self.session.run(tf.initialize_all_variables())
        checkpoint = tf.train.get_checkpoint_state("saved_networks1")
        if checkpoint and checkpoint.model_checkpoint_path:
            self.saver.restore(self.session, checkpoint.model_checkpoint_path)
            print ("Successfully loaded:", checkpoint.model_checkpoint_path)
        else:
            print ("Could not find old network weights")

    def createQNetwork(self):
        # network weights
        W_conv1 = self.weight_variable([4,4,1,32])
        b_conv1 = self.bias_variable([32])

        W_conv2 = self.weight_variable([3,3,32,64])
        b_conv2 = self.bias_variable([64])

        W_fc1 = self.weight_variable([64,256])
        b_fc1 = self.bias_variable([256])

        W_fc2 = self.weight_variable([256,self.actions])
        b_fc2 = self.bias_variable([self.actions])

        # input layer

        stateInput = tf.placeholder("float",[None,7,7,1])

        # hidden layers
        h_conv1 = tf.nn.tanh(self.conv2d(stateInput,W_conv1,1) + b_conv1)
  
        h_conv2 = tf.nn.tanh(self.conv2d(h_conv1,W_conv2,1) + b_conv2)
        h_pool2 = self.max_pool_2x2(h_conv2)
              
        h_conv2_flat = tf.reshape(h_pool2,[-1,64])
        h_fc1 = tf.nn.tanh(tf.matmul(h_conv2_flat,W_fc1) + b_fc1)

        # Q Value layer
        QValue = tf.matmul(h_fc1,W_fc2) + b_fc2

        return stateInput,QValue,W_conv1,b_conv1,W_conv2,b_conv2,W_fc1,b_fc1,W_fc2,b_fc2

    def copyTargetQNetwork(self):
        self.session.run(self.copyTargetQNetworkOperation)

    def createTrainingMethod(self):
        self.actionInput = tf.placeholder("float",[None,self.actions])
        self.yInput = tf.placeholder("float", [None]) 
        Q_Action = tf.reduce_sum(tf.multiply(self.QValue, self.actionInput), reduction_indices = 1)
        self.cost = tf.reduce_mean(tf.square(self.yInput - Q_Action))
        self.trainStep = tf.train.AdamOptimizer(1e-6).minimize(self.cost)
        
    def trainQNetwork(self):

		
        # Step 1: obtain random minibatch from replay memory
        minibatch = random.sample(self.replayMemory,BATCH_SIZE)
        state_batch = [data[0] for data in minibatch]
        action_batch = [data[1] for data in minibatch]
        reward_batch = [data[2] for data in minibatch]
        nextState_batch = [data[3] for data in minibatch]

        # Step 2: calculate y 
        y_batch = []
        QValue_batch = self.QValueT.eval(feed_dict={self.stateInputT:nextState_batch})
        for i in range(0,BATCH_SIZE):
            terminal = minibatch[i][4]
            if terminal:
                y_batch.append(reward_batch[i])
            else:
                y_batch.append(reward_batch[i] + GAMMA * np.max(QValue_batch[i]))

        self.trainStep.run(feed_dict={self.yInput : y_batch,self.actionInput : action_batch,self.stateInput : state_batch})
        print('Cost1:',self.cost.eval(feed_dict={self.yInput : y_batch,self.actionInput : action_batch,self.stateInput : state_batch}))

        # save network every 100000 iteration
        if self.timeStep % 10000 == 0:
            self.saver.save(self.session, 'C:/Users/peter/Desktop/Ataxx/saved_networks1/' + 'network' + '-dqn', global_step = self.timeStep)

        if self.timeStep % UPDATE_TIME == 0:
            self.copyTargetQNetwork()


    def setPerception(self,nextObservation,action,reward,terminal):
        #newState = np.append(nextObservation,self.currentState[:,:,1:],axis = 2)
        newState = nextObservation
        self.replayMemory.append((self.currentState,action,reward,newState,terminal))
        if len(self.replayMemory) > REPLAY_MEMORY:
            self.replayMemory.popleft()
        if self.timeStep > OBSERVE:
            # Train the network
            self.trainQNetwork()
        # print info
        state = ""

        if self.timeStep <= OBSERVE:
            state = "observe"
        elif self.timeStep > OBSERVE and self.timeStep <= OBSERVE + EXPLORE:
            state = "explore"
        else:
            state = "train"
        print ("TIMESTEP", self.timeStep, "/ STATE", state, \
        "/ EPSILON", self.epsilon)
        
        self.currentState = newState
        self.timeStep += 1

    def getQValue(self):
        QValue = self.QValue.eval(feed_dict= {self.stateInput:[self.currentState]})
#        action = np.zeros([self.actions,4],dtype='int64')
#        for i in range(1,self.actions):
#            action[i]=action[i-1].copy()
#            action[i,0]+=1
#            for j in range(4):
#                if action[i,j]==7 and j!=3:
#                    action[i,j]=0
#                    action[i,j+1]+=1
#            
#        action_index = 0
#        if random.random() <= self.epsilon:
#            action_index = random.randrange(self.actions)
#        else:
#            action_index = np.argmax(QValue)

        # change episilon
        if self.epsilon > FINAL_EPSILON and self.timeStep > OBSERVE:
            self.epsilon -= (INITIAL_EPSILON - FINAL_EPSILON)/EXPLORE

        return(QValue)

    def setInitState(self,observation):
        self.currentState = observation

    def weight_variable(self,shape):
        initial = tf.truncated_normal(shape, stddev = 0.1)
        return tf.Variable(initial)

    def bias_variable(self,shape):
        initial = tf.constant(0.1, shape = shape)
        return tf.Variable(initial)

    def conv2d(self,x, W, stride):
        return tf.nn.conv2d(x, W, strides = [1, stride, stride, 1], padding = "VALID")

    def max_pool_2x2(self,x):
        return tf.nn.max_pool(x, ksize = [1, 2, 2, 1], strides = [1, 1, 1, 1], padding = "VALID")
		