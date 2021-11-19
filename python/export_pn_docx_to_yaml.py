import os.path
import sys
import argparse
import logging
import docx2python
import officiel

from config import Config


def get_docx_format(tableau_document): # <- doc[i]
    """Renvoie le format (BUT1 ou BUT23) du contenu lu"""
    try:
        if "Nom de la " in tableau_document[0][0][0]:
            return "BUT1"
    except:
        pass
    try: # BUT 23
        if "Code " in tableau_document[0][0][0] or "Code SAE" in tableau_document[0][0][0]:
            return "BUT23"
    except:
        pass
    return None


def get_type_fiche(tableau_document): # <- docu[i]
    """Indique si ressource ou SAE"""
    if "ressource" in tableau_document[0][0][0].lower():
        return "RESSOURCE"
    else:
        return "SAE"


def get_ressource_BUT1_from_google(code_ressource, res):
    """Lit les infos du docx pour une ressource du BUT1 à partir du tableau"""
    # if len(res) != 15:
    # __LOGGER.warning(f"Champs en trop ou manquants dans \"{nom_ressource}\"")
    # Parsing des données brute de la ressource
    data = [None for i in range(len(ENTETES_BUT1))]  # les données attendues Nom, Code, ..., Mots clés
    apprentissages = [None for i in range(3)]  # les apprentissages des 3 compétences
    coeffs = [None for i in range(3)]
    data[-1] = 'Tronc commun' # Pas de mention du parcours dans les fiches de BUT1

    non_interprete = []
    for j in range(len(res)):  # parcours des entêtes du tableau décrivant la ressource
        ligne = res[j]
        if len(ligne) == 2:  # ligne de données classique champ => valeur
            champ = ligne[0][0]  # le nom du champ
            i = tools.get_indice_sans_accent_ni_espace(champ, ENTETES_BUT1)  # l'indice de l'entete dans ENTETES
            if i != None:
                data[i] = tools.caracteres_recalcitrants("\n".join(res[j][1]))
                if champ == "Prérequis" and not data[i]:
                    data[i] = officiel.AUCUN_PREREQUIS
                    print(f"Dans {code_ressource}, complète les prérequis à {officiel.AUCUN_PREREQUIS}")
            else:
                non_interprete.append((champ, ligne[1][0]))
        else:  # ligne de données soit chapeau (ex Compétences ciblées) soit détail par compétence
            champ = ligne[0][0]
            if "Apprentissages" in champ:  # les compétences ciblées sont déduites de la présence d'apprentissage critiques
                # j+1 = les ACs par compétences
                acs = res[j + 2]
                for k in range(len(acs)):
                    apprentissages[k] = tools.caracteres_recalcitrants(
                        "\n".join(acs[k]))  # fusionne les ACS (généralement sur plusieurs lignes)
            elif "Compétence(s) ciblée(s)" in champ:
                les_coeffs = res[j + 2]
                coeffs = [elmt[0] for elmt in les_coeffs]
    if non_interprete:  # souvent Heures de formation (incluant les TP)

        try:
            indice_champ = [chp[0] for chp in non_interprete].index("Heures de formation (incluant les TP)")
        except:
            indice_champ = -1
        if indice_champ >= 0:  # si le champ "Heures de formation (incluant les TP)" est trouvé
            # tente de réinjecter les heures dans Heures encadrées si elles n'on pas déjà été renseignées
            indice_heure = tools.get_indice("formation encadrée", ENTETES_BUT1)
            if not data[indice_heure]:
                print(
                    f"Dans \"{code_ressource}\", réinjection de \"Heures de formation (incluant les TP)\" dans \"formation encadrée\"")
                data[indice_heure] = champ[1]
                non_interprete = non_interprete[:indice_champ] + non_interprete[indice_champ + 1:]  # supprime le champ

        if non_interprete:
            __LOGGER.warning(f"Dans \"{code_ressource}\", champs en trop non interprétés  : " + ",".join(
                [chp[0] for chp in non_interprete]))

    # Analyse des champs manquants
    champ_manquants = []
    for (j, champ) in enumerate(ENTETES_BUT1):
        if not data[j]:
            champ_manquants += [champ]
    if champ_manquants:
        __LOGGER.warning(f"Dans \"{code_ressource}\", champs manquants  : " + ",".join(champ_manquants))

    # Sauvegarde des champs de la ressource
    info = tuple(data[1:])
    competences = [] # Ajoute les compétences
    for (i, c) in enumerate(coeffs):
        if coeffs[i]:
            competences.append("RT" + str(i+1))
    return info, apprentissages, competences, coeffs


