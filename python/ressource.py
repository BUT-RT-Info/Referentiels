import pypandoc
import ruamel.yaml

import latex
from ressourcedocx import *

__LOGGER = logging.getLogger(__name__)

MODALITES = ["CM/TD", "TP", "Projet"]   # modalités de mise en oeuvre d'une ressource/SAE


class ActivitePedagogique():
    """Modélise les éléments de bases d'une activité pédagogique (ressource ou SAE).
    Classe servant de base à l'héritage.

    Une activité pédagogique est initialisée par lecture des données contenues dans fichier yaml (attribut yaml)
    """
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, pnofficiel):
        """Charge les données du fichier yaml"""
        with open(fichieryaml, "r", encoding="utf8") as fid:
            yaml = ruamel.yaml.YAML()
            try:
                self.yaml = yaml.load(fid.read())
            except:
                ActivitePedagogique.__LOGGER.warning(f"Pb de chargement de {fichieryaml}")
        # Rappatrie les infos communes (code/titre)
        self.code = self.yaml["code"]
        self.numero_semestre = self.yaml["semestre"]
        self.nom_semestre = "S" + str(self.numero_semestre)

        # Charges les données officielles
        self.officiel = pnofficiel


class Ressource(ActivitePedagogique):
    """Modélise une ressource lorsqu'elle est extraite d'un fichier yaml"""

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        super().__init__(fichieryaml, officiel)
        self.ressource = self.yaml

    def to_latex(self, modele=Config.ROOT + "/python/pn/modele_ressource.tex"):
        """Génère le code latex décrivant la ressource"""
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
        ajoutac = "\\ajoutRac{%s}{%s}"
        compRT = []
        for accomp in ["RT1", "RT2", "RT3"]:
            comps = []
            if accomp in self.ressource["acs"]:
                for no_ac in range(
                    len(self.ressource["acs"][accomp])
                ):  # les ac de la comp
                    code_ac = self.ressource["acs"][accomp][no_ac]
                    comps.append(ajoutac % (code_ac, self.officiel.DATA_ACS[accomp][code_ac]))
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
                ajoutsaes % (sae, self.officiel.get_sem_sae_by_code(sae))
            )  # , code_latex))
        saes = "\n".join(saesRT)

        if self.ressource["code"] == "R110":
            print("ici")
        prerequis = ""
        if self.ressource["prerequis"] == AUCUN_PREREQUIS:
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
                        ajoutprerequis % (mod, self.officiel.get_ressource_name_by_code(mod))
                    )
                prerequis = "\n".join(liste)

        # préparation du contexte
        contexte = self.ressource["contexte"]
        if contexte == "Aucun":
            contexte = ""
            Ressource.__LOGGER.warning(f"{self.ressource['nom']} n'a pas de contexte")

        else:
            contexte = md_to_latex(contexte, self.officiel.DATA_MOTSCLES)

        # contexte = remove_ligne_vide(contexte)
        # préparation du contenu

        contenu = self.ressource["contenu"]  # supprime les passages à la ligne

        if contenu:
            if self.ressource["code"] == "R112":
                print("ici")
            contenu = md_to_latex(contenu, self.officiel.DATA_MOTSCLES)

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
        chaine = latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)

        # Insère les abbréviations
        return chaine


def contient_commandes(chaine, DATA_MOTSCLES):
    """Détecte si la `chaine` est une commande (éventuellement avec un caractère
    de ponctuation final)"""
    chaine_texte = ""
    for car in chaine:
        if car in string.ascii_lowercase + "-":
            chaine_texte += car
    if "ipc" in chaine:
        print("ici")
    if chaine_texte in DATA_MOTSCLES["commandes"]:
        return chaine_texte
    return None


def ajoute_cmd_latex(chaine, DATA_MOTSCLES):
    """
    Parse la chaine latex pour ajouter les abbréviations et les remplacer par
    \\textabbrv{abreviation}
    """
    mots = chaine.split(" ")
    for (i, mot) in enumerate(mots):
        champs = mot.split("\n")
        for (j, champ) in enumerate(champs):
            cmd = contient_commandes(champ, DATA_MOTSCLES)
            if cmd:
                champs[j] = champs[j].replace(cmd, "\\texttt{" + cmd + "}")
        mots[i] = "\n".join(champs)
    chaine = " ".join(mots)
    return chaine


