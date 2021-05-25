import string, logging
import pypandoc
import ruamel.yaml

import latex
import officiel

import ressourcedocx
from modeles import get_modele, TemplateLatex

__LOGGER = logging.getLogger(__name__)

MODALITES = ["CM/TD", "TP", "Projet"]   # modalités de mise en oeuvre d'une ressource/SAE


class ActivitePedagogique():
    """Modélise les éléments de bases d'une activité pédagogique (ressource ou SAE).
    Classe servant de base à l'héritage.

    Une activité pédagogique est initialisée par lecture des données contenues dans fichier yaml (attribut yaml)
    """
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        """Charge les données du fichier yaml"""
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.yaml = yaml.load(fid.read())
            except:
                ActivitePedagogique.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")

    def add_tags(self, tags):
        """Ajoute un attribut tags avec la liste de tags fournie"""
        self.tags = tags

    def get_heures_encadrees(self):
        """Renvoie les heures de formation encadrees (incluant les TP)"""
        return self.heures_encadrees

    def get_heures_tp(self):
        """Renvoie les heures de TP"""
        return self.heures_tp

    def get_heures_projet(self):
        """Renvoie les heures de projet tuteurés"""
        return self.heures_projet


class Ressource(ActivitePedagogique):
    """Modélise une ressource lorsqu'elle est extraite d'un fichier yaml"""

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        super().__init__(fichieryaml)
        self.ressource = self.yaml
        self.heures_encadrees = self.yaml["heures_formation"]
        self.heures_tp = self.yaml["heures_tp"]
        self.heures_projet = 0

    def to_latex(self, modele):
        """Génère le code latex décrivant la ressource en utilisant le
        modèle latex indiqué"""
        modlatex = get_modele(modele)

        # Préparation des coeffs
        ajoutcoeff = "\\ajoutRcoeff{%s}"
        coeffRT = []
        for comp in ["RT1", "RT2", "RT3"]:
            if comp in self.ressource["coeffs"]:
                coeffRT.append(ajoutcoeff % (str(self.ressource["coeffs"][comp])))
            else:
                coeffRT.append("")

        # Préparation des ac
        DATA_ACS = officiel.get_DATA_ACS()
        ajoutac = "\\ajoutRac{%s}{%s}"
        compRT = []
        for accomp in ["RT1", "RT2", "RT3"]:
            comps = []
            if accomp in self.ressource["acs"]:
                for no_ac in range(
                    len(self.ressource["acs"][accomp])
                ):  # les ac de la comp
                    code_ac = self.ressource["acs"][accomp][no_ac]
                    comps.append(ajoutac % (code_ac, DATA_ACS[accomp][code_ac]))
            compRT.append("\n".join(comps))

        # Préparation des sae
        ajoutsaes = "\\ajoutRsae{%s}{%s}"  # nom, intitule, code_latex
        saesRT = []
        for (i, sae) in enumerate(
            self.ressource["sae"]
        ):  # in range(len(self.apprentissages)):
            code_latex = (
                string.ascii_uppercase[int(sae[-2]) - 1]
                + string.ascii_uppercase[int(sae[-1]) - 1]
            )
            saesRT.append(
                ajoutsaes % (sae, officiel.get_officiel_sae_name_by_code(sae))
            )  # , code_latex))
        saes = "\n".join(saesRT)

        if self.ressource["code"] == "R110":
            print("ici")
        prerequis = ""
        if self.ressource["prerequis"] == officiel.AUCUN_PREREQUIS:
            prerequis = ""
        else:
            # est-une liste de ressources
            if not self.ressource["prerequis"][0].startswith("R"):
                prerequis = "\\ajoutRprerequislycee{%s}" % (self.ressource["prerequis"])
            else:
                ajoutprerequis = "\\ajoutRprerequis{%s}{%s}"
                liste = []
                for (no, mod) in enumerate(self.ressource["prerequis"]):
                    liste.append(
                        ajoutprerequis % (mod, officiel.get_officiel_ressource_name_by_code(mod))
                    )
                prerequis = "\n".join(liste)

        # préparation du contexte
        contexte = self.ressource["contexte"]
        if contexte == "Aucun":
            contexte = ""
            Ressource.__LOGGER.warning(f"{self.ressource['nom']} n'a pas de contexte")

        else:
            contexte = md_to_latex(contexte)

        # contexte = remove_ligne_vide(contexte)
        # préparation du contenu

        contenu = self.ressource["contenu"]  # supprime les passages à la ligne

        if contenu:
            if self.ressource["code"] == "R112":
                print("ici")
            contenu = md_to_latex(contenu)

        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(
            code=self.ressource["code"],
            nom=self.ressource["nom"],
            heures_formation=self.ressource["heures_formation"],
            heures_tp=self.ressource["heures_tp"],
            coeffRT1=coeffRT[0],
            coeffRT2=coeffRT[1],
            coeffRT3=coeffRT[2],
            compRT1=compRT[0],
            compRT2=compRT[1],
            compRT3=compRT[2],
            saes=saes,
            motscles=self.ressource["motscles"] + ".",
            prerequis=prerequis,
            contexte=contexte,
            contenu=contenu,
        )
        # chaine = chaine.replace("&", "\&")
        chaine = latex.nettoie_latex(chaine)

        # Insère les abbréviations
        return chaine


