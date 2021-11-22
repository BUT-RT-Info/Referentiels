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
        # self.competences = self.yaml["competences"]
        self.heures_encadrees = self.yaml["heures_encadrees"]
        self.heures_tp = self.yaml["tp"]
        self.heures_projet = self.yaml["projet"]

    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_sae.tex"):
        """Génère le code latex décrivant la saé en utilisant le template latex donné
        dans ``modele``
        """
        modlatex = modeles.get_modele(modele)  # "templates/modele_ressource.tex")

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
            descriptif = rpn.latex.md_to_latex(descriptif, self.officiel.DATA_MOTSCLES)

        # préparation des livrables
        livrables = self.sae["livrables"]
        if livrables == "Aucun":
            livrables = ""
            SAE.__LOGGER.warning(f"{self.sae['titre']} n'a pas de livrables")
        else:
            livrables = rpn.latex.md_to_latex(livrables, self.officiel.DATA_MOTSCLES)

        chaine = ""
        chaine = modeles.TemplateLatex(modlatex).substitute(
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

        chaine = rpn.latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)
        return chaine