def get_ressource_BUT23_from_google(code_ressource, docu):
    """Lit les infos du docx pour une ressource du BUT23 à partir du tableau"""
    # if len(res) != 15:
    # __LOGGER.warning(f"Champs en trop ou manquants dans \"{nom_ressource}\"")
    # Parsing des données brute de la ressource
    data = [None for i in range(len(ENTETES_BUT1))]  # les données attendues Nom, Code, ..., Mots clés
    apprentissages = []  # les apprentissages des 5 compétences
    competences = []
    coeffs = {} # si existant

    non_interprete = []
    for i in range(len(docu)):
        res = docu[i] # le tableau en cours

        # la 1ère ligne
        ligne = res[0]
        if len(ligne) == 1:
            champ = ligne[0][0]
            k = None
            if champ.startswith("Description"):
                k = tools.get_indice_sans_accent_ni_espace("Descriptif", ENTETES_BUT1)
                val = "\n".join(res[1][0]) # toutes les lignes
            elif champ.startswith("Mots"):
                k = tools.get_indice_sans_accent_ni_espace("Mots", ENTETES_BUT1)
                val = res[1][0][0]
            elif champ.startswith("Parcours"):
                k = tools.get_indice_sans_accent_ni_espace("Parcours", ENTETES_BUT1)
                val = res[1][0][0]
            elif champ.startswith("Semestre"):
                val = champ.split(":")[-1].strip()
                k = tools.get_indice_sans_accent_ni_espace("Semestre", ENTETES_BUT1)
            elif "Prérequis" in champ:
                k = tools.get_indice_sans_accent_ni_espace("Prérequis", ENTETES_BUT1)
                val = []
                for l in range(1, len(res)):
                    if res[l][0][0]:
                        val.append(res[l][0][0])
                val = "\n".join(val)
                if not val:
                    val = officiel.AUCUN_PREREQUIS
                    print(f"Dans {code_ressource}, complète les prérequis à {officiel.AUCUN_PREREQUIS}")
                data[k] = val
            elif "SAÉ" in champ:
                k = tools.get_indice_sans_accent_ni_espace("SAÉ", ENTETES_BUT1)
                val = []
                for l in range(1, len(res)):
                    if res[l][0][0]:
                        val.append(res[l][0][0])
                val = tools.caracteres_recalcitrants("\n".join(val))
            if k != None:
                data[k] = tools.caracteres_recalcitrants(val)

        elif len(ligne) == 2:  # ligne de données classique champ => valeur ou tableau des heures
            champ = ligne[0][0]  # le nom du champ
            if champ == "Heures totales":
                k = tools.get_indice_sans_accent_ni_espace("Heures de formation",
                                                           ENTETES_BUT1)  # l'indice de l'entete dans ENTETES
                data[k] = res[1][0][0]
                k = tools.get_indice_sans_accent_ni_espace("dont heures de TP", ENTETES_BUT1)
                data[k] = res[1][1][0]
            elif "Compétences" in champ: # et apprentissage
                # D'abord les comp puis les AC
                positions = [res[j][0][0].startswith("Apprentissages") for j in range(len(res))] # l'indice de début des AC
                deb_apprentissage = positions.index(True)
                competences = []
                for k in range(0, deb_apprentissage):
                    competences.append(tools.caracteres_recalcitrants(res[k][1][0]))
                # Apprentissages critiques
                apprentissages = []
                for k in range(deb_apprentissage, len(res)):
                    if res[k][1][0]:
                        apprentissages.append(tools.caracteres_recalcitrants(res[k][1][0]))


        else:  # ligne avec colonne de données => chapeau
            champ = ligne[0][0]
            if "Code" in champ:
                ordre_semestre = res[1][1][0]
                k = tools.get_indice_sans_accent_ni_espace("Code", ENTETES_BUT1)
                data[k] = res[1][0][0] if res[1][0][0] else res[1][3][0] # le code
                k = tools.get_indice_sans_accent_ni_espace("Nom", ENTETES_BUT1)
                data[k] = res[1][2][0] # le nom

    # Analyse des champs manquants
    champ_manquants = []
    for (j, champ) in enumerate(ENTETES_BUT1):
        if not data[j]:
            champ_manquants += [champ]
    if champ_manquants:
        __LOGGER.warning(f"Dans \"{code_ressource}\", champs manquants  : " + ",".join(champ_manquants))

    # Sauvegarde des champs de la ressource
    info = tuple(data[1:])
    return info, apprentissages, competences, coeffs


