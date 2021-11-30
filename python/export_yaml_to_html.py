import os
import sys
import argparse
import glob

import rofficiel.acs
import rofficiel.competences
import rpn.exemple
import rpn.ressource
import rpn.sae

sys.path.insert(0,"../python")
from config import Config
from jinja2 import Template, Environment, FileSystemLoader

# Description des arguments possibles du programme
parser = argparse.ArgumentParser(description="Conversion des YAML en HTML")
parser.add_argument(
    "-r",
    "--root",
    default="..",
    help="repertoire de base (racine) pour chercher les fichiers de données"
)
args = parser.parse_args()
Config.ROOT = args.root

import activite
import officiel

# Chemins des différents dossiers
REPERTOIRE_TEMP = Config.ROOT + "/python/export"
REPERTOIRE_RESSOURCES_DEFINITIVES = Config.ROOT + "/yaml/ressources"
REPERTOIRE_SAE_DEFINITIVES = Config.ROOT + "/yaml/saes"
REPERTOIRE_COMPETENCES_DEFINITIVES = Config.ROOT + "/yaml/competences"
REPERTOIRE_ACS = Config.ROOT + "/yaml/pn"

REPERTOIRE_HTML = Config.ROOT + "/html/export"
REPERTOIRE_JS = REPERTOIRE_HTML + "/js"
CHEMIN_TEMPLATE = Config.ROOT + "/html"

# Créer le dossier html/export et html/export/js s'il n'existe pas
if not os.path.exists(REPERTOIRE_HTML):
    os.makedirs(REPERTOIRE_HTML)
if not os.path.exists(REPERTOIRE_JS):
    os.makedirs(REPERTOIRE_JS)

pnofficiel = officiel.Officiel()

# Chargement des ressources : depuis les versions définitives du répertoire yaml d'abord,
# puis dans python/export si manquantes
fichiers_definitifs = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_RESSOURCES_DEFINITIVES+'/*.yml') ] #nom fichier dans yaml/ressources
fichiers_temp = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_TEMP+'/*.yml') ] #nom fichier dans python/export
fichiers_ressources = [REPERTOIRE_RESSOURCES_DEFINITIVES + "/" + f for f in fichiers_definitifs] # chemins de fichier ressources YAML
for f in fichiers_temp:
    if f not in fichiers_definitifs and f.startswith("R"):
        fichiers_ressources.append(REPERTOIRE_TEMP + "/" + f)
fichiers_ressources = sorted(fichiers_ressources) # tri par ordre alphabétique

ressources = {"S1": [], "S2": []}
for fichieryaml in fichiers_ressources:
    r = rpn.ressource.Ressource(fichieryaml, pnofficiel) # lecture du fichier
    sem = "S" + str(r.yaml["semestre"])
    ressources[sem].append(r)
# tri par code croissant
for sem in ressources:
    ressources[sem] = sorted(ressources[sem], key=lambda r: r.yaml["code"])

# Chargement des saé et des exemples
fichiers_definitifs = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_SAE_DEFINITIVES+'/*.yml') ]
fichiers_temp = [ os.path.split(x)[1] for x in glob.glob(REPERTOIRE_TEMP+'/*.yml') ]
fichiers_saes = [REPERTOIRE_SAE_DEFINITIVES + "/" + f for f in fichiers_definitifs if "exemple" not in f]
fichiers_exemples = [REPERTOIRE_SAE_DEFINITIVES + "/" + f for f in fichiers_definitifs if "exemple" in f]
for f in fichiers_temp:
    if f not in fichiers_definitifs and f.startswith("S"):
        if "exemple" not in f:
            fichiers_saes.append(REPERTOIRE_TEMP + "/" + f)
        elif "exemple" in f:
            fichiers_exemples.append(REPERTOIRE_TEMP + "/" + f)
fichiers_saes = sorted(fichiers_saes) # tri par ordre alphabétique
fichiers_exemples = sorted(fichiers_exemples)

