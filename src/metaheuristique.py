# fichier : metaheuristique.py
# contient l'algorithme de recherche tabou et ses fonctions associées.

import time
import random
import numpy as np
from src.utils import calculer_cout # on garde calculer_cout depuis utils


# 1. fonction de calcul du delta (gain/perte)

def delta_cout_2opt(tournee, i, j, matrice_dist):
    """
    calcule ultra-rapidement la variation de coût (delta) d'un mouvement 2-opt.
    au lieu de recalculer toute la tournée, on calcule seulement l'impact des 2 routes
    supprimées et des 2 nouvelles routes créées. temps d'exécution : o(1).
    """
    n = len(tournee)
    
    # on récupère les vrais indices pour la matrice (en faisant - 1)
    # le modulo % n permet de revenir au début si on est à la fin de la liste
    ville_avant_i = tournee[i - 1] - 1
    ville_i = tournee[i] - 1
    ville_j = tournee[j] - 1
    ville_apres_j = tournee[(j + 1) % n] - 1 

    # coût des chemins qu'on va casser
    distance_supprimee = matrice_dist[ville_avant_i][ville_i] + matrice_dist[ville_j][ville_apres_j]
    # coût des chemins qu'on va créer
    distance_ajoutee = matrice_dist[ville_avant_i][ville_j] + matrice_dist[ville_i][ville_apres_j]
    
    return distance_ajoutee - distance_supprimee


# 2. fonctions de voisinage (génération et évaluation)

def evaluer_voisinage_spatial(tournee_courante, matrice_dist, pos_ville, voisins_spatiaux, liste_tabou, iteration, meilleur_cout, cout_courant, nb_voisins):
    """
    voisinage 2-opt optimisé : on ne teste les inversions qu'entre des villes géographiquement proches.
    c'est le voisinage le plus performant pour le problème du voyageur de commerce.
    """
    n = len(tournee_courante)
    meilleur_delta = float('inf')
    meilleur_mouvement = None
    
    for _ in range(nb_voisins):
        ville_1 = random.randint(1, n)
        idx_1 = pos_ville[ville_1]
        
        # on choisit la deuxième ville parmi les k voisins de la première
        ville_2 = random.choice(voisins_spatiaux[ville_1])
        idx_2 = pos_ville[ville_2]
        
        i, j = sorted([idx_1, idx_2])
        # on ignore les villes déjà collées
        if j - i <= 1 or (i == 0 and j == n - 1): continue
            
        delta = delta_cout_2opt(tournee_courante, i, j, matrice_dist)
        est_tabou = liste_tabou.get((ville_1, ville_2), 0) > iteration
        
        # critère d'aspiration : on ignore le tabou si le mouvement bat le record absolu
        if est_tabou and (cout_courant + delta < meilleur_cout): est_tabou = False
            
        if not est_tabou and delta < meilleur_delta:
            meilleur_delta = delta
            meilleur_mouvement = (i, j, ville_1, ville_2)
            
    return meilleur_delta, meilleur_mouvement


def evaluer_voisinage_aleatoire(tournee_courante, matrice_dist, liste_tabou, iteration, meilleur_cout, cout_courant, nb_voisins):
    """
    voisinage 2-opt classique : on tire 2 arêtes au hasard n'importe où dans la tournée pour les inverser.
    """
    n = len(tournee_courante)
    meilleur_delta = float('inf')
    meilleur_mouvement = None
    
    for _ in range(nb_voisins):
        i, j = sorted(random.sample(range(n), 2))
        if j - i <= 1 or (i == 0 and j == n - 1): continue
            
        ville_1, ville_2 = tournee_courante[i], tournee_courante[j]
        delta = delta_cout_2opt(tournee_courante, i, j, matrice_dist)
        est_tabou = liste_tabou.get((ville_1, ville_2), 0) > iteration
        
        if est_tabou and (cout_courant + delta < meilleur_cout): est_tabou = False
            
        if not est_tabou and delta < meilleur_delta:
            meilleur_delta = delta
            meilleur_mouvement = (i, j, ville_1, ville_2)
            
    return meilleur_delta, meilleur_mouvement


def evaluer_voisinage_swap(tournee_courante, matrice_dist, liste_tabou, iteration, meilleur_cout, cout_courant, nb_voisins):
    """
    voisinage par échange de nœuds (swap) : on permute simplement la position de deux villes.
    attention : modifie 4 arêtes, on doit donc recalculer le coût avec la méthode classique.
    """
    n = len(tournee_courante)
    meilleur_delta = float('inf')
    meilleur_mouvement = None
    
    for _ in range(nb_voisins):
        i, j = random.sample(range(n), 2)
        ville_1, ville_2 = tournee_courante[i], tournee_courante[j]
        
        # évaluation naïve du delta (car le swap casse 4 arêtes, la formule 2-opt ne marche pas ici)
        tournee_test = tournee_courante[:]
        tournee_test[i], tournee_test[j] = tournee_test[j], tournee_test[i]
        nouveau_cout = calculer_cout(tournee_test, matrice_dist)
        delta = nouveau_cout - cout_courant
        
        est_tabou = liste_tabou.get((ville_1, ville_2), 0) > iteration
        
        if est_tabou and (cout_courant + delta < meilleur_cout): est_tabou = False
            
        if not est_tabou and delta < meilleur_delta:
            meilleur_delta = delta
            meilleur_mouvement = (i, j, ville_1, ville_2)
            
    return meilleur_delta, meilleur_mouvement


