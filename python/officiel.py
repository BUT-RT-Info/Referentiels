import logging, yaml
import unicodedata

__LOGGER = logging.getLogger(__name__)

# Récupère les informations officielles sur les ressources (code/nom)
with open("pn/ressources.yml", 'r', encoding="utf8") as fid:
    DATA_RESSOURCES = yaml.load(fid.read(), Loader=yaml.Loader)
# Récupère les données officielles des ACs
with open("pn/acs.yml", 'r', encoding="utf8") as fid:
    DATA_ACS = yaml.load(fid.read(), Loader=yaml.Loader)
with open("pn/saes.yml", 'r', encoding="utf8") as fid:
    DATA_SAES = yaml.load(fid.read(), Loader=yaml.Loader)


def supprime_accent_espace(chaine):
    """Met en minuscule, supprime les accents, les ponctuations et les espaces"""
    purge = chaine.lower().replace("'", "").replace("’", "")
    purge = unicodedata.normalize('NFD', purge).encode('ascii', 'ignore').decode('ascii')
    purge = purge.replace(" ", "")
    return purge

def devine_code_by_nom_from_dict(champ, dico):
    """Partant d'une chaine de caractères décrivant une ressource, une SAé ou un ACS,
    détermine le code présent dans le dico officiel (dico à double entrée),
    Le dico officiel vient d'un .yml"""
    acs = []
    champ_purge = supprime_accent_espace(champ)

    for comp in DATA_ACS:
        for code in DATA_ACS[comp]:
            acs_purge = supprime_accent_espace(DATA_ACS[comp][code])
            if acs_purge in champ_purge:
                acs += [code]
    return sorted(list(set(acs)))


def get_matrices_ac_ressource(ressources, sem):
    """Calcul la matrice AC vs ressource pour un sem donné et renvoie la
    chaine pour affichage dans un .txt"""
    les_codes_acs = [code for comp in DATA_ACS for code in DATA_ACS[comp]]
    nbre_acs = len(les_codes_acs)

    ressem = ressources[sem]  # les ressources du semestre
    nbre_ressources_semestre = len(DATA_RESSOURCES[sem])
    if len(ressem) != nbre_ressources_semestre:
        __LOGGER.warning(f"Pb => il manque des ressources au {sem}")

    matrice = [[False] * nbre_ressources_semestre for i in range(nbre_acs)]

    for (i, r) in enumerate(ressem):  # pour chaque ressource
        for comp in range(len(r.apprentissages)):  # pour chaque comp
            for (j, ac) in enumerate(les_codes_acs):  # pour chaque ac
                if ac in r.apprentissages[comp]:  # si l'ac est prévue dans la ressource
                    matrice[j][i] = True

    chaine = ""
    ligne = "{:20s} | " + "{:4s} | " * nbre_ressources_semestre
    valeurs = ("" for i in range(nbre_ressources_semestre + 1))
    trait = "-" * len(ligne.format(*valeurs))

    valeurs = [""] + [r.code if r.code else "????" for r in ressem] + [""] * (
                    nbre_ressources_semestre - len(ressem))
    valeurs = tuple(valeurs)
    chaine += ligne.format(*valeurs) + "\n" + trait + "\n"
    for (j, ac) in enumerate(les_codes_acs):
        valeurs = [ac] + [("X" if matrice[j][i] == True else "") for i in range(nbre_ressources_semestre)]
        valeurs = tuple(valeurs)
        chaine += ligne.format(*valeurs) + "\n"
    chaine += trait + "\n"
    return (matrice, chaine)