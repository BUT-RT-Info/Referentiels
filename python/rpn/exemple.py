import logging

import rpn.latex, modeles
from config import Config
import rpn.activite


class ExempleSAE(rpn.activite.ActivitePedagogique):
    """Modélise un exemple de SAE en chargeant les données de ``fichieryaml``
    et stocke les données ``officiel``.
    """

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        super().__init__(fichieryaml, officiel)
        self.nom = self.yaml["titre"]


    def get_titre_numerote(self, numero, option=None):
        """Renvoie un titre numéroté de la forme Exemple X : titre (ou Exemple X si pas de titre)"""
        intitule = "Exemple %d" % (numero)
        if option == "hyperlink":
            titre = "\\hyperlink{%s%d}{%s}" % (self.get_code_latex_hyperlink(self.code), numero, intitule)
        elif option == "hypertarget":
            titre = "\\hypertarget{%s%d}{%s}" % (self.get_code_latex_hyperlink(self.code), numero, intitule)
        else:
            titre = intitule
        if self.nom:
            titre += " : " + self.nom
        return titre


    def to_latex(self, numero,
                 modele=Config.ROOT + "/python/templates/modele_tableau_exemple.tex"):
        """Génère le code latex décrivant un exemple de SAE en utilisant le template
        donné dans ``modele``
        """
        modlatex = modeles.get_modele(modele)  # "templates/modele_ressource.tex")

        # préparation du titre
        titre = "{\\bfseries " + self.get_titre_numerote(numero, option="hypertarget") + "}"

        # préparation du descriptif
        description = self.prepare_description()

        chaine = ""
        chaine = modeles.TemplateLatex(modlatex).substitute(
            titre=titre,
            description=rpn.latex.nettoie_latex(description, self.officiel.DATA_ABBREVIATIONS),
        )
        # chaine = chaine.replace("&", "\&")

        return chaine

    def prepare_description(self):
        """Prépare la description"""

        # préparation de la problématique
        latex_problematique = self.to_latex_champ_titre("Problématique professionnelle", self.yaml["problematique"])

        description = self.yaml["description"]
        latex_description = ""
        if description:
            latex_description = rpn.latex.md_to_latex(description, self.officiel.DATA_MOTSCLES)

        # préparation de la forme -> inutilisé
        formes = self.yaml["formes"]
        if formes:
            champs_formes = []
            champs_formes.append("")
            formes = rpn.latex.md_to_latex(formes, self.officiel.DATA_MOTSCLES)

        # préparation des modalites
        latex_modalite = self.to_latex_champ_titre("Modalités d'évaluation", self.yaml["modalite"])

        if not latex_modalite and not latex_problematique:
            return latex_description
        else:
            champs = []
            if latex_problematique:
                champs.append(latex_problematique)
            latex_description = self.to_latex_champ_titre("Description", self.yaml["description"])
            champs.append(latex_description)
            if latex_modalite:
                champs.append(latex_modalite)
            return "\n\n\\vspace{0.2cm}\n".join(champs)