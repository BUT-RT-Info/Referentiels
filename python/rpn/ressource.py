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
        self.nom = self.yaml["nom"]
        self.acs = self.yaml["acs"]
        self.annee = self.yaml["annee"]
        # self.competences = self.yaml["competences"]
        self.heures_encadrees = self.yaml["heures_formation"]
        self.heures_tp = self.yaml["heures_tp"]
        self.heures_projet = 0

    def to_latex(self, modele=Config.ROOT + "/python/templates/modele_ressource.tex"):
        """Génère le code latex décrivant la ressource, en utilisant le template
        latex donné dans ``modele``.
        """
        modlatex = modeles.get_modele(modele)


        # Préparation des compétences, des ACs et des coeffs \ajoutRcomp + \ajoutRcoeff + boucle \ajoutRacs
        competences = self.to_latex_competences_et_acs("ressource")

        # Préparation des sae
        ajoutsaes = "\\ajoutRsae{%s}{%s}"  # nom, intitule, code_latex
        saesRT = []
        for (i, sae) in enumerate(
            self.yaml["sae"]
        ):  # in range(len(self.apprentissages)):
            code_latex = (
                string.ascii_uppercase[int(sae[-2]) - 1]
                + string.ascii_uppercase[int(sae[-1]) - 1]
            )
            saesRT.append(
                ajoutsaes % (sae, self.officiel.get_sae_name_by_code(sae))
            )  # , code_latex))
        saes = "\n".join(saesRT)

        prerequis = ""
        if self.yaml["prerequis"] == officiel.AUCUN_PREREQUIS:
            prerequis = ""
        else:
            # est-une liste de ressources
            if not self.yaml["prerequis"][0].startswith("R"):
                prerequis = "\\ajoutRprerequislycee{%s}" % (self.yaml["prerequis"])
            else:
                ajoutprerequis = "\\ajoutRprerequis{%s}{%s}"
                liste = []
                for (no, mod) in enumerate(self.yaml["prerequis"]):
                    liste.append(
                        ajoutprerequis % (mod, self.officiel.get_ressource_name_by_code(mod))
                    )
                prerequis = "\n".join(liste)

        # préparation du contexte
        contexte = self.yaml["contexte"]
        if contexte == "Aucun":
            contexte = ""
            Ressource.__LOGGER.warning(f"{self.yaml['nom']} n'a pas de contexte")

        else:
            contexte = rpn.latex.md_to_latex(contexte, self.officiel.DATA_MOTSCLES)

        # contexte = remove_ligne_vide(contexte)
        # préparation du contenu
        contenu = self.yaml["contenu"]  # supprime les passages à la ligne

        if contenu:
            contenu = rpn.latex.md_to_latex(contenu, self.officiel.DATA_MOTSCLES)

        chaine = ""
        chaine = modeles.TemplateLatex(modlatex).substitute(
            code=self.code,
            codeRT=self.codeRT,
            nom=self.nom,
            heures_formation=self.yaml["heures_formation"],
            heures_tp=self.yaml["heures_tp"],
            competences_et_ACs="\n".join(competences), # les compétences
            saes=saes,
            motscles=self.yaml["motscles"] + ".",
            prerequis=prerequis,
            contexte=contexte,
            contenu=contenu,
        )
        # chaine = chaine.replace("&", "\&")
        chaine = rpn.latex.nettoie_latex(chaine, self.officiel.DATA_ABBREVIATIONS)

        # Insère les abbréviations
        return chaine