saes = {"S1": [], "S2": []}
for fichieryaml in fichiers_saes:
    s = rpn.sae.SAE(fichieryaml, pnofficiel)
    sem = "S" + str(s.yaml["semestre"])
    saes[sem].append(s)

for sem in saes:
    saes[sem] = sorted(saes[sem], key=lambda s: s.yaml["code"])

exemples = {"S1" : {}, "S2" : {} }

for fichieryaml in fichiers_exemples:
    e = rpn.exemple.ExempleSAE(fichieryaml, pnofficiel)
    sem = "S" + str(e.yaml["semestre"])
    sae = e.yaml["code"]
    if sae not in exemples[sem]:
        exemples[sem][sae] = []
    exemples[sem][sae].append(e)

#Liste de string pour renommer certaines catégories (les autres qui n'ont pas besoins ont la première lettre en majuscule)
rename = {
    "heures_encadrees": "Heures encadrées",
    "heures_formation": "Heures formation",
           "heures_tp": "Heures TP",
                  "tp": "Heures TP",
              "coeffs": "Coef.",
                 "acs": "ACs",
            "motscles": "Mots clés",
                 "sae": "SAÉ",
           "prerequis": "Prérequis",
       "problematique": "Problématique",
            "modalite": "Modalité"
}

# Création de l'environnement pour charger les templates
env = Environment(trim_blocks=True, lstrip_blocks=True, loader=FileSystemLoader(CHEMIN_TEMPLATE))

# Template de la page index et génération de la page
template_index = env.get_template("indexTemplate.html")
template_index.stream().dump(REPERTOIRE_HTML + "/index.html")

# Template de chaque pages ressources, saes, exemples (doit contenir datas,rename,precedent,suivant)
template = env.get_template("InfoTemplate.html")

# Template de chaque pages de compétences (doit contenir data,rt,precedent,suivant)
template_Competence = env.get_template("CompetenceTemplate.html")

# Template de chaque pages de ACs (doit contenir data, precedent, suivant)
template_AC = env.get_template("ACTemplate.html")

# Template de la liste des ACs
template_List_ACs = env.get_template("ListACsTemplate.html")

# Template de la liste des ressources par semestre (doit contenir data,sem)
template_List_Ressource = env.get_template("ListRessourceTemplate.html")

# Template de la liste des acs ou  saes ou ressources (doit contenir data,titre)
template_List = env.get_template("ListTemplate.html")

def motscles(mc):
    """ Retourne un tableau de mots clés en prenant en compte les parenthèses """
    motscles = []
    mot = ""
    i = 0
    while i < len(mc):
        if mc[i] == "(":
            while mc[i] != ")":
                mot += mc[i]
                i += 1
        elif mc[i] == "," and mc[i+1] == " ":
            motscles.append(mot)
            mot = ""
            i += 2
        mot += mc[i]
        i += 1
    motscles.append(mot)
    return motscles

def formatHTML(string):
    """ Retourne un string avec les balises <ul> , <li> et <p> correctement placé, code plus compliqué pour ce qu'il fait"""
    texte = "\n" # \n permet d'améliorer la lisibilité dans les fichiers html
    phrases = list(filter(None,string.split("\n")))
    i = 0
    while i < len(phrases):
        if "* " in phrases[i]: # première balise li détecté
            texte += "<ul>\n" 
            while i < len(phrases) and "*" in phrases[i]: # Tant qu'il y a des * on continue de créer des balises li
                texte += "  <li>" + phrases[i][2:] + "</li>\n"
                if i+1 < len(phrases):
                    if phrases[i+1][:3] == "  *": # Si il y a une liste dans un li
                        texte += "  <ul>\n"
                        while i + 1 < len(phrases) and phrases[i+1][:2] == "  ": # Tant qu'on est dans la liste
                            if "*" in phrases[i+1]:
                                texte += "      <li>" + phrases[i+1][4:] + "</li>\n"
                            else:
                                texte = texte[:-6]
                                while i + 1 < len(phrases) and phrases[i+1][:2] == "  ": # Si il y a des retour chariot
                                    texte += phrases[i+1][3:]
                                    i += 1
                                i -= 1
                            i += 1
                        texte += "  </ul>\n"
                    elif phrases[i+1][:2] == "  ": # Retour à la ligne d'un li
                        texte = texte[:-6]
                        while i + 1 < len(phrases) and phrases[i+1][:2] == "  ":
                            texte += phrases[i+1][1:]
                            i += 1
                        texte += "</li>\n"
                i += 1
            texte += "</ul>\n"
            i -= 1
        else:
            texte += "<p>" + phrases[i] + "</p>\n"
        i += 1
    return texte[:-1] # On enlève le dernier \n 

