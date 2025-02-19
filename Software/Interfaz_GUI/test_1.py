import numpy as np 

#Training_data
#from statistics import covariance
import numpy as np 
import matplotlib.pyplot as plt 
from sklearn.datasets import make_gaussian_quantiles 

#Create datasets from zero - For in example of clasification 

N = 1000

gaussian_quantiles = make_gaussian_quantiles(
    mean = None,
    cov = 0.1,
    n_samples = N,
    n_features = 2, 
    n_classes = 2,
    shuffle = True,
    random_state = None
)

x, y = gaussian_quantiles

print(x.shape)
print(y.shape)

plt.scatter(x[:, 0], x[:, 1], c=y, s=40, cmap=plt.cm.viridis) 
plt.show()

def sigmoid(X, derivate = False): # me return of derivative of fuction sigmoid
    if derivate:
        return np.exp(-x)/(np.exp(-x)+1) ** 2
    else:
        return 1/(1 + np.exp(-x))
    
def relu(x, derivative = False):
    if derivative:
        x [x <= x] = 0
        x [x > 0 ] = 1
        return x
    else:
        return np.maximum(0,x)

# Loss of Fuction 

def mse(y,y_hat, derivative = False):
    if derivative:
        return (y_hat - y)
    else:
        return np.mean((y_hat - y)) ** 2

# Structure of red

def initialize_parameters_deep(layers_dim: list): # Son parámetros cuando lo creamos, y argumentos cuando lo mandamos llamar
    parameters = { }
    L = len(layers_dim) # len = 4 [cantidad de elementos en la lista]: te dice cuantos elementos tiene el argumento, dir: me dice que métodos y atributos tiene una función en python 
    for l in range(0, L-1): # el range y su argumento es un iterador, o generador, que en este caso de num. entre el 0 y L-1
        parameters['W' + str(l + 1)] = (np.random.rand( # que genere una matriz de 2 * 4 de valores aleatorios
            layers_dim[l], layers_dim[l + 1]) * 2) - 1 # generación de los pesos de la primera capa
        
        parameters['b' + str(l + 1)] = (np.random.rand( # que genere una matriz de 1 * 4 de valores aleatorios
            1, layers_dim[l + 1]) * 2) - 1 # que los valores estén desde 0 a 1
        
    return parameters
layers_dims = [2,4,8,1]

params = initialize_parameters_deep(layers_dims)

print(params)