def contient_abbr(chaine):
    """Détecte les abréviations présentes dans la chaine
    (dont la liste est fournie par DATA_ABBREVIATIONS lues depuis le .yml) et
    les renvoie sous forme d'une liste par abréviations de nombre de caractères décroissants"""
    mots = []
    DATA_ABBREVIATIONS = officiel.get_DATA_ABBREVIATIONS()
    for lettre in DATA_ABBREVIATIONS:
        for mot in DATA_ABBREVIATIONS[lettre]:
            if mot in chaine:
                mots.append(mot)
    mots = sorted(
        mots, key=lambda m: len(m), reverse=True
    )  # les mots triés par nbre de carac décroissant
    return mots


def ajoute_abbr_latex(chaine):
    """
    Parse la chaine latex pour ajouter les abbréviations et les remplacer par
    \\textabbrv{abreviation}
    """
    mots = chaine.split(" ")
    for (i, mot) in enumerate(mots):
        abbrs = contient_abbr(mot)
        if abbrs:
            mots[i] = mots[i].replace(abbrs[0], "\\textabbrv{" + abbrs[0] + "}")
    chaine = " ".join(mots)
    if "/IP" in chaine:
        chaine = chaine.replace("/IP", "/\\textabbrv{IP}")
    return chaine


def contient_commandes(chaine):
    """Détecte si la `chaine` est une commande (éventuellement avec un caractère
    de ponctuation final)"""
    chaine_texte = ""
    for car in chaine:
        if car in string.ascii_lowercase + "-":
            chaine_texte += car
    if "ipc" in chaine:
        print("ici")
    DATA_MOTSCLES = officiel.get_MOTS_CLES()
    if chaine_texte in DATA_MOTSCLES["commandes"]:
        return chaine_texte
    return None


def ajoute_cmd_latex(chaine):
    """
    Parse la chaine latex pour ajouter les abbréviations et les remplacer par
    \\textabbrv{abreviation}
    """
    mots = chaine.split(" ")
    for (i, mot) in enumerate(mots):
        champs = mot.split("\n")
        for (j, champ) in enumerate(champs):
            cmd = contient_commandes(champ)
            if cmd:
                champs[j] = champs[j].replace(cmd, "\\texttt{" + cmd + "}")
        mots[i] = "\n".join(champs)
    chaine = " ".join(mots)
    return chaine


