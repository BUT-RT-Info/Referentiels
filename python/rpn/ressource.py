import logging

import rpn.latex
from config import Config
import rpn.activite
import modeles, string, officiel


class Ressource(rpn.activite.ActivitePedagogique):
    """Modélise une ressource."""

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        """Initialise les informations sur la ressource à partir du ``fichieryaml``
        et stocke les données ``officiel``les
        """
        super().__init__(fichieryaml, officiel)
        self.acs = self.yaml["acs"]
        # self.competences = self.yaml["competences"]
        self.heures_encadrees = self.yaml["heures_formation"]
        self.heures_tp = self.yaml["heures_tp"]
        self.heures_projet = 0

    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_ressource.tex"):
        """Génère le code latex décrivant la ressource, en utilisant le template
        latex donné dans ``modele``.
        """
        modlatex = modeles.get_modele(modele)

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
            contexte = rpn.latex.md_to_latex(contexte, self.officiel.DATA_MOTSCLES)

        # contexte = remove_ligne_vide(contexte)
        # préparation du contenu

        contenu = self.ressource["contenu"]  # supprime les passages à la ligne

        if contenu:
            if self.ressource["code"] == "R112":
                print("ici")
            contenu = rpn.latex.md_to_latex(contenu, self.officiel.DATA_MOTSCLES)

        chaine = ""
        chaine = modeles.TemplateLatex(modlatex).substitute(
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
        chaine = rpn.latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)

        # Insère les abbréviations
        return chaine