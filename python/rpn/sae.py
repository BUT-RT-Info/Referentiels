import logging

import rpn.latex
from config import Config
import rpn.activite
import modeles, officiel

class SAE(rpn.activite.ActivitePedagogique):
    """Modélise une SAé (chapeau) en chargeant les données provenant du ``fichieryaml``
    et stocke les données ``officiel``les.
    """

    __LOGGER = logging.getLogger(__name__)

    def __init__(self, fichieryaml, officiel):
        super().__init__(fichieryaml, officiel)
        self.acs = self.yaml["acs"]
        self.nom = self.yaml["titre"]
        # self.competences = self.yaml["competences"]
        self.annee = self.yaml["annee"]
        self.heures_encadrees = self.yaml["heures_encadrees"]
        self.heures_tp = self.yaml["tp"]
        self.heures_projet = self.yaml["projet"]

    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_sae.tex"):
        """Génère le code latex décrivant la saé en utilisant le template latex donné
        dans ``modele``
        """
        modlatex = modeles.get_modele(modele)  # "templates/modele_ressource.tex")

        # La liste des compétences, des acs (et des coeffs)
        competences = self.to_latex_competences_et_acs("sae")

        # Préparation des ressources
        ajoutressources = "\\ajoutSressources{%s}{%s}"
        resRT = []
        for (i, res) in enumerate(
            self.yaml["ressources"]
        ):  # in range(len(self.apprentissages)):
            resRT.append(
                ajoutressources % (res, self.officiel.get_ressource_name_by_code(res))
            )
        ressources = "\n".join(resRT)

        # préparation du descriptif
        descriptif = self.yaml["description"]
        if descriptif == "Aucun":
            descriptif = ""
            SAE.__LOGGER.warning(f"{self.nom} n'a pas de description")
        else:
            descriptif = rpn.latex.md_to_latex(descriptif, self.officiel.DATA_MOTSCLES)

        # préparation des livrables
        livrables = self.yaml["livrables"]
        if livrables == "Aucun":
            livrables = ""
            SAE.__LOGGER.warning(f"{self.nom} n'a pas de livrables")
        else:
            livrables = rpn.latex.md_to_latex(livrables, self.officiel.DATA_MOTSCLES)

        chaine = ""
        chaine = modeles.TemplateLatex(modlatex).substitute(
            code=self.code,
            codeRT=self.codeRT,
            titre=self.nom,
            competences_et_ACs="\n".join(competences),
            heures_encadrees=self.yaml["heures_encadrees"],
            heures_tp=self.yaml["tp"],
            heures_projet=self.yaml["projet"],
            description=descriptif,
            ressources=ressources,
            livrables=livrables,
            motscles=self.yaml["motscles"] + ".",
        )
        # chaine = chaine.replace("&", "\&")

        chaine = rpn.latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)
        return chaine