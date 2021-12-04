from rofficiel.competences import ACs
from rofficiel.officiel import get_DATA_R_DOCX, __LOGGER


def mapping_code_RXXX_vers_code_pointe(code):
    """Renvoie le code d'une ressource en utilisant le mapping"""
    code_clean = code.lower().replace(".", "").replace(" ", "").replace("é", "e")
    DATA_R_DOCX = get_DATA_R_DOCX()
    for sem in DATA_R_DOCX:
        for mod in DATA_R_DOCX[sem]:
            if DATA_R_DOCX[sem][mod].lower().startswith(code_clean):
                return mod
    __LOGGER.warning(f"Pb: Le code {code} n'a pas pu être mappé en RX.XX")

def mapping_code_SAEXX_vers_code_pointe(code):
    """Renvoie le code d'une sae en utilisant le mapping"""
    code_clean = code.lower().replace(".", "").replace(" ", "").replace("é", "e").replace("-", "")
    DATA_R_DOCX = get_DATA_R_DOCX()
    for sem in DATA_R_DOCX:
        for mod in DATA_R_DOCX[sem]:
            if DATA_R_DOCX[sem][mod].lower().replace("-", "").startswith(code_clean):
                return mod
    __LOGGER.warning(f"Pb: Le code {code} n'a pas pu être mappé en SAEX.X")

def mapping_code_AC0XXX_vers_code_pointe(code):
    """Réalise le mapping d'un AC avec l'ancien systeme de numeroration
    vers le nouveau :
    ancien : AC0can ou ACcan avec c=n° de la compétence, a=annee, n=numero
    nouveau : ACac.0n avec a=annee, c=competence, n=numero"""
    if len(code) == 6: # supprime le 0 très certainement en trop
        if "AC0" in code or "AC1" in code:
            code = "AC" + code[3:]
        else:
            raise Exception("Décodage de l'AC non prévu")
    elif len(code) != 5:
        raise Exception("Décodage de l'AC non prévu")
    comp, annee, numero = code[2], code[3], code[4]
    renumerote = "AC" + annee + comp + "0" + numero
    return ACs.get_acs_notation_pointe(renumerote)