def parse_docu_ressource(code_ressource, docu):
    """
    Parse un document google exporté en .docx, avec pour son code_ressource donné.
    Format du parsing issu de docx2python
    [  # document
        [  # table A
            [  # table A row
                [  # table A cell 1  <-- structure des tableaux
    """
    # A priori un tableau avec un titre (AnnexeD ou Données) puis les tableaux de synthèse de la ressource
    res = docu[1]  # le 1er contenu
    version = get_docx_format(res)

    if version == "BUT1":
        nom_ressource = tools.caracteres_recalcitrants(res[0][1][0])
    else:  # version BU12
        nom_ressource = tools.caracteres_recalcitrants(res[1][2][0])

    # Création de la ressource
    r = activitedocx.RessourceDocx(nom_ressource, code_ressource, res, pnofficiel)

    if version == "BUT1":
        info, apprentissages, competences, coeffs = get_ressource_BUT1_from_google(code_ressource, docu[1])  # le tableau de la fiche
    else:
        info, apprentissages, competences, coeffs = get_ressource_BUT23_from_google(code_ressource, docu[1:])  # le docu

    r.charge_informations(*info)
    r.charge_ac(apprentissages)
    r.charge_competences(competences)
    r.charge_coeffs(coeffs)


    return r


__LOGGER = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description="Parse doc ressources et crée yaml", 
    usage='%(prog)s [options]'
    )
# parser.add_argument(
#    "DOCUMENT",
#    nargs="?",
#    default="../google/" + "compilation-ressources-JOBO21" + ".docx",
#    help="docx à parser, defaut: ../google/compilation-ressources-JOBO21.docx"
#    )
parser.add_argument(
    "-o", 
    "--outdir",
    default= "../yaml/ressources",
    help="repertoire resultat, defaut: ../yaml/ressources"
    )
parser.add_argument(
    "-r", 
    "--root", 
    default="..", 
    help="repertoire de base (racine) pour chercher les fichiers de données"
    )
args = parser.parse_args()
Config.ROOT = args.root

# __LOGGER.warning(f"{sys.argv[0]} processing {args.DOCUMENT}")
# __LOGGER.warning(f"{sys.argv[0]} outputs to {args.outdir}")

# Ces imports doivent être faits après la config
import tools, activitedocx, officiel

# Récupère les données officielles
pnofficiel = officiel.Officiel()

# Ouverture du document
# if not os.path.isfile(args.DOCUMENT):
#    print(f"Le fichier à parser {args.DOCUMENT} n'existe pas")
#    sys.exit()

REPERTOIRE_GOOGLE = "../google/"

ENTETES_BUT1 = ["Nom", "Code", "Semestre", "Heures de formation", "dont heures de TP",
                "SAÉ", "Prérequis", "Descriptif", "Mots", "Parcours"]

liste_ressources = []  # la liste des ressources telle qu'extrait du docx
liste_saes = []

DATA_RESSOURCES = officiel.get_DATA_RESSOURCES() # les ressources du PN
for sem in DATA_RESSOURCES: # ['S1']: #
    for code_ressource in DATA_RESSOURCES[sem]:
        fichier = pnofficiel.get_docx_file_by_code(code_ressource)

        fichier = REPERTOIRE_GOOGLE + fichier
        if not fichier or not os.path.exists(fichier):
            print(f"{fichier} manquant pour la ressource {code_ressource}")
        else:
            docu = docx2python.docx2python(fichier)
            docu = docu.body

            # A priori un tableau avec un titre (AnnexeD ou Données) puis les tableaux de synthèse de la ressource
            type_fiche = False

            try:
                res = docu[1]  # le 1er contenu
                version = get_docx_format(res)
                type_fiche = get_type_fiche(res)
            except:
                pass

            if type_fiche == "RESSOURCE":
                r = parse_docu_ressource(code_ressource, docu)
                if r:
                    liste_ressources.append(r)

# fin du parsing
print(f"{len(liste_ressources)} ressources")

# ************************************************************************

# Post traitement des ressources => gestion des heures/des acs/ + tri par semestre
ressources = {"S{}".format(d) : [] for d in range(1, 7)}

for (i, r) in enumerate(liste_ressources):
    r.nettoie_champ()

    # Remet en forme les mots-clés
    # Tri dans le bon semestre
    ressources["S" + r.semestre] += [r]

# complète les codes d'après les numéros => inutilisé ?
# for sem in ressources:
#    for (i, r) in enumerate(ressources[sem]):
    #        if not r.code:
    #       if i == 0:
    #           r.code = "R" + sem[1] + "01"
    #       elif ressources[sem][i-1].code:
#           r.code = "R" + sem[1] + "{:02d}".format(int(ressources[sem][i-1].code[-2:])+1)

# Export yaml
WITH_EXPORT = True
for sem in ressources:
    for r in ressources[sem]:
        output = r.to_yaml()
        if WITH_EXPORT and r.code:
            fichier = f"{args.outdir}/{r.code}.yml"
            __LOGGER.warning(f"writing '{fichier}")
            with open(fichier, "w", encoding="utf8") as fid:
                fid.write(output)

