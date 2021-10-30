from graphe import *
import math
import argparse
from os import walk

def charger_donnees(graphe, fichier):
    i = 1
    id_lst = list()
    f = open(fichier, 'r')
    lines = f.readlines()

    while lines[i] != "# connexions\n":
        s = lines[i].find(":")
        id_lst.append(int(lines[i][0 : s]))
        graphe.nom_station[int(lines[i][0 : s])] = lines[i][s+1:-1]
        i += 1
    graphe.ajouter_sommets(id_lst)

    i += 1 # to skip the index of "# connexions\n"

    for x in range(i, len(lines)):
        fst = lines[x].find("/")
        snd = lines[x].find("/", fst + 1)
        graphe.ajouter_arete( int(lines[x][ : fst]), int(lines[x][fst + 1 : snd]), fichier[:-4])

    f.close()

def numerotations(G):
    debut = dict()
    parent = dict()
    ancetre = dict()
    for v in G.sommets():
        debut[v] = 0
        parent[v] = None
        ancetre[v] = math.inf
    instant = 0
    def numerotation_rec(s):
        nonlocal instant
        instant += 1
        ancetre[s] = instant
        debut[s] = ancetre[s]
        for t in sorted(G.voisins(s)):
            if(debut[t[0]] != 0):
                if parent[s] != t[0]:
                    ancetre[s] = min(ancetre[s], debut[t[0]])
            else:
                parent[t[0]] = s
                numerotation_rec(t[0])
                ancetre[s] = min(ancetre[s], ancetre[t[0]])
    for v in G.sommets():
        if debut[v] == 0:
            numerotation_rec(v)
    return debut, parent, ancetre    



def points_articulation(G):
    articulations = set()
    debut, parent, ancetre = numerotations(G)
    racines = {v for v in G.sommets() if parent[v] is None}
    
    for depart in racines:
        if sum(value == depart for value in parent.values()) >= 2:
            articulations.add(depart)
    
    racines.add(None)

    for v in G.sommets():
        if parent[v] not in racines and ancetre[v] >= debut[parent[v]]:
            articulations.add(parent[v])
    return articulations

def ponts(reseau):
    debut, parent, ancetre = numerotations(reseau)
    res = list()
    for sommet in reseau.sommets():
        if parent[sommet] != None:
            if ancetre[sommet] > debut[parent[sommet]]:
                if parent[sommet] > sommet:
                    res.append((sommet, parent[sommet]))
                else:
                    res.append((parent[sommet], sommet))
    return res

def racine_sommet(sommet, parent):
    if parent[sommet] == None:
        return sommet
    return racine_sommet(parent[sommet], parent)

def dictionnaire(sommet, val):
    dico = dict()
    for u in sommet:
        dico[u] = val
    return dico


def amelioration_ponts(reseau):
    pont_reseau = ponts(reseau)
    debut, parent, ancentre = numerotations(reseau)

    def composantes_sans_ponts(sommet, csp, deja_visite):
        if not deja_visite[sommet]:
            deja_visite[sommet] = True
            csp.add(sommet)
            for u, ligne in reseau.voisins(sommet):
                if tuple(sorted((sommet, u))) not in pont_reseau:
                    composantes_sans_ponts(u, csp, deja_visite)
        return csp

    def construction_arbre(p):
        arbre = Graphe()
        for (u, v) in p:
            deja_visite = dictionnaire(reseau.sommets(), False)
            csp1 = composantes_sans_ponts(u, set(), deja_visite)
            deja_visite = dictionnaire(reseau.sommets(), False)
            csp2 = composantes_sans_ponts(v, set(), deja_visite)
            if csp1 != csp2:
                arbre.ajouter_arete(tuple((sorted(csp1))), tuple((sorted(csp2))), None)

        return arbre

    arbre = construction_arbre(pont_reseau)
    aretes = set()

    if (reseau.nombre_aretes() <= 1):
        for u,v,ligne in reseau.aretes():
            aretes.add((u, v))
        return aretes

    feuilles = sorted([csp for csp in arbre.sommets() if arbre.degre(csp) == 1])

    for cpt in range(len(feuilles) - 1):
        i = False
        for u in feuilles[cpt]:
            for v in feuilles[cpt + 1]:
                if (u, v) not in pont_reseau and (v, u) not in pont_reseau and racine_sommet(u, parent) == racine_sommet(v, parent):
                    aretes.add((u, v))
                    i = True
                    break
            if i:
                break

    return aretes


