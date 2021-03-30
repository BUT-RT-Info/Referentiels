import logging, yaml

__LOGGER = logging.getLogger(__name__)

# Récupère les informations officielles sur les ressources (code/nom)
with open("pn/ressources.yml", 'r', encoding="utf8") as fid:
    DATA_RESSOURCES = yaml.load(fid.read(), Loader=yaml.Loader)
# Récupère les données officielles des ACs
with open("pn/acs.yml", 'r', encoding="utf8") as fid:
    DATA_ACS = yaml.load(fid.read(), Loader=yaml.Loader)
with open("pn/saes.yml", 'r', encoding="utf8") as fid:
    DATA_SAES = yaml.load(fid.read(), Loader=yaml.Loader)

