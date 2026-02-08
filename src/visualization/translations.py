"""
French translations for dashboard UI components.

This module centralizes all user-facing French strings for the dashboard.
Internal keys (e.g., 'net_income', 'total_revenue') remain in English for stability.

Note
----
The word "Forecast" is kept in English per user requirements.
"""

from typing import Dict

# ============================================================================
# Layout strings (layouts.py)
# ============================================================================

DASHBOARD_TITLE = "Tableau de Bord de Comparaison des Forecasts"
COMPANY_LABEL = "Entreprise"  # Used in: f"{COMPANY_LABEL} : {display_name}"
SELECTOR_LABEL = "Sélectionner un compte ou une vue agrégée :"
FOOTER_TEXT = "Comparaison des Forecasts TabPFN vs Prophet | Construit avec Dash"

# ============================================================================
# App title (app.py)
# ============================================================================

APP_TITLE_PREFIX = "Comparaison des forecasts"  # Used in: f"{APP_TITLE_PREFIX} - {company_id}"

# ============================================================================
# Dropdown options (data_loader.py)
# ============================================================================

DROPDOWN_HEADER_AGGREGATED = "─── Vues agrégées ───"
DROPDOWN_HEADER_ACCOUNTS = "─── Comptes individuels ───"

# Aggregation type display labels (French)
# Maps internal English keys to French display labels
AGG_LABELS: Dict[str, str] = {
    "net_income": "Résultat net",
    "total_revenue": "Chiffre d'affaires",
    "total_expenses": "Total charges"
}

# Account label prefix
ACCOUNT_PREFIX = "Compte"  # Used in: f"{ACCOUNT_PREFIX} {account}"

# ============================================================================
# Chart strings (time_series_chart.py)
# ============================================================================

CHART_TRAIN_DATA = "Données d'Entraînement"
CHART_ACTUAL_TEST = "Réel (Test)"
CHART_FORECAST_SUFFIX = "Forecast"  # Used in: f"Forecast {approach_name}"
CHART_CI_SUFFIX = "80% CI"  # Used in: f"{approach_name} {CHART_CI_SUFFIX}"

# Hover templates
CHART_HOVER_TRAIN = "<b>Entraînement</b>"
CHART_HOVER_ACTUAL = "<b>Réel</b>"
CHART_HOVER_DATE = "Date"  # Used in hover templates
CHART_HOVER_VALUE = "Valeur"  # Used in hover templates

CHART_EMPTY_MESSAGE = "Aucune donnée disponible"

# Axis labels
CHART_XAXIS_LABEL = "Date"
CHART_YAXIS_LABEL = "Montant (€)"

# ============================================================================
# Callback strings (callbacks.py)
# ============================================================================

# Error/info messages
CALLBACK_SELECT_ACCOUNT = "Veuillez sélectionner un compte ou une vue agrégée"
CALLBACK_ACCOUNT_NOT_FOUND = "introuvable"  # Used in: f"Compte {account} {CALLBACK_ACCOUNT_NOT_FOUND}"
CALLBACK_NO_FORECASTS = "Aucun forecast disponible pour le compte"  # Used in: f"{msg} {account}"
CALLBACK_ERROR_AGGREGATION = "Erreur de calcul de l'agrégation"  # Used in: f"{msg} : {str(e)}"
CALLBACK_ERROR_METRICS = "Erreur de calcul des métriques"  # Used in: f"{msg} : {str(e)}"
CALLBACK_NO_METRICS = "Aucune métrique disponible pour cette sélection"

# Title templates
CALLBACK_FORECAST_COMPARISON = "Comparaison des forecasts"  # Used in titles
CALLBACK_METRICS_COMPARISON = "Comparaison des Métriques"  # Used in titles

# ============================================================================
# Metrics table strings (metrics_table.py)
# ============================================================================

# Metric descriptions (French translations of full names)
METRICS_INFO_FR = [
    ('MAPE', 'Mean Absolute Percentage Error', '%'),
    ('SMAPE', 'Symmetric Mean Absolute Percentage Error', '%'),
    ('RMSSE', 'Root Mean Squared Scaled Error', ''),
    ('NRMSE', 'Normalized Root Mean Squared Error', ''),
    ('WAPE', 'Weighted Absolute Percentage Error', '%'),
    ('SWAPE', 'Symmetric Weighted Absolute Percentage Error', '%'),
    ('PBIAS', 'Percent Bias', '%'),
]

# Table column headers
METRICS_TABLE_HEADER_METRIC = "Métrique"
METRICS_TABLE_HEADER_DESCRIPTION = "Description"

# Messages
METRICS_EMPTY_MESSAGE = "Aucune métrique disponible"
METRICS_NOTE = "Note : Des valeurs plus basses sont meilleures pour toutes les métriques"
