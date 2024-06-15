import numpy as np
from pyDecision.algorithm import fuzzy_ahp_method
  
saaty_scale = [
    [(1,1,1),(1,1,1)],          #1
    [(1,2,3),(1/3,1/2,1)],      #2
    [(2,3,4),(1/4,1/3,1/2)],    #3
    [(3,4,5),(1/5,1/4,1/3)],    #4
    [(4,5,6),(1/6,1/5,1/4)],    #5
    [(5,6,7),(1/7,1/6,1/5)],    #6
    [(6,7,8),(1/8,1/7,1/6)],    #7
    [(7,8,9),(1/9,1/8,1/7)],    #8
    [(9,9,9),(1/9,1/9,1/9)]     #9
]

def generate_pair(vf,vc):   #vf: valor fila, vc: valor columna
    v_max = max(vf,vc)
    v_min = min(vf,vc)
    v_grade = np.round((v_max*100)/(v_min*100),0)
    if v_grade > 9: v_grade = 9

    #fts = fuzzy triangle scale
    for grade in saaty_scale:
      if v_grade == grade[0][1]:
          if v_max == vf: return grade[0]
          else: return grade[1]

def generate_dataset(puntajes):
  n = len(puntajes)

  #matriz inicial de (1,1,1)
  dataset = list([[(1,1,1)] * n for _ in range(n)])

  #rellenar matriz
  for i in range(n):
      for j in range(n):
              dataset[i][j] = generate_pair(puntajes[i],puntajes[j])

  return dataset

def generate_results(puntajes):
  dataset = generate_dataset(puntajes) #matriz pairwise 
  fuzzy_weights, defuzzified_weights, normalized_weights, rc = fuzzy_ahp_method(dataset)

  return [normalized_weights,rc]