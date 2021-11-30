def get_ressource_notation_pointe(code_ressource): # => à remplacer
    """Renvoie la notation pointée d'une ressource partant
    de RXXX"""
    return code_ressource[:2] + "." + code_ressource[-2:]


def get_sae_notation_pointe(code_sae):
    """Renvoie la notation pointée d'une sae"""
    return code_sae[:4] + "." + code_sae[-1]