class SAE(ActivitePedagogique):
    """Modélise une SAé (chapeau) lorsqu'elle est extraite d'un yaml"""

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        super().__init__(fichieryaml)
        self.sae = self.yaml
        self.heures_encadrees = self.yaml["heures_encadrees"]
        self.heures_tp = self.yaml["tp"]
        self.heures_projet = self.yaml["projet"]

    def to_latex(self, modele):
        """Génère le code latex décrivant la ressource en utilisant le modèle indiqué"""
        modlatex = get_modele(modele)  # "pn/modele_ressource.tex")

        # Préparation des coeffs
        ajoutcoeff = "\\ajoutScoeff{%s}"
        coeffRT = []
        for comp in ["RT1", "RT2", "RT3"]:
            if comp in self.sae["coeffs"]:
                coeffRT.append(ajoutcoeff % (str(self.sae["coeffs"][comp])))
            else:
                coeffRT.append("")

        # Préparation des ac
        ajoutac = "\\ajoutSac{%s}{%s}"  # nom, intitule, code latex
        compRT = []
        DATA_ACS = officiel.get_DATA_ACS()
        for accomp in ["RT1", "RT2", "RT3"]:
            comps = []
            if accomp in self.sae["acs"]:
                for no_ac in range(len(self.sae["acs"][accomp])):  # les ac de la comp
                    code_ac = self.sae["acs"][accomp][no_ac]
                    comps.append(ajoutac % (code_ac, DATA_ACS[accomp][code_ac]))

            compRT.append("\n".join(comps))

        # Préparation des ressources
        ajoutressources = "\\ajoutSressources{%s}{%s}"
        resRT = []
        for (i, res) in enumerate(
            self.sae["ressources"]
        ):  # in range(len(self.apprentissages)):
            resRT.append(
                ajoutressources % (res, officiel.get_officiel_ressource_name_by_code(res))
            )
        ressources = "\n".join(resRT)

        # préparation du descriptif
        descriptif = self.sae["description"]
        if descriptif == "Aucun":
            descriptif = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de description")
        else:
            descriptif = md_to_latex(descriptif)

        # préparation des livrables
        livrables = self.sae["livrables"]
        if livrables == "Aucun":
            livrables = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de livrables")
        else:
            livrables = md_to_latex(livrables)

        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(
            code=self.sae["code"],
            titre=self.sae["titre"],
            heures_encadrees=self.sae["heures_encadrees"],
            heures_tp=self.sae["tp"],
            heures_projet=self.sae["projet"],
            coeffRT1=coeffRT[0],
            coeffRT2=coeffRT[1],
            coeffRT3=coeffRT[2],
            compRT1=compRT[0],
            compRT2=compRT[1],
            compRT3=compRT[2],
            description=descriptif,
            ressources=ressources,
            livrables=livrables,
            motscles=self.sae["motscles"] + ".",
        )
        # chaine = chaine.replace("&", "\&")

        chaine = latex.nettoie_latex(chaine)
        return chaine


class ExempleSAE(ActivitePedagogique):
    """Modélise un exemple de SAE lorsqu'elle est extraite d'un yaml"""

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml):
        super().__init__(fichieryaml)
        self.exemple = self.yaml

    def to_latex(self, modele):
        """Génère le code latex décrivant la ressource en utilisant le modèle latex indiqué"""
        modlatex = get_modele(modele)  # "pn/modele_ressource.tex")

        # préparation du descriptif
        description = self.exemple["description"]
        if not description:
            description = ""
            ExempleSAE.__LOGGER.warning(
                f"{self.exemple['titre']} n'a pas de description"
            )
        else:
            description = md_to_latex(description)


        # préparation de la forme
        formes = self.exemple["formes"]
        if not formes:
            formes = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de formes")
        else:
            formes = md_to_latex(formes)

        # préparation de la problématique
        problematique = self.exemple["problematique"]
        if not problematique:
            problematique = ""
            ExempleSAE.__LOGGER.warning(
                f"{self.exemple['titre']} n'a pas de problematique"
            )
        else:
            problematique = md_to_latex(problematique)
            if "15" in self.exemple["code"]:
                # supprime le \\[3pt]
                problematique = problematique[:-7]

        # préparation des modalites
        modalite = self.exemple["modalite"]
        if not modalite:
            modalite = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de modalite")
        else:
            modalite = md_to_latex(modalite)

        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(
            titre=self.exemple["titre"],
            description=description,
            formes=formes,
            problematique=problematique,
            modalite=modalite,
        )
        # chaine = chaine.replace("&", "\&")
        chaine = latex.nettoie_latex(chaine)

        return chaine


def md_to_latex(contenu):
    """Réalise la conversion markdown to latex avec pypandoc"""
    contenu = contenu.replace(
        "\n", "\n\n"
    )  # corrige les suppressions de ligne à la relecture du yaml

    contenu = pypandoc.convert_text(
        contenu, "tex", format="md", extra_args=["--atx-headers"]
    )
    contenu = contenu.replace("\r\n", "\n")
    lignes = contenu.split("\n\n")  # Détecte les sauts de ligne
    for (i, ligne) in enumerate(lignes):
        if i < len(lignes) - 1:
            if (
                lignes[i].strip().startswith("\\") == False
                and lignes[i].startswith(" ") == False
                and lignes[i + 1].strip().startswith("\\") == False
                and lignes[i + 1].startswith(" ") == False
                and lignes[i].strip().endswith("\\\\") == False
            ):
                lignes[i] = lignes[i] + "\\\\"  # ajoute un passage à la ligne latex
    contenu = "\n\n".join(lignes)

    # contenu = caracteres_recalcitrants(contenu)
    contenu = ressourcedocx.remove_ligne_vide(contenu)
    lignes = contenu.split("\n")  # pour debug

    if contenu.startswith("\\begin{itemize}"):
        contenu = (
            "\\vspace{-10pt}\n" + contenu
        )  # ajout d'un offset en cas de liste à puces
    contenu = contenu.replace("\\\\" * 2, "\\\\[25pt]")
    if not contenu.endswith("\\end{itemize}"):
        contenu += "\\\\[3pt]"

    contenu = ajoute_cmd_latex(contenu)  # détecte les commandes

    return contenu


