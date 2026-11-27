# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

"""
Texts of the findings of `check_study`, in every language of the user interface.

The rules compute the values (objects, years, costs); this module only says them. The French texts
use the words of the user interface of Antares Web ("cluster", "contrainte couplante").
"""

from antares_web_mcp.tools.common import Language

MESSAGES: dict[str, dict[Language, str]] = {
    "calendar.horizon": {
        "en": (
            "1 January is set to a {weekday}, but {expected} (horizon '{horizon}'): weekdays "
            "and weekends of the time series are shifted."
        ),
        "fr": (
            "Le 1er janvier est réglé sur un {weekday}, alors que {expected} (horizon « {horizon} ») : "
            "les jours de semaine et les week-ends des séries temporelles sont décalés."
        ),
    },
    "calendar.first_january": {
        "en": "1 January {year} is a {day}",
        "fr": "le 1er janvier {year} est un {day}",
    },
    "calendar.and": {"en": " and ", "fr": " et "},
    "calendar.name": {
        "en": (
            "The study name refers to {year} (1 January {year} is a {day}), "
            "but the study uses {calendar} (horizon '{horizon}', 1 January = {weekday}). "
            "Check that time series built for that year are aligned with this calendar (weekends, holidays)."
        ),
        "fr": (
            "Le nom de l'étude fait référence à {year} (le 1er janvier {year} est un {day}), "
            "mais l'étude utilise {calendar} (horizon « {horizon} », 1er janvier = {weekday}). "
            "Vérifiez que les séries temporelles construites pour cette année sont alignées sur ce calendrier "
            "(week-ends, jours fériés)."
        ),
    },
    "calendar.of_year": {"en": "the {year} calendar", "fr": "le calendrier {year}"},
    "calendar.of_another_year": {"en": "another calendar", "fr": "un autre calendrier"},
    "playlist": {
        "en": "{inactive} of {total} Monte-Carlo years are excluded by the playlist.",
        "fr": "Années Monte-Carlo exclues par la playlist : {inactive} sur {total}.",
    },
    "playlist.year": {"en": "year {year}", "fr": "année {year}"},
    "thermal_min_stable_power": {
        "en": "Min stable power above the unit capacity.",
        "fr": "Puissance minimale stable supérieure à la capacité d'une unité.",
    },
    "thermal_market_bid": {
        "en": (
            "Market bid below the marginal cost: the merit order uses the bid, so these plants run before "
            "cheaper ones (intended only to model a subsidy or a must-run contract)."
        ),
        "fr": (
            "Offre de marché inférieure au coût marginal : l'ordre de mérite utilise l'offre, ces clusters sont "
            "donc appelés avant des clusters moins chers (voulu seulement pour modéliser une subvention ou un "
            "contrat de must-run)."
        ),
    },
    "thermal_market_bid.object": {
        "en": "{cluster} (bid {bid} < cost {cost} EUR/MWh)",
        "fr": "{cluster} (offre {bid} < coût {cost} EUR/MWh)",
    },
    "unsupplied_energy_cost.too_low": {
        "en": (
            "Unsupplied energy cost below the most expensive plant of the area: the optimiser sheds load "
            "rather than running these plants."
        ),
        "fr": (
            "Coût de l'énergie non distribuée inférieur au coût du cluster le plus cher de la zone : "
            "l'optimiseur déleste plutôt que de faire produire ces clusters."
        ),
    },
    "unsupplied_energy_cost.free": {
        "en": (
            "Unsupplied energy cost of 0: the load of these areas can be left unserved for free. Usual for "
            "technical (virtual) nodes modelling an optional consumption, an error for a real area."
        ),
        "fr": (
            "Coût de l'énergie non distribuée à 0 : la consommation de ces zones peut rester non servie "
            "gratuitement. Habituel pour des nœuds techniques (virtuels) qui modélisent une consommation "
            "facultative, une erreur pour une zone réelle."
        ),
    },
    "storage_efficiency": {
        "en": (
            "Storage efficiency above 1: the storage returns more energy than it absorbs. Check whether it "
            "compensates a loss modelled elsewhere."
        ),
        "fr": (
            "Rendement de stockage supérieur à 1 : le stockage restitue plus d'énergie qu'il n'en absorbe. "
            "Vérifiez s'il compense une perte modélisée ailleurs."
        ),
    },
    "storage_efficiency.object": {
        "en": "{storage} (injection {injection:g}, withdrawal {withdrawal:g})",
        "fr": "{storage} (injection {injection:g}, soutirage {withdrawal:g})",
    },
    "disabled_objects.disabled": {
        "en": "{count}/{total} {kind} are disabled.",
        "fr": "{count}/{total} {kind} sont désactivés.",
    },
    "disabled_objects.without_capacity": {
        "en": "{count} enabled {kind} have no capacity.",
        "fr": "{count} {kind} activés n'ont aucune capacité.",
    },
    "disabled_objects.constraints": {
        "en": "Disabled binding constraints.",
        "fr": "Contraintes couplantes désactivées.",
    },
    "kind.thermals": {"en": "thermal clusters", "fr": "clusters thermiques"},
    "kind.renewables": {"en": "renewable clusters", "fr": "clusters renouvelables"},
    "kind.storages": {"en": "short-term storages", "fr": "stockages court-terme"},
    "isolated_areas": {
        "en": (
            "Areas without any link: their production only serves their own load (or is spilled). Usual for "
            "helper areas used in binding constraints."
        ),
        "fr": (
            "Zones sans aucun lien : leur production ne sert que leur propre consommation (ou est déversée). "
            "Habituel pour des zones auxiliaires utilisées dans des contraintes couplantes."
        ),
    },
    "constraint_references.missing": {
        "en": "Binding constraint terms on objects that do not exist.",
        "fr": "Termes de contraintes couplantes portant sur des objets qui n'existent pas.",
    },
    "constraint_references.disabled": {
        "en": (
            "Binding constraint terms on disabled clusters: their production is 0, which may make the "
            "constraint infeasible or meaningless."
        ),
        "fr": (
            "Termes de contraintes couplantes portant sur des clusters désactivés : leur production vaut 0, "
            "ce qui peut rendre la contrainte infaisable ou sans objet."
        ),
    },
    "relaxable_helper_terms": {
        "en": (
            "These constraints use a free and optional production of an isolated (helper) area on the side that "
            "is relaxed by lowering it: the optimiser can reduce it at no cost, so the constraint probably never "
            "binds. If the helper stands for an availability, it only works as an upper bound. Check in the "
            "outputs whether the helper produces less than its availability."
        ),
        "fr": (
            "Ces contraintes utilisent une production gratuite et facultative d'une zone isolée (auxiliaire), du "
            "côté que sa baisse relâche : l'optimiseur peut la réduire sans coût, la contrainte n'est donc "
            "probablement jamais active. Si la zone auxiliaire représente une disponibilité, elle ne joue que le "
            "rôle de borne supérieure. Vérifiez dans les résultats si elle produit moins que sa disponibilité."
        ),
    },
    "hydro_generation_power": {
        "en": "Hydro inflows but no generating power: the reservoir cannot be turbined.",
        "fr": "Apports hydrauliques mais aucune puissance de turbinage : le réservoir ne peut pas être turbiné.",
    },
    "hydro_generation_power.hourly": {
        "en": " Power read in 'input/hydro/series/<area>/maxHourlyGenPower' (`hydro-pmax = hourly`).",
        "fr": " Puissance lue dans 'input/hydro/series/<area>/maxHourlyGenPower' (`hydro-pmax = hourly`).",
    },
    "hydro_generation_power.legacy": {
        "en": (
            " The legacy files maxpower_<area> still declare {power} MW in total but are ignored "
            "in this mode: the switch to `hourly` probably did not migrate their values."
        ),
        "fr": (
            " Les anciens fichiers maxpower_<area> déclarent encore {power} MW au total mais sont ignorés "
            "dans ce mode : le passage à `hourly` n'a probablement pas migré leurs valeurs."
        ),
    },
    "hydro_generation_power.daily": {
        "en": (
            " Power read in the 1st column of 'input/hydro/common/capacity/maxpower_<area>' (`hydro-pmax` is "
            "not `hourly`: the hourly series are ignored)."
        ),
        "fr": (
            " Puissance lue dans la 1re colonne de 'input/hydro/common/capacity/maxpower_<area>' (`hydro-pmax` "
            "n'est pas `hourly` : les séries horaires sont ignorées)."
        ),
    },
    "thermal_availability.null": {
        "en": "Enabled clusters with a capacity but a null availability series: they never produce.",
        "fr": "Clusters activés ayant une capacité mais une série de disponibilité nulle : ils ne produisent jamais.",
    },
    "thermal_availability.above_capacity": {
        "en": (
            "Availability above the installed capacity (unit count x nominal capacity): the capacity was "
            "probably changed without updating the series."
        ),
        "fr": (
            "Disponibilité supérieure à la capacité installée (nombre d'unités x capacité nominale) : la capacité "
            "a probablement été modifiée sans mettre à jour la série."
        ),
    },
    "renewable_series.null": {
        "en": "Enabled renewable clusters with a null series.",
        "fr": "Clusters renouvelables activés ayant une série nulle.",
    },
    "renewable_series.out_of_range": {
        "en": (
            "Production factors outside [0, 1]: the series is probably in MW while the cluster expects a "
            "production factor (or the opposite)."
        ),
        "fr": (
            "Facteurs de production hors de [0, 1] : la série est probablement en MW alors que le cluster attend "
            "un facteur de production (ou l'inverse)."
        ),
    },
    "renewable_series.object": {
        "en": "{cluster} (factor from {minimum:g} to {maximum:g})",
        "fr": "{cluster} (facteur de {minimum:g} à {maximum:g})",
    },
    "link_capacities": {
        "en": (
            "Links with a 0 MW capacity in both directions: they carry nothing (placeholders, or capacities "
            "never filled in)."
        ),
        "fr": (
            "Liens ayant une capacité de 0 MW dans les deux sens : ils ne transportent rien (liens réservés, ou "
            "capacités jamais renseignées)."
        ),
    },
    "scenarised_constraints": {
        "en": (
            "Constraints of a scenarised group whose right-hand side columns are all identical: the "
            "scenarisation has no effect."
        ),
        "fr": (
            "Contraintes d'un groupe scénarisé dont les colonnes du second membre sont toutes identiques : la "
            "scénarisation n'a aucun effet."
        ),
    },
    "note.unreadable_matrices": {
        "en": "{count} matrices could not be read and were not checked.",
        "fr": "{count} matrices n'ont pas pu être lues et n'ont pas été vérifiées.",
    },
}

FRENCH_WEEKDAYS = {
    "Monday": "lundi",
    "Tuesday": "mardi",
    "Wednesday": "mercredi",
    "Thursday": "jeudi",
    "Friday": "vendredi",
    "Saturday": "samedi",
    "Sunday": "dimanche",
}
NO_BREAK_SPACE = " "


def say(key: str, language: Language, **values: object) -> str:
    """The text of `key` in `language`, with its values."""
    return MESSAGES[key][language].format(**values)


def weekday_name(weekday: str, language: Language) -> str:
    """The name of a weekday of the Antares Web API (`Monday`) in `language`."""
    return FRENCH_WEEKDAYS.get(weekday, weekday) if language == "fr" else weekday


def number(value: float, language: Language, decimals: int = 0) -> str:
    """A number with its thousands separated: `3,000.0` in English reads as 3 for a French reader."""
    english = f"{value:,.{decimals}f}"
    if language == "fr":
        return english.replace(",", NO_BREAK_SPACE).replace(".", ",")
    return english