def amelioration_points_articulation(reseau):
    debut, parent, ancentre = numerotations(reseau)
    articulations = sorted(points_articulation(reseau), reverse=True)
    aretes = set()

    def successeurs(sommet):
        next = set()
        for v, ligne in reseau.voisins(sommet):
            if parent[v] == sommet:
                next.add(v)

        return sorted(next)

    def arti_successeurs(sommet):
        next = successeurs(sommet)
        if (sommet in articulations):
            return True
        else:
            for v in successeurs(sommet):
                arti_successeurs(v)
        return False

    for u in articulations:
        lst = successeurs(u)
        if parent[u] == None:
            for i in range(len(lst) - 1):
                aretes.add((lst[i], lst[i + 1]))
        else:
            for v in lst:
                if not arti_successeurs(v) and ancentre[v] >= debut[u]:
                    aretes.add((v, racine_sommet(u, parent)))
    return aretes



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--metro", nargs = "*")
    parser.add_argument("--rer", nargs = "*")
    parser.add_argument("-l", "--liste-stations", action = "store_true")
    parser.add_argument("-a", "--articulations", action = "store_true")
    parser.add_argument("-p", "--ponts", action = "store_true")
    parser.add_argument("-A", "--ameliorer-articulations", action = "store_true")
    parser.add_argument("-P", "--ameliorer-ponts", action = "store_true")
    args = parser.parse_args()

    G = Graphe()

    if args.metro != None:
        if len(args.metro) != 0:
            for i in args.metro:
                f = "METRO_" + str(i) + ".txt"
                charger_donnees(G, f)
        else:
            for repertoire, sousrep, fichiers in walk("."):
                for f in fichiers:
                    if f[0] == 'M':
                        charger_donnees(G, f)
        print("Le réseau contient " + str(G.nombre_sommets()) + " sommets et " + str(G.nombre_aretes()) + " arêtes.")
        print("Chargement des lignes " + str(args.metro) + " de metro terminé.")

    if args.rer != None:
        if len(args.rer) != 0:
            for i in args.rer:
                f = "RER_" + str(i) + ".txt"
                charger_donnees(G, f)
        else:
            for repertoire, sousrep, fichiers in walk("."):
                for f in fichiers:
                    if f[0] == 'R':
                        charger_donnees(G, f)
        print("Le réseau contient " + str(G.nombre_sommets()) + " sommets et " + str(G.nombre_aretes()) + " arêtes.")
        print("Chargement des lignes " + str(args.rer) + " de rer terminé.")

    if args.liste_stations == True:
        print("Le réseau contient les " + str(len(G.sommets())) + " stations suivantes :")
        for sommet in G.sommets():
            print(str(G.nom_sommet(sommet)) + " (" + str(sommet) + ")")

    if args.articulations == True:
        i = 1
        arti = points_articulation(G)
        print("Le réseau contient les " + str(len(arti)) + " points d'articulations suivants :")
        for s in arti:
            print(str(i) + " : " + str(G.nom_sommet(s)))
            i+=1

    if args.ponts == True:
        ponts = ponts(G)
        print("Le réseau contient les " + str(len(ponts)) + " ponts suivants :")
        for pont in ponts:
            print("- " + str(G.nom_sommet(pont[0])) + " -- " + str(G.nom_sommet(pont[1])))

    if args.ameliorer_ponts == True:
        ap = amelioration_ponts(G)
        print("On peut éliminer tous les ponts du réseau en rajoutant les " + str(len(ap)) + " arêtes suivantes :")
        for pont in ap:
            print("- " + str(G.nom_sommet(pont[0])) + " -- " + str(G.nom_sommet(pont[1])))

    if args.ameliorer_articulations == True:
        aparti = amelioration_points_articulation(G)
        print("On peut éliminer tous les points d'articulations du réseau en rajoutant les " + str(len(aparti)) + " arêtes suivantes :")
        for a in aparti:
            print("- " + str(G.nom_sommet(a[0])) + " -- " + str(G.nom_sommet(a[1])))


