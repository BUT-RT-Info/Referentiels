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
        self.heures_tp = self.yaml["heures_tp"]
        self.heures_projet = self.yaml["projet"]


    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_tableau_sae.tex"):
        """Génère le code latex décrivant la saé en utilisant le template latex donné
        dans ``modele``
        """
        modlatex = modeles.get_modele(modele)  # "templates/modele_ressource.tex")

        # La liste des compétences, des acs (et des coeffs)
        latex_competences = self.to_latex_liste_competences_et_acs()

        # Préparation des ressources
        latex_ressource = self.to_latex_liste_fiches(self.yaml["ressources"])

        # Préparation des objectifs
        objectifs = self.yaml["objectifs"]
        if not objectifs:
            latex_objectifs = ""
        else:
            latex_objectifs = rpn.latex.md_to_latex(objectifs, self.officiel.DATA_MOTSCLES)

        # préparation de la description générique
        descriptif = self.yaml["description"]
        if not descriptif:
            latex_description = "\\textit{Aucun}"
            SAE.__LOGGER.warning(f"{self.nom} n'a pas de description")
        else:
            latex_description = rpn.latex.md_to_latex(descriptif, self.officiel.DATA_MOTSCLES)

        # préparation des livrables
        livrables = self.yaml["livrables"]
        if livrables == "Aucun":
            latex_livrables = ""
            SAE.__LOGGER.warning(f"{self.nom} n'a pas de livrables")
        else:
            latex_livrables = rpn.latex.md_to_latex(livrables, self.officiel.DATA_MOTSCLES)

        # Prépare les parcours
        latex_parcours = ", ".join(self.yaml["parcours"])

        # préparation des exemples
        # A FAIRE

        # Injection dans le template
        chaine = modeles.TemplateLatex(modlatex).substitute(
            codelatex=self.get_code_latex_hyperlink(self.code),
            code=self.code,
            codeRT=self.codeRT,
            nom=rpn.latex.nettoie_latex(self.nom, self.officiel.DATA_ABBREVIATIONS),
            semestre=self.nom_semestre,
            heures_formation=self.yaml["heures_encadrees"],
            heures_tp=self.yaml["heures_tp"],
            heures_projet=self.yaml["projet"],
            parcours=latex_parcours,
            objectifs=rpn.latex.nettoie_latex(latex_objectifs, self.officiel.DATA_ABBREVIATIONS),
            description=rpn.latex.nettoie_latex(latex_description, self.officiel.DATA_ABBREVIATIONS),
            livrables=latex_livrables,
            competences_et_acs=latex_competences,
            listeRessources=latex_ressource,
            motsCles=rpn.latex.nettoie_latex(self.yaml["motscles"] + ".", self.officiel.DATA_ABBREVIATIONS),
            # listeExemples = A FAIRE
        )
        # chaine = chaine.replace("&", "\&")
        return chaine

    def to_variable_latex(self, modele=Config.ROOT + "/python/templates/modele_sae.tex"):
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

        objectifs = self.yaml["objectifs"]
        if not objectifs:
            objectifs = "Aucun"
        objectifs = rpn.latex.md_to_latex(objectifs, self.officiel.DATA_MOTSCLES)

        # préparation de la description générique
        descriptif = self.yaml["description"]
        if not descriptif:
            descriptif = "Aucun"
            SAE.__LOGGER.warning(f"{self.nom} n'a pas de description")
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
            objectifs=objectifs,
            description=descriptif,
            ressources=ressources,
            livrables=livrables,
            motscles=self.yaml["motscles"] + ".",
        )
        # chaine = chaine.replace("&", "\&")

        chaine = rpn.latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)
        return chaine