class SAE(ActivitePedagogique):
    """Modélise une SAé (chapeau) lorsqu'elle est extraite d'un yaml"""

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        super().__init__(fichieryaml, officiel)
        self.sae = self.yaml

    def to_latex(self, modele=Config.ROOT + "/python/pn/modele_sae.tex"):
        """Génère le code latex décrivant la ressource"""
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
        for accomp in ["RT1", "RT2", "RT3"]:
            comps = []
            if accomp in self.sae["acs"]:
                for no_ac in range(len(self.sae["acs"][accomp])):  # les ac de la comp
                    code_ac = self.sae["acs"][accomp][no_ac]
                    comps.append(ajoutac % (code_ac, self.officiel.DATA_ACS[accomp][code_ac]))

            compRT.append("\n".join(comps))

        # Préparation des ressources
        ajoutressources = "\\ajoutSressources{%s}{%s}"
        resRT = []
        for (i, res) in enumerate(
            self.sae["ressources"]
        ):  # in range(len(self.apprentissages)):
            resRT.append(
                ajoutressources % (res, self.officiel.get_ressource_name_by_code(res))
            )
        ressources = "\n".join(resRT)

        # préparation du descriptif
        descriptif = self.sae["description"]
        if descriptif == "Aucun":
            descriptif = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de description")
        else:
            descriptif = md_to_latex(descriptif, self.officiel.DATA_MOTSCLES)

        # préparation des livrables
        livrables = self.sae["livrables"]
        if livrables == "Aucun":
            livrables = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de livrables")
        else:
            livrables = md_to_latex(livrables, self.officiel.DATA_MOTSCLES)

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

        chaine = latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)
        return chaine


class ExempleSAE(ActivitePedagogique):
    """Modélise un exemple de SAE lorsqu'elle est extraite d'un yaml"""

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        super().__init__(fichieryaml, officiel)
        self.exemple = self.yaml

    def to_latex(self, modele=Config.ROOT + "/python/pn/modele_exemple_sae.tex"):
        """Génère le code latex décrivant la ressource"""
        modlatex = get_modele(modele)  # "pn/modele_ressource.tex")

        # préparation du descriptif
        description = self.exemple["description"]
        if not description:
            description = ""
            ExempleSAE.__LOGGER.warning(
                f"{self.exemple['titre']} n'a pas de description"
            )
        else:
            description = md_to_latex(description, self.officiel.DATA_MOTSCLES)


        # préparation de la forme
        formes = self.exemple["formes"]
        if not formes:
            formes = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de formes")
        else:
            formes = md_to_latex(formes, self.officiel.DATA_MOTSCLES)

        # préparation de la problématique
        problematique = self.exemple["problematique"]
        if not problematique:
            problematique = ""
            ExempleSAE.__LOGGER.warning(
                f"{self.exemple['titre']} n'a pas de problematique"
            )
        else:
            problematique = md_to_latex(problematique, self.officiel.DATA_MOTSCLES)
            if "15" in self.exemple["code"]:
                # supprime le \\[3pt]
                problematique = problematique[:-7]

        # préparation des modalites
        modalite = self.exemple["modalite"]
        if not modalite:
            modalite = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de modalite")
        else:
            modalite = md_to_latex(modalite, self.officiel.DATA_MOTSCLES)

        chaine = ""
        chaine = TemplateLatex(modlatex).substitute(
            titre=self.exemple["titre"],
            description=description,
            formes=formes,
            problematique=problematique,
            modalite=modalite,
        )
        # chaine = chaine.replace("&", "\&")
        chaine = latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)

        return chaine


def md_to_latex(contenu, DATA_MOTSCLES):
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
    contenu = remove_ligne_vide(contenu)
    lignes = contenu.split("\n")  # pour debug

    if contenu.startswith("\\begin{itemize}"):
        contenu = (
            "\\vspace{-10pt}\n" + contenu
        )  # ajout d'un offset en cas de liste à puces
    contenu = contenu.replace("\\\\" * 2, "\\\\[25pt]")
    if not contenu.endswith("\\end{itemize}"):
        contenu += "\\\\[3pt]"

    contenu = ajoute_cmd_latex(contenu, DATA_MOTSCLES)  # détecte les commandes

    return contenu


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