def defineSearchTerm(dictio, url, documents):
    """ Retourne un dictionnaire d'une ressource compatible Lunr pour la recherche de cet élément """
    document = {}
    document["code"] = dictio["code"]
    document["url"] = url
    if "titre" in dictio: document["titre"] = dictio["titre"]
    else: document["titre"] = dictio["nom"]
    if "motscles" in dictio: document["motscles"] = dictio["motscles"]
    if "diminutif" in dictio: document["diminutif"] = dictio["diminutif"]
    if "description" in dictio: document["description"] = dictio["description"]
    if "contexte" in dictio: document["contexte"] = dictio["contexte"]
    if "contenu" in dictio: document["contenu"] = dictio["contenu"]
    documents[document["code"]] = document

# Créer un fichier contenant la liste des saes
datas = {"data" : saes, "title": "SAEs"} # "data" contient un tableau des saes
template_List.stream(datas).dump(REPERTOIRE_HTML + "/SAE.html")

# Créer un fichier contenant la liste des ressources
datas = {"data" : ressources, "title": "Ressources"}
template_List.stream(datas).dump(REPERTOIRE_HTML + "/ressources.html")

documents = {} # Définition d'un liste de document contenant les informations nécessaires pour la recherche
SAE_mobilise_AC = {} # Dictionnaire de ACs contenant la liste des SAE qui les mobilisent
relations = {"nodes": [], "links": []} # Dictionnaires des relations entre les ressources pour le graphe

