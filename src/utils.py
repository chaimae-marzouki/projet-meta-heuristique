# fichier : utils.py
# Contient les fonctions de lecture des fichiers TSPLIB, calcul des distances et des coûts


import math
import numpy as np


def load_tsp(filepath):
    """
    Lit un fichier .tsp et extrait les coordonnées des villes.
    Retourne un dictionnaire {id_ville: (x, y)} et la règle de calcul de distance.
    """
    coords = {}
    edge_weight_type = "EUC_2D" # Valeur par défaut
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    reading_nodes = False
    for line in lines:
        line = line.strip()
        if line.startswith("EDGE_WEIGHT_TYPE"):
            edge_weight_type = line.split(":")[1].strip()
        elif line.startswith("NODE_COORD_SECTION"):
            reading_nodes = True
            continue
        elif line == "EOF" or line == "":
            break
            
        if reading_nodes:
            parts = line.split()
            if len(parts) >= 3:
                node_id = int(parts[0]) - 1 # On indexe à partir de 0 pour Python
                x = float(parts[1])
                y = float(parts[2])
                coords[node_id] = (x, y)
                
    return coords, edge_weight_type

def create_distance_matrix(coords, weight_type):
    """
    Calcule la distance entre chaque paire de villes et la stocke dans une matrice.
    """
    n = len(coords)
    matrix = np.zeros((n, n), dtype=int) 
    
    for i in range(n):
        for j in range(n):
            if i != j:
                x1, y1 = coords[i]
                x2, y2 = coords[j]
                
                # Distance euclidienne
                distance_brute = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                
                # Arrondi selon la norme TSPLIB
                if weight_type == "EUC_2D":
                    matrix[i][j] = round(distance_brute)
                elif weight_type == "CEIL_2D":
                    matrix[i][j] = math.ceil(distance_brute)
                    
    return matrix

def calculer_cout(tournee, matrice_dist):
    """
    Calcule le coût total d'une tournée.
    Gère automatiquement la conversion des indices et le retour au départ.
    """
    cout = 0
    n_villes = len(tournee)
    
    # 1. Calcul du chemin normal (de la ville i à la ville i+1)
    for i in range(n_villes - 1):
        # On fait -1 car Python compte à partir de 0 dans la matrice
        ville_actuelle = tournee[i] - 1
        ville_suivante = tournee[i+1] - 1
        cout += matrice_dist[ville_actuelle][ville_suivante]
        
    # 2. Ajout automatique du retour à la maison (dernière ville -> première ville)
    derniere_ville = tournee[-1] - 1
    premiere_ville = tournee[0] - 1
    cout += matrice_dist[derniere_ville][premiere_ville]
    
    return cout

def verifier_tournee(tournee, n_villes):
    """
    Vérifie si la tournée est valide :
    - Contient exactement n villes.
    - Chaque ville est visitée exactement une fois (aucun doublon).
    - Les villes sont numérotées de 1 à n.
    """
    # 1. La tournée doit faire exactement la taille de n_villes
    if len(tournee) != n_villes:
        return False
        
    # 2. Il ne doit y avoir aucun doublon (chaque ville est unique)
    if len(set(tournee)) != n_villes:
        return False
        
    # 3. Les numéros des villes doivent aller de 1 à n_villes
    if min(tournee) != 1 or max(tournee) != n_villes:
        return False
        
    return True