# 3. algorithme principal : recherche tabou

def recherche_tabou(matrice_dist, tournee_initiale, cout_initial, type_voisinage='spatial', K_voisins=10, taille_tabou=25, max_stagnation=1000):
    """
    métaheuristique de recherche tabou unifiée.
    
    paramètres :
        - matrice_dist : matrice des distances entre les villes.
        - tournee_initiale : solution de départ (idéalement générée par ppv).
        - cout_initial : coût de la solution de départ.
        - type_voisinage : 'spatial', 'aleatoire', ou 'swap'.
        - K_voisins : nombre de voisins les plus proches à considérer (pour le type 'spatial').
        - taille_tabou : durée de vie d'un mouvement interdit dans la liste.
        - max_stagnation : critère d'arrêt (nombre d'itérations sans amélioration).
        
    retourne :
        - meilleure_tournee : la meilleure séquence trouvée.
        - meilleur_cout : le coût de cette séquence.
        - temps_execution : le temps mis par l'algorithme.
    """
    start_time = time.time()
    n = len(tournee_initiale)
    nb_voisins_a_tester = min(100, n) 
    
    tournee_courante, meilleure_tournee = tournee_initiale[:], tournee_initiale[:]
    cout_courant, meilleur_cout = cout_initial, cout_initial
    
    # --- pré-calculs spécifiques ---
    voisins_spatiaux = {}
    pos_ville = {}
    
    if type_voisinage == 'spatial':
        pos_ville = {ville: idx for idx, ville in enumerate(tournee_courante)}
        for v in range(1, n + 1):
            voisins_tries = np.argsort(matrice_dist[v - 1])
            voisins_spatiaux[v] = [x + 1 for x in voisins_tries[1:K_voisins+1]]
            
    liste_tabou = {} 
    iteration, iterations_sans_amelioration = 0, 0 
    
    # --- boucle principale ---
    while iterations_sans_amelioration < max_stagnation:
        
        # 1. évaluation du voisinage choisi
        if type_voisinage == 'spatial':
            meilleur_delta, meilleur_mouvement = evaluer_voisinage_spatial(
                tournee_courante, matrice_dist, pos_ville, voisins_spatiaux, liste_tabou, iteration, meilleur_cout, cout_courant, nb_voisins_a_tester)
        elif type_voisinage == 'aleatoire':
            meilleur_delta, meilleur_mouvement = evaluer_voisinage_aleatoire(
                tournee_courante, matrice_dist, liste_tabou, iteration, meilleur_cout, cout_courant, nb_voisins_a_tester)
        elif type_voisinage == 'swap':
            meilleur_delta, meilleur_mouvement = evaluer_voisinage_swap(
                tournee_courante, matrice_dist, liste_tabou, iteration, meilleur_cout, cout_courant, nb_voisins_a_tester)
        else:
            raise ValueError("erreur : type_voisinage doit être 'spatial', 'aleatoire' ou 'swap'")
            
        # 2. application du meilleur mouvement
        if meilleur_mouvement:
            i, j, v1, v2 = meilleur_mouvement
            
            # modification de la tournée selon le type de mouvement
            if type_voisinage in ['spatial', 'aleatoire']:
                tournee_courante[i:j+1] = tournee_courante[i:j+1][::-1] # 2-opt : on inverse le segment
                if type_voisinage == 'spatial':
                    # mise à jour rapide du dictionnaire des positions
                    for k in range(i, j+1): pos_ville[tournee_courante[k]] = k
            elif type_voisinage == 'swap':
                tournee_courante[i], tournee_courante[j] = tournee_courante[j], tournee_courante[i] # swap : on permute
                
            cout_courant += meilleur_delta
            
            # mise à jour de la liste tabou
            liste_tabou[(v1, v2)] = iteration + taille_tabou
            liste_tabou[(v2, v1)] = iteration + taille_tabou
            
            # 3. vérification du nouveau record et gestion de la stagnation
            if cout_courant < meilleur_cout:
                meilleur_cout = cout_courant
                meilleure_tournee = tournee_courante[:]
                iterations_sans_amelioration = 0 # on a trouvé mieux, on reset la stagnation !
            else:
                iterations_sans_amelioration += 1 
        else:
            iterations_sans_amelioration += 1
            
        iteration += 1
                
    return meilleure_tournee, meilleur_cout, time.time() - start_time