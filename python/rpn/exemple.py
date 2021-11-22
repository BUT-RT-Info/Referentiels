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
        self.exemple = self.yaml

    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_exemple_sae.tex"):
        """Génère le code latex décrivant l'exemple de SAE en utilisant le template
        donné dans ``modele``
        """
        modlatex = modeles.get_modele(modele)  # "templates/modele_ressource.tex")

        # préparation du descriptif
        description = self.exemple["description"]
        if not description:
            description = ""
            ExempleSAE.__LOGGER.warning(
                f"{self.exemple['titre']} n'a pas de description"
            )
        else:
            description = rpn.latex.md_to_latex(description, self.officiel.DATA_MOTSCLES)


        # préparation de la forme
        formes = self.exemple["formes"]
        if not formes:
            formes = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de formes")
        else:
            formes = rpn.latex.md_to_latex(formes, self.officiel.DATA_MOTSCLES)

        # préparation de la problématique
        problematique = self.exemple["problematique"]
        if not problematique:
            problematique = ""
            ExempleSAE.__LOGGER.warning(
                f"{self.exemple['titre']} n'a pas de problematique"
            )
        else:
            problematique = rpn.latex.md_to_latex(problematique, self.officiel.DATA_MOTSCLES)
            if "15" in self.exemple["code"]:
                # supprime le \\[3pt]
                problematique = problematique[:-7]

        # préparation des modalites
        modalite = self.exemple["modalite"]
        if not modalite:
            modalite = ""
            ExempleSAE.__LOGGER.warning(f"{self.exemple['titre']} n'a pas de modalite")
        else:
            modalite = rpn.latex.md_to_latex(modalite, self.officiel.DATA_MOTSCLES)

        chaine = ""
        chaine = modeles.TemplateLatex(modlatex).substitute(
            titre=self.exemple["titre"],
            description=description,
            formes=formes,
            problematique=problematique,
            modalite=modalite,
        )
        # chaine = chaine.replace("&", "\&")
        chaine = rpn.latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)

        return chaine