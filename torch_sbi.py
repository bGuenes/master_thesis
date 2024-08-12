import numpy as np

#from sklearn.neural_network import MLPRegressor

from Chempy.parameter import ModelParameters

import sbi.utils as utils
from sbi.inference.base import infer
from sbi.analysis import pairplot

import torch
from torch.distributions.normal import Normal

from torch.distributions.uniform import Uniform

#import tensorflow as tf

import time as t
import pickle


# --------------------------- 

# ------ Load & prepare the data ------

# --- Load in training data ---
path_training = '../ChempyMulti/tutorial_data/TNG_Training_Data.npz'
training_data = np.load(path_training, mmap_mode='r')

elements = training_data['elements']
train_x = training_data['params']
train_y = training_data['abundances']


# ---  Load in the validation data ---
path_test = '../ChempyMulti/tutorial_data/TNG_Test_Data.npz'
val_data = np.load(path_test, mmap_mode='r')

val_x = val_data['params']
val_y = val_data['abundances']


# --- Clean the data ---
def clean_data(x, y):
    # Remove all zeros from the training data
    index = np.where((y == 0).all(axis=1))[0]
    x = np.delete(x, index, axis=0)
    y = np.delete(y, index, axis=0)

    # Remove all infinite values from the training data
    index = np.where(np.isfinite(y).all(axis=1))[0]
    x = x[index]
    y = y[index]

    return x, y


train_x, train_y = clean_data(train_x, train_y)
val_x, val_y     = clean_data(val_x, val_y)


# --- Normalize the data ---
x_mean, x_std = train_x.mean(axis=0), train_x.std(axis=0)
y_mean, y_std = train_y.mean(axis=0), train_y.std(axis=0)


def normalize_data(x, y, x_mean=x_mean, x_std=x_std, y_mean=y_mean, y_std=y_std):
    x = (x - x_mean) / x_std
    y = (y - y_mean) / y_std

    return x, y


train_x, train_y = normalize_data(train_x, train_y)
val_x, val_y     = normalize_data(val_x, val_y)


# add time squared as parameter
def add_time_squared(x):
    time_squared = np.array([x.T[-1]**2]).T
    if len(x.shape) == 1:
        return np.concatenate((x, time_squared))
    elif len(x.shape) == 2:
        return np.concatenate((x, time_squared), axis=1)


train_x = add_time_squared(train_x)
val_x = add_time_squared(val_x)


# -----------------------

# --- Define the neural network ---
"""print(".")
model = torch.nn.Sequential(
    torch.nn.Linear(train_x.shape[1], 100),
    torch.nn.Tanh(),
    torch.nn.Linear(100, 40),
    torch.nn.Tanh(),
    torch.nn.Linear(40, train_y.shape[1])
)"""

if torch.backends.mps.is_available():
    print("using mps")
    device = torch.device("mps")

else:
    print("using cpu")
    device = torch.device("cpu")


class Model_Torch(torch.nn.Module):
    def __init__(self):
        super(Model_Torch, self).__init__()
        self.l1 = torch.nn.Linear(train_x.shape[1], 100)
        self.l2 = torch.nn.Linear(100, 40)
        self.l3 = torch.nn.Linear(40, train_y.shape[1])

    def forward(self, x):
        x = torch.tanh(self.l1(x))
        x = torch.tanh(self.l2(x))
        x = self.l3(x)
        return x


model = Model_Torch()
model.to(device)

optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = torch.nn.MSELoss()


"""# --- Train the neural network ---
epochs = 15
batch_size = 64
for epoch in range(epochs):
    for i in range(0, train_x.shape[0], batch_size):
        optimizer.zero_grad()
        x_batch = torch.tensor(train_x[i:i+batch_size], dtype=torch.float32, device=device)
        y_batch = torch.tensor(train_y[i:i+batch_size], dtype=torch.float32, device=device)

        #print(".")
        y_pred = model(x_batch)
        #print(".")
        loss = loss_fn(y_pred, y_batch)
        loss.backward()
        optimizer.step()

    print(f'Epoch {epoch+1}/{epochs}, Loss: {loss.item()}')

torch.save(model.state_dict(), 'data/pytorch_state_dict.pt')
"""

# --- Load the Network ------------------------------------------------------------------------------------------------
model = Model_Torch()
model.load_state_dict(torch.load('data/pytorch_state_dict.pt'))
model.eval()

model.to(device)

x = np.load('data/tutorial_weights.npz')

w0 = x['w0']
w1 = x['w1']
b0 = x['b0']
b1 = x['b1']
in_mean = x['in_mean']
in_std = x['in_std']
out_mean = x['out_mean']
out_std = x['out_std']
activation = x['activation']
neurons = x['neurons']


def add_time_squared(x):
    time_squared = np.array([x.T[-1] ** 2]).T
    if len(x.shape) == 1:
        return np.concatenate((x, time_squared))
    elif len(x.shape) == 2:
        return np.concatenate((x, time_squared), axis=1)


def simulator_NN_torch(in_par):
    in_par = (in_par - in_mean) / in_std
    in_par = add_time_squared(in_par)

    in_par = torch.tensor(in_par, dtype=torch.float32).to(device)

    out = model(in_par)

    return out.detach().cpu().numpy() * out_std + out_mean

# ----- Set-up priors -----
a = ModelParameters()
priors = torch.tensor([[a.priors[opt][0], a.priors[opt][1]] for opt in a.to_optimize])

combined_priors = utils.MultipleIndependent(
    [Normal(p[0]*torch.ones(1), p[1]*torch.ones(1)) for p in priors] +
    [Uniform(torch.tensor([2.0]), torch.tensor([12.8]))],
    validate_args=False)

# ----- sbi setup -----
num_sim = 100000
method = 'SNPE' #SNPE or SNLE or SNRE

start = t.time()
posterior = infer(
    simulator_NN_torch,
    combined_priors,
    method=method,
    num_simulations=num_sim)

print(f'Time taken to train the posterior with {num_sim} samples: {round(t.time() - start, 4)}s')

# ----- Save the posterior -----
with open("data/posterior_SNPE_torch.pickle", "wb") as f:
    pickle.dump(posterior, f)