# Création des pages individuelles ressources, saes, exemples
for indexSem, sem in enumerate(ressources):

    # ____________________ Ressources ____________________
    for indexRessource, ressource in enumerate(ressources[sem]):
        
        data = {}
        
        for categorie, valeur in ressource.getInfo().items():
            data[categorie] = valeur
        
        # Mise en page des textes en HTML
        data["contenu"] = formatHTML(data["contenu"])
        data["contexte"] = formatHTML(data["contexte"])
        
        # Sépare les motclés pour former des tags
        data["motscles"] = motscles(data["motscles"])
        datas = {"data": data, "rename": rename} # Rename contient le dico pour renommer les catégories ressources[list(ressources.keys())[indexSem - 1]]
        
        # Ajoute les liens pour les boutons "Suivant" et "Précédent"
        # On doit prendre en compte le premier ressource et la dernière ressource du dernier semestre
        if indexRessource > 0: datas["precedent"] = "R" + str(int(data["code"][1:])-1) + ".html"
        elif indexSem > 0: datas["precedent"] = "R" + ressources["S"+str(indexSem)][-1].getInfo()["code"][1:] + ".html"
        if indexRessource < len(ressources[sem]) - 1: datas["suivant"] = "R" + str(int(data["code"][1:])+1) + ".html"
        elif indexSem < len(ressources) - 1: datas["suivant"] = "R" + str((indexSem+2)*100+1) + ".html"

        url = data["code"] + ".html" # Ajout de l'url pour la recherche
        defineSearchTerm(data, url, documents) # Ajout des informations de ressource pour la recherche dans une liste
        
        # Créer un fichier html depuis un TemplateStream créer à partir du template et des données dans "datas" qui remplace les variables pour Jinja2
        template.stream(datas).dump(REPERTOIRE_HTML + "/" + url)

        # Ajout des informations nécessaires pour créer le graphique (node et link)
        relations["nodes"].append({"id": data["code"], "sem": sem, "type": "Ressource"})
        for sae in data["sae"]:
            relations["links"].append({"source": data["code"], "target": sae, "sem": sem, "type": "RessourceToSAE"})
        for rt in data["acs"]:
            for ac in data["acs"][rt]:
                if not any(ac in node["id"] for node in relations["nodes"]): relations["nodes"].append({"id": ac, "sem": 0, "type": "AC"})
                relations["links"].append({"source": data["code"], "target": ac, "sem": sem, "type": "RessourceToAC"})
    
    #Créer un fichier contenant la liste des ressources du semestre
    data = {"data" : ressources[sem],"sem" : sem} # "data" contient un tableau des ressources du semestre
    template_List_Ressource.stream(data).dump(REPERTOIRE_HTML + "/ressources" + str(sem) + ".html")

    # ____________________ SAEs ____________________
    for indexSAE, sae in enumerate(saes[sem]):
        
        data = {}

        for categorie, valeur in sae.sae.items():
            data[categorie] = valeur
        # On regarde si des exemples du sae existent, si True, on les ajoute dans "data"
        if(sae.sae["code"] in exemples[sem]) : 
            data["exemples"] = exemples[sem][sae.sae["code"]]

        data["description"] = formatHTML(data["description"])
        data["livrables"] = formatHTML(data["livrables"])
        data["motscles"] = motscles(data["motscles"])
        datas = {"data":data, "rename": rename}
        
        if indexSAE > 0: datas["precedent"] = "SAE" + str(int(data["code"][3:])-1) + ".html"
        elif indexSem > 0: datas["precedent"] = "SAE" + saes["S"+str(indexSem)][-1].getInfo()["code"][3:] + ".html" # saes[list(saes.keys())[indexSem - 1]][-1].sae["code"][3:] -> "code" du dernier sae du semestre précédent        
        if indexSAE < len(saes[sem]) - 1: datas["suivant"] = "SAE" + str(int(sae.getInfo()["code"][3:])+1) + ".html"
        elif indexSem < len(saes) - 1: datas["suivant"] = "SAE" + str((indexSem+2)*10+1) + ".html"
        
        url = data["code"].replace("É","E") + ".html"
        defineSearchTerm(data, url, documents)
        template.stream(datas).dump(REPERTOIRE_HTML + "/" + url)

        # Créer la liste des SAEs mobilisés par des AC
        for rt, acs in sae.getInfo()["acs"].items():
            for ac in acs:
                if not ac in SAE_mobilise_AC: SAE_mobilise_AC[ac] = []
                SAE_mobilise_AC[ac].append(sae.getInfo())

        # Ajout des informations nécessaires pour créer le graphique (node et link)
        if not any(data["code"] in node["id"] for node in relations["nodes"]):
            relations["nodes"].append({"id": data["code"], "type": "SAE"})
        for rt in data["acs"]:
            for ac in data["acs"][rt]:
                if not any(ac in node["id"] for node in relations["nodes"]): relations["nodes"].append({"id": ac, "sem": 0, "type": "AC"})
                relations["links"].append({"source": data["code"], "target": ac, "sem": sem, "type": "SAEToAC"})

    # ____________________ Exemples SAE ____________________
    for sae in exemples[sem]:
        num = 1 # Nommage des fichiers exemple sae
        for indexExemple, exemple in enumerate(exemples[sem][sae]):
            
            data = {}
            
            for categorie, valeur in exemple.exemple.items():
                data[categorie] = valeur

            data["description"] = formatHTML(data["description"])
            data["modalite"] = formatHTML(data["modalite"])
            datas = {"data":data, "rename": rename}

            if indexExemple > 0: datas["precedent"] = "SAE" + data["code"][-2:] + "_exemple" + str(num-1) + ".html"
            if indexExemple < len(exemples[sem][sae]) - 1: datas["suivant"] = "SAE" + data["code"][-2:] + "_exemple" + str(num+1) + ".html"
            num += 1
            
            url = data["code"].replace("É","E") + "_exemple" + str(num) + ".html"
            template.stream(datas).dump(REPERTOIRE_HTML + "/" + url)
            