def get_matrices_ac_ressource(saes, ressources, sem):
    """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie"""
    DATA_ACS = officiel.get_DATA_ACS()
    les_codes_acs = [code for comp in DATA_ACS for code in DATA_ACS[comp]]
    nbre_acs = len(les_codes_acs)

    saesem = saes[sem]  # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
    DATA_SAES = officiel.get_DATA_SAES()
    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])
    if len(saesem) != nbre_saes:
        __LOGGER.warning(f"Pb => il manque des saes au {sem}")
    if len(ressem) != nbre_ressources:
        __LOGGER.warning(f"Pb => il manque des ressources au {sem}")

    matrice = [[False] * (nbre_saes + nbre_ressources) for i in range(nbre_acs)]

    for (i, s) in enumerate(saesem):  # pour chaque SAE
        for comp in s.sae["acs"]:  # pour chaque comp
            for (j, ac) in enumerate(DATA_ACS[comp]):  # pour chaque ac
                if ac in s.sae["acs"][comp]:  # si l'ac est prévue dans la ressource
                    k = les_codes_acs.index(ac)
                    matrice[k][i] = True

    for (i, r) in enumerate(ressem):  # pour chaque ressource
        for comp in r.ressource["acs"]:  # pour chaque comp
            for (j, ac) in enumerate(DATA_ACS[comp]):  # pour chaque ac
                if (
                    ac in r.ressource["acs"][comp]
                ):  # si l'ac est prévue dans la ressource
                    k = les_codes_acs.index(ac)
                    matrice[k][i + nbre_saes] = True
    return matrice


def get_matrices_coeffs(saes, ressources, sem):
    """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie"""
    comps = ["RT1", "RT2", "RT3"]

    saesem = saes[sem]  # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
    DATA_SAES = officiel.get_DATA_SAES()
    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])
    if len(saesem) != nbre_saes:
        __LOGGER.warning(f"Pb => il manque des saes au {sem}")
    if len(ressem) != nbre_ressources:
        __LOGGER.warning(f"Pb => il manque des ressources au {sem}")

    matrice = [[None] * (len(comps)) for i in range(nbre_saes + nbre_ressources)]

    for (i, s) in enumerate(saesem):  # pour chaque SAE
        for (j, comp) in enumerate(comps):  # pour chaque comp
            if comp in s.sae["coeffs"]:
                matrice[i][j] = s.sae["coeffs"][comp]

    for (i, r) in enumerate(ressem):  # pour chaque ressource
        for (j, comp) in enumerate(comps):  # pour chaque comp
            if comp in r.ressource["coeffs"]:  # pour chaque ac
                matrice[i + nbre_saes][j] = r.ressource["coeffs"][comp]
    return matrice


def get_matrices_volumes(saes, ressources, sem):
    """Calcule la matrice AC vs sae + ressource pour un sem donné et la renvoie
    => obsolète ? déplacé dans semestre"""
    saesem = saes[sem]  # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
    DATA_SAES = officiel.get_DATA_SAES()
    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])
    if len(saesem) != nbre_saes:
        __LOGGER.warning(f"Pb => il manque des saes au {sem}")
    if len(ressem) != nbre_ressources:
        __LOGGER.warning(f"Pb => il manque des ressources au {sem}")

    matrice = [[0] * (len(MODALITES)) for i in range(nbre_saes + nbre_ressources)]

    for (i, s) in enumerate(saesem):  # pour chaque SAE
        formation = (
            s.sae["heures_encadrees"]
            if not isinstance(s.sae["heures_encadrees"], str)
            else 0
        )
        tp = s.sae["tp"] if not isinstance(s.sae["tp"], str) else 0
        matrice[i][0] = formation - tp
        matrice[i][1] = tp
        matrice[i][2] = s.sae["projet"] if not isinstance(s.sae["projet"], str) else 0

    for (i, r) in enumerate(ressem):  # pour chaque ressource
        formation = (
            r.ressource["heures_formation"]
            if not isinstance(r.ressource["heures_formation"], str)
            else 0
        )
        tp = (
            r.ressource["heures_tp"]
            if not isinstance(r.ressource["heures_tp"], str)
            else 0
        )
        matrice[i + nbre_saes][0] = formation - tp
        matrice[i + nbre_saes][1] = tp

    return matrice


