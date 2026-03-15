# fichier : heuristique.py
# contient la focntion de l'algorithme constructif du Plus Proche Voisin

import time
from src.utils import calculer_cout

def plus_proche_voisin(matrice_dist, ville_depart=1):
    """
    Algorithme glouton du Plus Proche Voisin (Nearest Neighbor).
    Part d'une ville de départ, visite la ville non visitée la plus proche, 
    et revient au point de départ à la fin.

    Retourne :
        - tournee : la liste des villes visitées dans l'ordre.
        - cout_total : la distance totale de cette tournée.
        - temps_execution : le temps pris par l'algorithme pour cette tournée.
    """
    start_time = time.time()
    
    n = len(matrice_dist)
    visite = [False] * n
    
    # L'index pour la machine (0 à n-1)
    index_actuel = ville_depart - 1
    visite[index_actuel] = True
    
    # La tournée pour l'affichage humain (1 à n)
    tournee = [ville_depart]
    
    # Boucle pour trouver les n-1 villes restantes
    for _ in range(1, n):
        distance_min = float('inf')
        prochain_index = -1
        
        distances = matrice_dist[index_actuel]
        
        for v in range(n):
            if not visite[v] and distances[v] < distance_min:
                distance_min = distances[v]
                prochain_index = v
                
        # On ajoute la vraie ville (index + 1) à notre tournée
        tournee.append(prochain_index + 1)
        visite[prochain_index] = True
        index_actuel = prochain_index
        
    # On calcule le coût 
    cout_total = calculer_cout(tournee, matrice_dist)
    
    end_time = time.time()
    temps_execution = end_time - start_time
    
    return tournee, cout_total, temps_execution