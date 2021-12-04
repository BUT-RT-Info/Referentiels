import logging

from ruamel.yaml.scalarstring import FoldedScalarString as folded

import rofficiel.officiel
import rdocx.docx
import rofficiel.activites
import tools


class RessourceDocx(rdocx.docx.Docx):
    """Classe modélisant les ressources, lorsqu'elles sont extraites du rdocx"""
    __LOGGER = logging.getLogger(__name__)


    def charge_informations(self, codeRT, semestre,
                            heures_encadrees, tp, cm, td,
                            adapation_locale,
                            sae, prerequis,
                            description, mots, parcours,
                            exemple):
        """Charge les informations lues de la fiche docx (et parsées par parsedocx)"""
        self.codeRT = codeRT.strip()
        self.semestre = semestre # <--

        self.heures_encadrees = heures_encadrees
        self.details_heures_encadrees = {'cm': cm, 'td': td, 'tp': tp}

        self.adaptation_locale = adapation_locale

        self.saes = sae
        self.prerequis = prerequis
        self.desc = description # la description avant d'être slitée dans self.description
        ## pour les ressources
        self.description = {"contexte": [],
                            "contenus": [],
                            "prolongements": []}

        self.mots = mots
        self.parcours = parcours
        self.exemple = exemple


    def nettoie_code(self):
        """Recherche le code de la forme RXXX => ne sert plus qu'à vérifier le mapping"""
        if self.codeRT:
            codes = rdocx.docx.devine_ressources_by_code_RXXX(self.codeRT)
            codes += rdocx.docx.devine_ressource_by_code_RPXX(self.codeRT)

            if len(codes) == 1: # 1 code deviné
                if codes[0] != self.codeRT:
                    raise Exception(f"Probleme dans le mapping {self.code} <-> {self.codeRT}")
            else:
                code_devine = rofficiel.officiel.get_code_from_nom_using_dict(self.nom, self.officiel.DATA_RESSOURCES)

                if code_devine:
                    RessourceDocx.__LOGGER.warning(f"nettoie_code : \"{self.nom}\" => code {code_devine}")
                    if code_devine != self.code:
                        raise Exception(f"Probleme dans le mapping de {self.code} <-> {self.codeRT}")

        if not self.codeRT:
            RessourceDocx.__LOGGER.warning("{self.code}: nettoie_code: code/libellé court manquant")


    def nettoie_prerequis(self):
        """Nettoie les prérequis"""
        if not self.prerequis or rofficiel.officiel.AUCUN_PREREQUIS.lower() in self.prerequis.lower():
            self.prerequis = rofficiel.officiel.AUCUN_PREREQUIS
        else:
            ressources = self.nettoie_liste_ressources(self.prerequis)
            if ressources:
                self.prerequis = ressources


    def nettoie_sae(self):
        """Nettoie le champ SAe d'une ressource en détectant les codes"""
        liste = self.saes
        self.saes = self.nettoie_liste_sae(liste)
        if not self.saes:
            self.__LOGGER.warning(f"{self}: nettoie_sae:  pas de SAE (:")


    def nettoie_heures_encadrees_et_tp(self):
        """Nettoie le champ (horaire) (de la forme 46h ou 33...) pour en extraire la valeur numérique :
        le champ peut contenir 2 volumes (heures formation puis heures tp), auquel cas les 2 valeurs sont renvoyées
        dans un tuple"""
        volumes = None
        if self.heures_encadrees:  # si les heures encadrées sont renseignées
            volumes = self.nettoie_champ_heure(self.heures_encadrees)

        if isinstance(volumes, int):
            self.heures_encadrees = volumes
        elif isinstance(volumes, tuple):
            self.heures_encadrees = volumes[0]
            if not self.details_heures_encadrees["tp"]:
                self.details_heures_encadrees["tp"] = volumes[1]
                RessourceDocx.__LOGGER.warning(f"{self}: nettoie_heure: injection heures de heures encadrées dans heures tp")
            elif self.details_heures_encadrees["tp"] != volumes[1]:
                RessourceDocx.__LOGGER.warning(f"{self}: nettoie_heure: pb dans les heures tp")
        else:
            self.heures_encadrees = None


    def split_description(self):
        """Découpe le champ description en contexte/contenu/prolongement;
        si pas possible place dans contenu"""
        # if self.code == "R110":
        #    print("ici")
        description = {**self.description, "objectifs": []} # copie du dictionnaire description

        lignes = self.desc.split("\n")
        lignes = [c for c in lignes if c]  # supprime les lignes vides

        indices = {cle: -1 for cle in description}
        for id in description:
            presence = [ligne.lower().startswith(id) for ligne in lignes]
            if True in presence: # la ligne commençant par l'identifiant
                indices[id] = presence.index(True)

        champs_ordonnes = sorted(indices, key=lambda cle: indices[cle]) # tri par indice croissant

        # -1 -1 -1 -1 => tout dans contenu
        if list(indices.values()).count(-1) == 4:
            description["contenus"] = lignes[:]
        # sinon 1 marqueur a été trouvé
        else:
            for (i, cle) in enumerate(champs_ordonnes):
                if indices[cle] >= 0: # si la clé est trouvée
                    if i < len(champs_ordonnes) -1: # pas le dernier champ
                        champ_suivant = champs_ordonnes[i+1]
                        description[cle] = lignes[indices[cle]+1:indices[champ_suivant]]
                    else:
                        description[cle] = lignes[indices[cle]+1:]

        # suppression des lignes vides
        for cle in description:
            lignes_conservees = tools.remove_ligne_vide(description[cle])
            chaine = "\n".join(lignes_conservees)
            description[cle] = rdocx.docx.remove_link(chaine)
            if not description[cle]:
                self.__LOGGER.warning(f"{self}: nettoie_description: description > {cle} manquant")
        # sauvegarde
        self.description = {"contexte": description["contexte"],
                            "contenus": description["contenus"] + description["objectifs"],
                            "prolongements": description["prolongements"]}


    def nettoie_champs(self):
        """Lance le nettoyage des champs"""
        self.nettoie_code()
        self.nettoie_semestre()
        self.annee = rofficiel.officiel.Officiel.get_annee_from_semestre(self.semestre)

        self.nettoie_titre(self.officiel.DATA_RESSOURCES)

        for type in ["cm", "td", "tp"]:
            self.details_heures_encadrees[type] = self.nettoie_heures_cm_td(self.details_heures_encadrees, type)
        self.nettoie_heures_encadrees_et_tp()
        self.nettoie_heures_cm_td()
        self.nettoie_adaptation_locale()



        self.nettoie_acs()
        self.nettoie_competences()
        self.compare_acs_competences()

        self.nettoie_sae()
        self.nettoie_prerequis()
        self.nettoie_mots_cles()
        self.nettoie_coeffs()
        self.parcours = self.nettoie_parcours(self.parcours)

        # Remet en forme le descriptif
        self.split_description()
        self.nettoie_description()
        # print(f"{self.code} {self.semestre}")
        self.nettoie_exemple()


    def nettoie_exemple(self):
        """Nettoie l'exemple de mise en oeuvre"""
        contenu = self.exemple
        if not contenu:
            self.exemple = ""
        else:
            contenu = tools.remove_ligne_vide(contenu)  # supprime les ligne vides
            contenu_md = rdocx.docx.convert_to_markdown(contenu)
            contenu_md = self.nettoie_codes_dans_champ(contenu_md)
            self.exemple = contenu_md

    def to_yaml(self):
        """Exporte la ressource en yaml"""
        # prépare le champ description (fusion de contexte/objectifs/contenu/prolongements)
        dico = {"nom": self.nom,
                "code": self.code,
                "codeRT": self.codeRT,
                "libelle": self.codeRT,  # A revoir
                "url": folded(self.url),
                "semestre" : int(self.semestre),
                "annee": self.annee,
                "parcours": self.parcours,
                "heures_formation": self.heures_encadrees if self.heures_encadrees else "???",
                "details_heures_formation": self.prepare_heures_yaml(self.details_heures_encadrees),
                "heures_formation_pn": self.heures_encadrees_pn if self.heures_encadrees_pn else "???",
                "details_heures_formation_pn": self.prepare_heures_yaml(self.details_heures_encadrees_pn),
                "tableur_heures_formation": self.prepare_heures_yaml(self.tableur_heures_formation),
                "tableur_heures_formation_pn": self.prepare_heures_yaml(self.tableur_heures_formation_pn),
                "adaptation_locale": "oui" if self.adaptation_locale.lower() == "oui" else "non",
                "coeffs": self.coeffs,
                "competences": self.competences,
                "acs": self.acs,
                "sae": self.saes,
                "prerequis": self.prerequis,
                "contexte": folded(self.description["contexte"]) if self.description["contexte"] else "Aucun",
                "contenus": folded(self.description["contenus"]) if self.description["contenus"] else "Aucun",
                "prolongements": folded(self.description["prolongements"]) if self.description["prolongements"] else "",
                "motscles": self.mots if self.mots else "",
                "exemple": folded(self.exemple)
                }
        return self.dico_to_yaml(dico)