def str_matrice(matrice, saes, ressources, sem):
    """Renvoie une chaine de caractère affichant la matrice"""
    DATA_ACS = officiel.get_DATA_ACS()
    les_codes_acs = [code for comp in DATA_ACS for code in DATA_ACS[comp]]
    nbre_acs = len(les_codes_acs)

    saesem = saes[sem]  # les saé du semestre
    ressem = ressources[sem]  # les ressources du semestre

    DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
    DATA_SAES = officiel.get_DATA_SAES()
    nbre_saes = len(DATA_SAES[sem])
    nbre_ressources = len(DATA_RESSOURCES[sem])

    chaine = ""
    ligne = "{:20s} | " + "{:5s} | " * (nbre_saes + nbre_ressources)
    valeurs = ("" for i in range(nbre_saes + nbre_ressources + 1))
    trait = "-" * len(ligne.format(*valeurs))

    valeurs = (
        [""]
        + [s.sae["code"] if s.sae["code"] else "????" for s in saesem]
        + [r.ressource["code"] if r.ressource["code"] else "????" for r in ressem]
        + [""] * (nbre_saes - len(saesem) + nbre_ressources - len(ressem))
    )
    valeurs = tuple(valeurs)
    chaine += ligne.format(*valeurs) + "\n" + trait + "\n"
    for (j, ac) in enumerate(les_codes_acs):
        valeurs = [ac] + [
            ("X" if matrice[j][i] == True else "")
            for i in range(nbre_saes + nbre_ressources)
        ]
        valeurs = tuple(valeurs)
        chaine += ligne.format(*valeurs) + "\n"
    chaine += trait + "\n"
    return chaine


def cesure_contenu(contenu, long_max=30):
    chaine = "\\rotatebox[origin=c]{90}{\n"
    chaine += "\\begin{tabular}{ll}\n"
    contenu_cesure = []
    while contenu:
        indice_espace = contenu.find(" ", long_max)
        if indice_espace < 0:
            contenu_cesure.append(contenu)
            contenu = ""
        else:
            contenu_cesure.append(contenu[:indice_espace])
            contenu = contenu[indice_espace + 1 :]
    chaine += " \\\\ ".join(contenu_cesure)
    chaine += "\\end{tabular} }"
    return chaine


def get_total_nbre_heures(matrice_heures):
    """Calcul le nombre d'heures total des SAé d'après la matrice"""
    sommes = [
        sum(
            [
                matrice_heures[i][j]
                for i in range(len(matrice_heures))
                if matrice_heures[i][j]
            ]
        )
        for j in range(3)
    ]
    return sommes


def get_total_nbre_heures_saes(matrice_heures, sem):
    """Calcul le nombre d'heures total des SAé d'après la matrice"""
    DATA_SAES = officiel.get_DATA_SAES()
    nbre_sae = len(DATA_SAES[sem])
    sommes = [
        sum([matrice_heures[i][j] for i in range(nbre_sae) if matrice_heures[i][j]])
        for j in range(3)
    ]
    return sommes


def get_total_nbre_heures_ressources(matrice_heures, sem):
    """Calcul le nombre d'heures total des SAé d'après la matrice"""
    DATA_RESSOURCES = officiel.get_DATA_RESSOURCES()
    nbre_ressources = len(DATA_RESSOURCES[sem])
    sommes = [
        sum(
            [
                matrice_heures[i][j]
                for i in range(nbre_ressources, len(matrice_heures))
                if matrice_heures[i][j]
            ]
        )
        for j in range(3)
    ]
    return sommes


def get_total_coeffs(matrice_coeffs):
    sommes = [
        sum(
            [
                matrice_coeffs[i][j]
                for i in range(len(matrice_coeffs))
                if matrice_coeffs[i][j]
            ]
        )
        for j in range(3)
    ]
    return sommes


def get_total_coeffs_saes(matrice_coeffs, sem):
    DATA_SAES = officiel.get_DATA_SAES()
    nbre_sae = len(DATA_SAES[sem])
    sommes = [
        sum([matrice_coeffs[i][j] for i in range(nbre_sae) if matrice_coeffs[i][j]])
        for j in range(3)
    ]
    return sommes


def get_total_coeffs_ressources(matrice_coeffs, sem):
    DATA_SAES = officiel.get_DATA_SAES()
    nbre_sae = len(DATA_SAES[sem])
    sommes = [
        sum(
            [
                matrice_coeffs[i][j]
                for i in range(nbre_sae, len(matrice_coeffs))
                if matrice_coeffs[i][j]
            ]
        )
        for j in range(3)
    ]
    return sommes