# Création d'une liste de AC pour créer une page listant les ACs
ListACs = {"RT1":[], "RT2":[], "RT3":[]}

# Chargement des ACs
fichieryaml = REPERTOIRE_ACS +'/acs.yml'
acs = rofficiel.competences.ACs(fichieryaml)

# Chargement des Compétences
fichieryaml = REPERTOIRE_COMPETENCES_DEFINITIVES + '/RT123.yml'
competences = rofficiel.competences.Competences(fichieryaml)

# Création des pages individuelles ACs, Compétences
for indexRt, rt in enumerate(acs.getInfo()):

    # ____________________ ACs ____________________
    for i, (ac, desc) in enumerate(acs.getInfo()[rt].items()):
        
        data = {}

        data["code"] = ac
        data["titre"] = desc
        data["sae"] = SAE_mobilise_AC[ac]
        datas = {"data":data}

        ListACs[rt].append(data)

        if i > 0: datas["precedent"] = list(acs.getInfo()[rt].keys())[i-1] + ".html"
        elif indexRt > 0: datas["precedent"] = list(acs.getInfo()["RT" + str(int(rt[-1])-1)].keys())[-1] + ".html"
        if i < len(acs.getInfo()[rt]) - 1: datas["suivant"] = list(acs.getInfo()[rt].keys())[i+1] + ".html"
        elif indexRt < len(acs.getInfo()) - 1: datas["suivant"] = list(acs.getInfo()["RT" + str(int(rt[-1])+1)].keys())[0] + ".html"
        
        url = ac + ".html"
        defineSearchTerm(data, url, documents)
        template_AC.stream(datas).dump(REPERTOIRE_HTML + "/" + url)
        
    # ____________________ Compétences ____________________

    data = {}

    for categorie, valeur in competences.getInfo()[rt].items():
        data[categorie] = valeur

    data["description"] = formatHTML(data["description"])
    datas = {"data": data, "rt": rt}

    if indexRt > 0: datas["precedent"] = "RT" + str(indexRt) + ".html"
    if indexRt < len(competences.getInfo()) - 1: datas["suivant"] = "RT" + str(indexRt + 2) + ".html"

    url = rt + ".html"
    template_Competence.stream(datas).dump(REPERTOIRE_HTML + "/" + url)
    data["code"] = rt # On le créer ici pour pas ajouter une ligne au tableau de la page mais pour la recherche
    defineSearchTerm(data, url, documents)

# Créer un fichier contenant la liste des ACs
datas = {"data": ListACs, "title": "ACs"}
template_List_ACs.stream(datas).dump(REPERTOIRE_HTML + "/ACs.html")

# Envoie des informations des documents pour la recherche
template_recherche = env.get_template("baseTemplate.js")
template_recherche.stream(documents=documents).dump(REPERTOIRE_JS + "/base.js")

# Créer un fichier contenant le graphe des relations entres les toutes les ressources
datas = {"data": relations}
template_graph = env.get_template("graphTemplate.html")
template_graphJS = env.get_template("graphTemplate.js")
template_graph.stream().dump(REPERTOIRE_HTML + "/graph.html")
template_graphJS.stream(datas).dump(REPERTOIRE_JS + "/graph.js")