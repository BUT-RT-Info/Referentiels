import ruamel.yaml
from config import Config
import latex
from activitedocx import *

__LOGGER = logging.getLogger(__name__)

MODALITES = ["CM/TD", "TP", "Projet"]   # modalités de mise en oeuvre d'une ressource/SAE


class ActivitePedagogique():
    """Modélise les éléments de bases d'une activité pédagogique (ressource, SAE ou exemple
    de SAE) et stocke les données officielles.

    Une *activité pédagogique* est initialisée par lecture des données contenues dans fichier yaml (attribut yaml).
    Ses attributs sont :

    * ``yaml`` : le dictionnaire lu dans le fichier yaml décrivant l'activité
    * ``code`` : le code de l'activité (par ex: ``"R101"`` ou ``"SAE12"``)
    * ``nom_semestre`` : le nom du semestre où se tient l'activité (par ex: ``"S1"``)
    * ``numero_semestre`` : le numéro du semestre où se tient l'activité (1, 2, ..., 6)
    * ``officiel`` : les données officielles du templates (cf. module ``officiel``)
    """
    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, pnofficiel):
        """
        Charge les données du ``fichieryaml``
        """
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
    """Modélise une ressource."""

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        """Initialise les informations sur la ressource à partir du ``fichieryaml``
        et stocke les données ``officiel``les
        """
        super().__init__(fichieryaml, officiel)
        self.ressource = self.yaml
        self.heures_encadrees = self.yaml["heures_formation"]
        self.heures_tp = self.yaml["heures_tp"]
        self.heures_projet = 0

    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_ressource.tex"):
        """Génère le code latex décrivant la ressource, en utilisant le template
        latex donné dans ``modele``.
        """
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
                ajoutsaes % (sae, self.officiel.get_sae_name_by_code(sae))
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
                        ajoutprerequis % (mod, self.officiel.get_ressource_name_by_code(mod))
                    )
                prerequis = "\n".join(liste)

        # préparation du contexte
        contexte = self.ressource["contexte"]
        if contexte == "Aucun":
            contexte = ""
            Ressource.__LOGGER.warning(f"{self.ressource['nom']} n'a pas de contexte")

        else:
            contexte = latex.md_to_latex(contexte, self.officiel.DATA_MOTSCLES)

        # contexte = remove_ligne_vide(contexte)
        # préparation du contenu

        contenu = self.ressource["contenu"]  # supprime les passages à la ligne

        if contenu:
            if self.ressource["code"] == "R112":
                print("ici")
            contenu = latex.md_to_latex(contenu, self.officiel.DATA_MOTSCLES)

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




class SAE(ActivitePedagogique):
    """Modélise une SAé (chapeau) en chargeant les données provenant du ``fichieryaml``
    et stocke les données ``officiel``les.
    """

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        super().__init__(fichieryaml, officiel)
        self.sae = self.yaml
        self.heures_encadrees = self.yaml["heures_encadrees"]
        self.heures_tp = self.yaml["tp"]
        self.heures_projet = self.yaml["projet"]

    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_sae.tex"):
        """Génère le code latex décrivant la saé en utilisant le template latex donné
        dans ``modele``
        """
        modlatex = get_modele(modele)  # "templates/modele_ressource.tex")

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
            descriptif = latex.md_to_latex(descriptif, self.officiel.DATA_MOTSCLES)

        # préparation des livrables
        livrables = self.sae["livrables"]
        if livrables == "Aucun":
            livrables = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de livrables")
        else:
            livrables = latex.md_to_latex(livrables, self.officiel.DATA_MOTSCLES)

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
    """Modélise un exemple de SAE en chargeant les données de ``fichieryaml``
    et stocke les données ``officiel``.
    """

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        super().__init__(fichieryaml, officiel)
        self.exemple = self.yaml

    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_exemple_sae.tex"):
        """Génère le code latex décrivant l'exemple de SAE en utilisant le template
        donné dans ``modele``
        """
        modlatex = get_modele(modele)  # "templates/modele_ressource.tex")

        # préparation du descriptif
        description = self.exemple["description"]
        if not description:
            description = ""
            ExempleSAE.__LOGGER.warning(
                f"{self.exemple['titre']} n'a pas de description"
            )
        else:
            description = latex.md_to_latex(description, self.officiel.DATA_MOTSCLES)


        # préparation de la forme
        formes = self.exemple["formes"]
        if not formes:
            formes = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de formes")
        else:
            formes = latex.md_to_latex(formes, self.officiel.DATA_MOTSCLES)

        # préparation de la problématique
        problematique = self.exemple["problematique"]
        if not problematique:
            problematique = ""
            ExempleSAE.__LOGGER.warning(
                f"{self.exemple['titre']} n'a pas de problematique"
            )
        else:
            problematique = latex.md_to_latex(problematique, self.officiel.DATA_MOTSCLES)
            if "15" in self.exemple["code"]:
                # supprime le \\[3pt]
                problematique = problematique[:-7]

        # préparation des modalites
        modalite = self.exemple["modalite"]
        if not modalite:
            modalite = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de modalite")
        else:
            modalite = latex.md_to_latex(modalite, self.officiel.DATA_MOTSCLES)

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


