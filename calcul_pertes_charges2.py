import streamlit as st
import pandas as pd
import numpy as np
from math import pi, log10, exp, sqrt
import io
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Rectangle, Polygon, FancyBboxPatch
import matplotlib.lines as mlines
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import tempfile
import os

# Configuration de la page
st.set_page_config(
    page_title="Calculateur Pertes de Charge & NPSH Avancé",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        border-bottom: 2px solid #2e86ab;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .result-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .total-box {
        background-color: #1f77b4;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #e8f4fd;
        border: 1px solid #b8daff;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .template-box {
        background-color: #fff3e0;
        border: 2px dashed #ff9800;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class CalculateurPertesCharge:
    def __init__(self):
        self.initialiser_donnees()
    
    def initialiser_donnees(self):
        """Initialise les données par défaut"""
        # Matériaux et rugosités (en mètres)
        if 'materiaux' not in st.session_state:
            st.session_state.materiaux = {
                'Acier': 0.000045,
                'PVC': 0.0000015,
                'PEHD': 0.000007,
                'Fonte': 0.00026,
                'Béton': 0.0003,
                'Cuivre': 0.0000015,
                'Acier galvanisé': 0.00015
            }
        
        # Fluides et propriétés
        if 'fluides' not in st.session_state:
            st.session_state.fluides = {
                'Eau': {
                    'masse_volumique_20c': 998.2,
                    'viscosite_cinematique_20c': 1.004e-6,
                    'pression_vapeur_20c': 2337.0,
                    'coefficient_temp': 0.0002,
                    'module_elasticite': 2.15e9
                },
                'Eau glycolée 30%': {
                    'masse_volumique_20c': 1050.0,
                    'viscosite_cinematique_20c': 2.5e-6,
                    'pression_vapeur_20c': 2337.0,
                    'coefficient_temp': 0.0003,
                    'module_elasticite': 2.5e9
                },
                'Fuel léger': {
                    'masse_volumique_20c': 850.0,
                    'viscosite_cinematique_20c': 3.0e-6,
                    'pression_vapeur_20c': 500.0,
                    'coefficient_temp': 0.0007,
                    'module_elasticite': 1.5e9
                },
                'Huile hydraulique': {
                    'masse_volumique_20c': 870.0,
                    'viscosite_cinematique_20c': 46.0e-6,
                    'pression_vapeur_20c': 100.0,
                    'coefficient_temp': 0.0006,
                    'module_elasticite': 1.8e9
                },
                'Ammoniac': {
                    'masse_volumique_20c': 610.0,
                    'viscosite_cinematique_20c': 0.36e-6,
                    'pression_vapeur_20c': 857000.0,
                    'coefficient_temp': 0.0025,
                    'module_elasticite': 1.2e9
                }
            }
        
        # Coefficients de pertes de charge singulières
        if 'coefficients_singuliers' not in st.session_state:
            st.session_state.coefficients_singuliers = {
                'Vanne pleine ouverture': 0.2,
                'Vanne 1/2 ouverture': 4.0,
                'Clapet de retenue': 2.5,
                'Clapet anti-retour': 10.0,
                'Coudes 90° standard': 0.3,
                'Coudes 90° rayon long': 0.2,
                'Coudes 45°': 0.2,
                'Té droit': 0.9,
                'Té latéral': 1.8,
                'Rétrécissement brusque': 0.5,
                'Élargissement brusque': 1.0,
                'Entrée de réservoir': 0.5,
                'Sortie de réservoir': 1.0,
                'Crépine': 2.0,
                'Robinet vanne': 0.2
            }
        
        # Données de base
        if 'donnees_base' not in st.session_state:
            st.session_state.donnees_base = {
                'diametre': 0.1,
                'materiau': 'Acier',
                'debit_m3h': 36.0,
                'fluide': 'Eau',
                'temperature': 20.0,
                'pression_amont': 101325.0,
                'hauteur_geodesique_aspiration': 2.0,
                'npsh_requis': 2.0,
                'rendement_mecanique': 0.95,
                'rendement_electrique': 0.92,
                'epaisseur_conduite': 0.005,
                'module_young_materiau': 200e9
            }
        
        # Longueurs et hauteurs
        if 'geometrie' not in st.session_state:
            st.session_state.geometrie = {
                'longueur_totale': 100.0,
                'hauteur_montee': 10.0,
                'hauteur_descente': 5.0,
                'longueur_aspiration': 5.0,
                'longueur_refoulement': 95.0
            }
        
        # Points singuliers
        if 'points_singuliers' not in st.session_state:
            st.session_state.points_singuliers = []
        
        # Données de pompe
        if 'donnees_pompe' not in st.session_state:
            st.session_state.donnees_pompe = pd.DataFrame()

    def convertir_debit_m3h_vers_m3s(self, debit_m3h):
        """Convertit le débit de m³/h vers m³/s"""
        return debit_m3h / 3600.0

    def convertir_debit_m3s_vers_m3h(self, debit_m3s):
        """Convertit le débit de m³/s vers m³/h"""
        return debit_m3s * 3600.0

    def calculer_proprietes_fluide(self, fluide, temperature):
        """Calcule les propriétés du fluide en fonction de la température"""
        proprietes_20c = st.session_state.fluides[fluide]
        
        # Correction pour la température (approximation linéaire)
        delta_temp = temperature - 20.0
        coeff_temp = proprietes_20c['coefficient_temp']
        
        masse_volumique = proprietes_20c['masse_volumique_20c'] * (1.0 - coeff_temp * delta_temp)
        
        # Pour la viscosité, utilisation d'une approximation exponentielle
        viscosite_cinematique = proprietes_20c['viscosite_cinematique_20c'] * exp(-0.02 * delta_temp)
        
        # Pour la pression de vapeur, approximation avec formule d'Antoine simplifiée
        if fluide == 'Eau':
            # Formule d'Antoine pour l'eau (P en Pa, T en °C)
            pression_vapeur = 610.94 * exp((17.625 * temperature) / (temperature + 243.04))
        else:
            # Approximation linéaire pour autres fluides
            pression_vapeur = proprietes_20c['pression_vapeur_20c'] * exp(0.05 * delta_temp)
        
        return {
            'masse_volumique': max(masse_volumique, 500.0),
            'viscosite_cinematique': max(viscosite_cinematique, 0.1e-6),
            'pression_vapeur': pression_vapeur,
            'module_elasticite': proprietes_20c['module_elasticite']
        }

    def calculer_nombre_reynolds(self, vitesse, diametre, viscosite_cinematique):
        """Calcule le nombre de Reynolds"""
        if viscosite_cinematique == 0:
            return 0.0
        return (vitesse * diametre) / viscosite_cinematique

    def calculer_rugosite_relative(self, rugosite, diametre):
        """Calcule la rugosité relative"""
        if diametre == 0:
            return 0.0
        return rugosite / diametre

    def calculer_coefficient_friction(self, Re, rugosite_relative):
        """Calcule le coefficient de friction avec la formule de Colebrook-White"""
        if Re == 0:
            return 0.0
        
        # Pour un écoulement laminaire
        if Re < 2000:
            return 64.0 / Re
        
        # Estimation initiale pour turbulent
        f = 0.02
        
        # Résolution itérative de Colebrook-White
        for i in range(50):
            f_new = 1.0 / (-2.0 * log10((rugosite_relative / 3.7) + (2.51 / (Re * f**0.5))))**2
            if abs(f_new - f) < 1e-8:
                return f_new
            f = f_new
        
        return f

    def calculer_pertes_lineaires(self, f, L, D, vitesse, g=9.81):
        """Calcule les pertes de charge linéaires (formule de Darcy-Weisbach)"""
        if D == 0:
            return 0.0
        return f * (L / D) * (vitesse**2 / (2.0 * g))

    def calculer_pertes_singulieres(self, coefficients_singuliers, vitesse, g=9.81):
        """Calcule les pertes de charge singulières"""
        pertes_totales = 0.0
        details = []
        
        for nom, coefficient in coefficients_singuliers.items():
            perte = coefficient * (vitesse**2 / (2.0 * g))
            pertes_totales += perte
            details.append({
                'nom': nom,
                'coefficient': coefficient,
                'perte': perte
            })
        
        return pertes_totales, details

    def calculer_section(self, diametre):
        """Calcule la section de la conduite"""
        return pi * (diametre**2) / 4.0

    def calculer_vitesse(self, debit, section):
        """Calcule la vitesse d'écoulement"""
        if section == 0:
            return 0.0
        return debit / section

    def calculer_npsh_disponible(self, pression_amont, hauteur_geodesique, pertes_aspiration, 
                               pression_vapeur, masse_volumique, g=9.81):
        """Calcule le NPSH disponible"""
        terme_pression = (pression_amont - pression_vapeur) / (masse_volumique * g)
        npsh_disponible = terme_pression + hauteur_geodesique - pertes_aspiration
        
        return max(npsh_disponible, 0.0)

    def calculer_coup_belier(self, resultats):
        """Calcule les paramètres du coup de bélier"""
        donnees = st.session_state.donnees_base
        proprietes_fluide = resultats['proprietes_fluide']
        
        # Célérité de l'onde
        K = proprietes_fluide['module_elasticite']  # Module d'élasticité du fluide
        E = donnees['module_young_materiau']  # Module d'Young du matériau
        D = donnees['diametre']
        e = donnees['epaisseur_conduite']
        
        # Calcul de la célérité (formule d'Allievi)
        a = sqrt(K / proprietes_fluide['masse_volumique']) / sqrt(1 + (K * D) / (E * e))
        
        # Temps de parcours de l'onde
        L = st.session_state.geometrie['longueur_refoulement']
        T_parcours = 2 * L / a
        
        # Pente des droites de Bergeron
        pente_bergeron = a / (9.81 * resultats['section'])
        
        # Surpression maximale lors de l'arrêt brusque
        delta_v = resultats['vitesse']  # Variation de vitesse (arrêt complet)
        delta_p = proprietes_fluide['masse_volumique'] * a * delta_v
        
        # Dépression au réservoir
        depression_reservoir = delta_p / (proprietes_fluide['masse_volumique'] * 9.81)
        
        return {
            'celerite_onde': a,
            'temps_parcours': T_parcours,
            'pente_bergeron': pente_bergeron,
            'surpression_max': delta_p,
            'depression_reservoir': depression_reservoir
        }

    def calculer_puissances(self, resultats):
        """Calcule les puissances mécanique et électrique"""
        donnees = st.session_state.donnees_base
        
        # Puissance hydraulique (déjà calculée)
        P_hydraulique = resultats['puissance_hydraulique']
        
        # Puissance mécanique
        P_mecanique = P_hydraulique / donnees['rendement_mecanique']
        
        # Puissance électrique
        P_electrique = P_mecanique / donnees['rendement_electrique']
        
        return {
            'puissance_hydraulique': P_hydraulique,
            'puissance_mecanique': P_mecanique,
            'puissance_electrique': P_electrique
        }

    def calculer_courbe_pompe_frequence(self, donnees_pompe_50Hz, frequence):
        """Calcule les courbes de pompe pour différentes fréquences"""
        if donnees_pompe_50Hz.empty:
            return pd.DataFrame()
        
        ratio = frequence / 50.0
        
        # Lois de similitude pour les pompes
        donnees_pompe = donnees_pompe_50Hz.copy()
        
        # Vérification et normalisation des noms de colonnes
        colonnes_disponibles = donnees_pompe.columns.str.lower().tolist()
        
        # Recherche des colonnes avec différentes orthographes possibles
        colonne_debit = None
        colonne_hmt = None
        
        for col in donnees_pompe.columns:
            col_lower = col.lower()
            if 'débit' in col_lower or 'debit' in col_lower or 'q' in col_lower:
                colonne_debit = col
            elif 'hmt' in col_lower or 'hauteur' in col_lower or 'h' in col_lower:
                colonne_hmt = col
            elif 'pression' in col_lower:
                colonne_hmt = col  # On considère que la pression peut être convertie en HMT
        
        # Application des lois de similitude
        if colonne_debit and colonne_hmt:
            donnees_pompe[colonne_debit] = donnees_pompe[colonne_debit] * ratio
            donnees_pompe[colonne_hmt] = donnees_pompe[colonne_hmt] * (ratio ** 2)
        
        return donnees_pompe

    def calculer_pertes_totales(self):
        """Calcule toutes les pertes de charge et le NPSH"""
        donnees = st.session_state.donnees_base
        geometrie = st.session_state.geometrie
        materiaux = st.session_state.materiaux
        
        # Conversion du débit
        debit_m3s = self.convertir_debit_m3h_vers_m3s(donnees['debit_m3h'])
        
        # Calcul des propriétés du fluide
        proprietes_fluide = self.calculer_proprietes_fluide(donnees['fluide'], donnees['temperature'])
        
        # Calculs géométriques de base
        diametre = donnees['diametre']
        section = self.calculer_section(diametre)
        vitesse = self.calculer_vitesse(debit_m3s, section)
        
        # Nombre de Reynolds
        Re = self.calculer_nombre_reynolds(
            vitesse, diametre, proprietes_fluide['viscosite_cinematique']
        )
        
        # Rugosité relative
        rugosite = materiaux[donnees['materiau']]
        rugosite_relative = self.calculer_rugosite_relative(rugosite, diametre)
        
        # Coefficient de friction
        f = self.calculer_coefficient_friction(Re, rugosite_relative)
        
        # Pertes linéaires totales
        pertes_lineaires_totales = self.calculer_pertes_lineaires(
            f, geometrie['longueur_totale'], diametre, vitesse
        )
        
        # Pertes linéaires d'aspiration seulement
        pertes_lineaires_aspiration = self.calculer_pertes_lineaires(
            f, geometrie['longueur_aspiration'], diametre, vitesse
        )
        
        # Pertes singulières
        coefficients_singuliers = {}
        for point in st.session_state.points_singuliers:
            nom = point['type']
            quantite = point['quantite']
            coefficient = st.session_state.coefficients_singuliers.get(nom, 0.0)
            coefficients_singuliers[f"{nom} (x{quantite})"] = coefficient * float(quantite)
        
        pertes_singulieres_totales, details_singuliers = self.calculer_pertes_singulieres(
            coefficients_singuliers, vitesse
        )
        
        # Estimation des pertes singulières d'aspiration (50% des pertes totales par défaut)
        pertes_singulieres_aspiration = pertes_singulieres_totales * 0.5
        
        # Pertes de charge totales
        pertes_totales = pertes_lineaires_totales + pertes_singulieres_totales
        
        # Pertes d'aspiration totales
        pertes_aspiration_totales = pertes_lineaires_aspiration + pertes_singulieres_aspiration
        
        # Hauteur manométrique totale
        hauteur_manometrique = (
            geometrie['hauteur_montee'] - 
            geometrie['hauteur_descente'] + 
            pertes_totales
        )
        
        # Puissance hydraulique
        puissance_hydraulique = (
            proprietes_fluide['masse_volumique'] * 9.81 * debit_m3s * hauteur_manometrique
        ) / 1000.0  # en kW
        
        # NPSH disponible
        npsh_disponible = self.calculer_npsh_disponible(
            donnees['pression_amont'],
            donnees['hauteur_geodesique_aspiration'],
            pertes_aspiration_totales,
            proprietes_fluide['pression_vapeur'],
            proprietes_fluide['masse_volumique']
        )
        
        # Marge de NPSH
        marge_npsh = npsh_disponible - donnees['npsh_requis']
        
        # Calcul des puissances
        puissances = self.calculer_puissances({
            'puissance_hydraulique': puissance_hydraulique
        })
        
        # Calcul du coup de bélier
        coup_belier = self.calculer_coup_belier({
            'vitesse': vitesse,
            'section': section,
            'proprietes_fluide': proprietes_fluide
        })
        
        return {
            'diametre': diametre,
            'section': section,
            'vitesse': vitesse,
            'nombre_reynolds': Re,
            'rugosite': rugosite,
            'rugosite_relative': rugosite_relative,
            'coefficient_friction': f,
            'pertes_lineaires': pertes_lineaires_totales,
            'pertes_singulieres': pertes_singulieres_totales,
            'pertes_totales': pertes_totales,
            'pertes_aspiration': pertes_aspiration_totales,
            'hauteur_manometrique': hauteur_manometrique,
            'puissance_hydraulique': puissance_hydraulique,
            'proprietes_fluide': proprietes_fluide,
            'npsh_disponible': npsh_disponible,
            'marge_npsh': marge_npsh,
            'details_singuliers': details_singuliers,
            'debit_m3s': debit_m3s,
            'regime_ecoulement': 'Turbulent' if Re > 4000 else 'Laminaire' if Re < 2000 else 'Transition',
            'puissances': puissances,
            'coup_belier': coup_belier
        }

    def dessiner_schema_installation(self):
        """Dessine un schéma schématique de l'installation"""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Configuration du graphique
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 8)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Couleurs
        couleur_conduite = '#4682B4'
        couleur_reservoir = '#87CEEB'
        couleur_pompe = '#FF6B6B'
        couleur_vanne = '#32CD32'
        couleur_clapet = '#FFA500'
        
        # Réservoir amont (aspiration)
        reservoir_amont = Rectangle((1, 2), 0.5, 2, facecolor=couleur_reservoir, edgecolor='black')
        ax.add_patch(reservoir_amont)
        ax.text(0.5, 3.5, 'Réservoir\nAspiration', ha='center', va='center', fontsize=10, weight='bold')
        
        # Conduite d'aspiration
        ax.plot([1.5, 3], [3, 3], color=couleur_conduite, linewidth=3)
        
        # Points singuliers sur aspiration
        x_aspiration = 2.0
        for point in st.session_state.points_singuliers:
            if 'aspiration' in point.get('emplacement', 'aspiration'):
                if 'vanne' in point['type'].lower():
                    ax.plot([x_aspiration, x_aspiration], [2.8, 3.2], color=couleur_vanne, linewidth=3)
                    ax.text(x_aspiration, 2.5, 'V', ha='center', va='center', fontsize=8, weight='bold')
                elif 'clapet' in point['type'].lower():
                    triangle = Polygon([[x_aspiration, 2.8], [x_aspiration-0.2, 3.2], [x_aspiration+0.2, 3.2]], 
                                     facecolor=couleur_clapet)
                    ax.add_patch(triangle)
                    ax.text(x_aspiration, 2.5, 'C', ha='center', va='center', fontsize=8, weight='bold')
                x_aspiration += 0.3
        
        # Pompe
        cercle_pompe = Circle((3.5, 3), 0.4, facecolor=couleur_pompe, edgecolor='black')
        ax.add_patch(cercle_pompe)
        ax.text(3.5, 3, 'P', ha='center', va='center', fontsize=12, weight='bold', color='white')
        ax.text(3.5, 2.3, 'POMPE', ha='center', va='center', fontsize=9, weight='bold')
        
        # Conduite refoulement horizontale
        ax.plot([3.9, 7], [3, 3], color=couleur_conduite, linewidth=3)
        
        # Points singuliers sur refoulement
        x_refoulement = 4.5
        for point in st.session_state.points_singuliers:
            if point.get('emplacement', 'aspiration') == 'refoulement':
                if 'vanne' in point['type'].lower():
                    ax.plot([x_refoulement, x_refoulement], [2.8, 3.2], color=couleur_vanne, linewidth=3)
                    ax.text(x_refoulement, 2.5, 'V', ha='center', va='center', fontsize=8, weight='bold')
                elif 'clapet' in point['type'].lower():
                    triangle = Polygon([[x_refoulement, 2.8], [x_refoulement-0.2, 3.2], [x_refoulement+0.2, 3.2]], 
                                     facecolor=couleur_clapet)
                    ax.add_patch(triangle)
                    ax.text(x_refoulement, 2.5, 'C', ha='center', va='center', fontsize=8, weight='bold')
                elif 'coude' in point['type'].lower():
                    ax.plot([x_refoulement, x_refoulement+0.2], [3, 3.2], color='red', linewidth=2)
                    ax.text(x_refoulement, 2.5, '⟳', ha='center', va='center', fontsize=10)
                x_refoulement += 0.3
        
        # Montée vers réservoir aval
        ax.plot([7, 7], [3, 5], color=couleur_conduite, linewidth=3)
        
        # Réservoir aval (refoulement)
        reservoir_aval = Rectangle((6.5, 5), 0.5, 2, facecolor=couleur_reservoir, edgecolor='black')
        ax.add_patch(reservoir_aval)
        ax.text(8, 6, 'Réservoir\nRefoulement', ha='center', va='center', fontsize=10, weight='bold')
        
        # Flèches d'écoulement
        ax.annotate('', xy=(2.5, 3), xytext=(2.0, 3),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.annotate('', xy=(5, 3), xytext=(4.5, 3),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
        
        # Textes informatifs
        resultats = self.calculer_pertes_totales()
        ax.text(5, 0.8, f"Débit: {st.session_state.donnees_base['debit_m3h']:.1f} m³/h", 
               ha='center', va='center', fontsize=11, weight='bold', 
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
        ax.text(5, 0.4, f"HMT: {resultats['hauteur_manometrique']:.1f} m", 
               ha='center', va='center', fontsize=11, weight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"))
        
        ax.text(5, 7.5, "SCHEMA DE L'INSTALLATION", 
               ha='center', va='center', fontsize=14, weight='bold')
        
        # Légende
        legend_elements = [
            mlines.Line2D([], [], color=couleur_conduite, linewidth=3, label='Conduite'),
            mlines.Line2D([], [], color=couleur_vanne, linewidth=3, label='Vanne'),
            mlines.Line2D([], [], color=couleur_clapet, marker='^', markersize=10, label='Clapet', linewidth=0),
            mlines.Line2D([], [], color='red', marker='>', markersize=10, label='Sens écoulement', linewidth=0)
        ]
        ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
        
        plt.tight_layout()
        return fig

    def dessiner_courbe_reseau_pompes(self, resultats):
        """Dessine la courbe du réseau avec les courbes de pompes"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Calcul de la courbe du réseau pour différents débits
        debits = np.linspace(0.1, st.session_state.donnees_base['debit_m3h'] * 2, 50)
        hmt_reseau = []
        
        for debit in debits:
            debit_m3s = self.convertir_debit_m3h_vers_m3s(debit)
            vitesse = self.calculer_vitesse(debit_m3s, resultats['section'])
            
            pertes_lineaires = self.calculer_pertes_lineaires(
                resultats['coefficient_friction'],
                st.session_state.geometrie['longueur_totale'],
                resultats['diametre'],
                vitesse
            )
            
            hmt = (st.session_state.geometrie['hauteur_montee'] - 
                  st.session_state.geometrie['hauteur_descente'] + 
                  pertes_lineaires)
            hmt_reseau.append(hmt)
        
        # Courbe du réseau
        ax.plot(debits, hmt_reseau, 'b-', linewidth=3, label='Courbe du réseau')
        
        # Courbes de pompes si disponibles
        if not st.session_state.donnees_pompe.empty:
            frequences = [50, 45, 40, 35, 30, 25]
            couleurs = ['red', 'orange', 'green', 'purple', 'brown', 'pink']
            
            for freq, couleur in zip(frequences, couleurs):
                pompe_freq = self.calculer_courbe_pompe_frequence(st.session_state.donnees_pompe, freq)
                if not pompe_freq.empty:
                    # Recherche des colonnes de débit et HMT
                    colonne_debit = None
                    colonne_hmt = None
                    
                    for col in pompe_freq.columns:
                        col_lower = col.lower()
                        if 'débit' in col_lower or 'debit' in col_lower or 'q' in col_lower:
                            colonne_debit = col
                        elif 'hmt' in col_lower or 'hauteur' in col_lower or 'h' in col_lower:
                            colonne_hmt = col
                        elif 'pression' in col_lower:
                            colonne_hmt = col
                    
                    if colonne_debit and colonne_hmt:
                        # Trier par débit pour une courbe propre
                        pompe_freq = pompe_freq.sort_values(by=colonne_debit)
                        ax.plot(pompe_freq[colonne_debit], pompe_freq[colonne_hmt], 
                               color=couleur, linestyle='--', linewidth=2, 
                               label=f'Pompe {freq}Hz')
        
        # Point de fonctionnement actuel
        ax.plot(st.session_state.donnees_base['debit_m3h'], 
               resultats['hauteur_manometrique'], 
               'ro', markersize=10, label='Point de fonctionnement')
        
        ax.set_xlabel('Débit (m³/h)', fontsize=12, weight='bold')
        ax.set_ylabel('Hauteur Manométrique Totale (m)', fontsize=12, weight='bold')
        ax.set_title('Courbe du Réseau et Courbes de Pompes', fontsize=14, weight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        return fig

def afficher_sidebar():
    """Affiche la barre latérale avec les paramètres"""
    with st.sidebar:
        st.header("⚙️ Paramètres de la Conduite")
        
        # Données de base
        st.subheader("Caractéristiques de base")
        st.session_state.donnees_base['diametre'] = st.number_input(
            "Diamètre intérieur (m)",
            value=float(st.session_state.donnees_base['diametre']),
            min_value=0.001,
            max_value=10.0,
            step=0.01,
            format="%.3f"
        )
        
        st.session_state.donnees_base['materiau'] = st.selectbox(
            "Matériau de la conduite",
            options=list(st.session_state.materiaux.keys()),
            index=list(st.session_state.materiaux.keys()).index(
                st.session_state.donnees_base['materiau']
            )
        )
        
        st.session_state.donnees_base['debit_m3h'] = st.number_input(
            "Débit (m³/h)",
            value=float(st.session_state.donnees_base['debit_m3h']),
            min_value=0.1,
            max_value=10000.0,
            step=1.0,
            format="%.1f"
        )
        
        # Propriétés du fluide
        st.subheader("Propriétés du fluide")
        st.session_state.donnees_base['fluide'] = st.selectbox(
            "Nature du fluide",
            options=list(st.session_state.fluides.keys()),
            index=list(st.session_state.fluides.keys()).index(
                st.session_state.donnees_base['fluide']
            )
        )
        
        st.session_state.donnees_base['temperature'] = st.number_input(
            "Température (°C)",
            value=float(st.session_state.donnees_base['temperature']),
            min_value=-50.0,
            max_value=300.0,
            step=1.0,
            format="%.1f"
        )
        
        # Rendements
        st.subheader("Rendements du moteur")
        st.session_state.donnees_base['rendement_mecanique'] = st.number_input(
            "Rendement mécanique",
            value=float(st.session_state.donnees_base['rendement_mecanique']),
            min_value=0.1,
            max_value=1.0,
            step=0.01,
            format="%.3f"
        )
        
        st.session_state.donnees_base['rendement_electrique'] = st.number_input(
            "Rendement électrique",
            value=float(st.session_state.donnees_base['rendement_electrique']),
            min_value=0.1,
            max_value=1.0,
            step=0.01,
            format="%.3f"
        )
        
        # Géométrie
        st.subheader("Géométrie de la conduite")
        st.session_state.geometrie['longueur_totale'] = st.number_input(
            "Longueur totale (m)",
            value=float(st.session_state.geometrie['longueur_totale']),
            min_value=0.0,
            step=1.0
        )
        
        st.session_state.geometrie['longueur_aspiration'] = st.number_input(
            "Longueur aspiration (m)",
            value=float(st.session_state.geometrie['longueur_aspiration']),
            min_value=0.0,
            step=1.0
        )
        
        st.session_state.geometrie['longueur_refoulement'] = st.number_input(
            "Longueur refoulement (m)",
            value=float(st.session_state.geometrie['longueur_refoulement']),
            min_value=0.0,
            step=1.0
        )
        
        st.session_state.geometrie['hauteur_montee'] = st.number_input(
            "Hauteur de montée (m)",
            value=float(st.session_state.geometrie['hauteur_montee']),
            step=1.0
        )
        
        st.session_state.geometrie['hauteur_descente'] = st.number_input(
            "Hauteur de descente (m)",
            value=float(st.session_state.geometrie['hauteur_descente']),
            step=1.0
        )
        
        # Paramètres NPSH
        st.subheader("Paramètres NPSH")
        st.session_state.donnees_base['pression_amont'] = st.number_input(
            "Pression amont (Pa abs)",
            value=float(st.session_state.donnees_base['pression_amont']),
            min_value=0.0,
            step=1000.0
        )
        
        st.session_state.donnees_base['hauteur_geodesique_aspiration'] = st.number_input(
            "Hauteur géodésique aspiration (m)",
            value=float(st.session_state.donnees_base['hauteur_geodesique_aspiration']),
            step=0.1
        )
        
        st.session_state.donnees_base['npsh_requis'] = st.number_input(
            "NPSH requis (m)",
            value=float(st.session_state.donnees_base['npsh_requis']),
            min_value=0.0,
            step=0.1
        )
        
        # Paramètres coup de bélier
        st.subheader("Paramètres coup de bélier")
        st.session_state.donnees_base['epaisseur_conduite'] = st.number_input(
            "Épaisseur conduite (m)",
            value=float(st.session_state.donnees_base['epaisseur_conduite']),
            min_value=0.001,
            step=0.001,
            format="%.3f"
        )
        
        st.session_state.donnees_base['module_young_materiau'] = st.number_input(
            "Module d'Young matériau (Pa)",
            value=float(st.session_state.donnees_base['module_young_materiau']),
            min_value=1e9,
            step=1e9,
            format="%.0f"
        )
        
        # Import des données de pompe
        st.subheader("Données de pompe")
        
        # Template de données de pompe
        st.markdown('<div class="template-box">', unsafe_allow_html=True)
        st.write("**Template CSV pour pompe 50Hz:**")
        template_data = {
            'Débit': [0, 10, 20, 30, 40, 50, 60, 70],
            'HMT': [35, 34, 32, 29, 25, 20, 14, 7],
            'Puissance': [5.2, 6.1, 7.0, 7.5, 7.8, 7.5, 6.8, 5.5],
            'Rendement': [0, 45, 62, 68, 70, 65, 55, 40]
        }
        template_df = pd.DataFrame(template_data)
        st.dataframe(template_df, use_container_width=True)
        
        # Bouton pour télécharger le template
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger le Template CSV",
            data=csv_template,
            file_name="template_pompe_50Hz.csv",
            mime="text/csv"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Upload des données de pompe
        fichier_pompe = st.file_uploader("Importer courbe pompe 50Hz (CSV)", type=['csv'])
        if fichier_pompe is not None:
            try:
                st.session_state.donnees_pompe = pd.read_csv(fichier_pompe)
                st.success(f"✅ Données pompe chargées: {len(st.session_state.donnees_pompe)} points")
                
                # Aperçu des données importées
                st.write("**Aperçu des données importées:**")
                st.dataframe(st.session_state.donnees_pompe.head(), use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Erreur lecture fichier: {e}")
        else:
            st.info("📁 Importez un fichier CSV avec les colonnes: Débit, HMT, Puissance, Rendement")
        
        # Points singuliers
        st.subheader("Points Singuliers")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            type_singulier = st.selectbox(
                "Type de point singulier",
                options=list(st.session_state.coefficients_singuliers.keys())
            )
        
        with col2:
            quantite = st.number_input("Quantité", min_value=1, max_value=100, value=1, step=1)
        
        with col3:
            emplacement = st.selectbox(
                "Emplacement",
                options=['aspiration', 'refoulement']
            )
        
        if st.button("➕ Ajouter point singulier"):
            st.session_state.points_singuliers.append({
                'type': type_singulier,
                'quantite': quantite,
                'emplacement': emplacement
            })
            st.rerun()
        
        # Afficher la liste des points singuliers
        if st.session_state.points_singuliers:
            st.write("**Points singuliers ajoutés:**")
            for i, point in enumerate(st.session_state.points_singuliers):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {point['type']} (x{point['quantite']}) - {point['emplacement']}")
                with col2:
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.points_singuliers.pop(i)
                        st.rerun()


def exporter_pdf(resultats, calculateur):
    """Exporte les résultats en PDF avec graphiques"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Créer un style personnalisé pour les titres
    titre_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.HexColor('#1f77b4')
    )
    
    story = []
    
    # Fonction pour ajouter le filigrane en arrière-plan
    def add_watermark(canvas, doc):
        canvas.saveState()
        
        # Configuration du filigrane
        watermark_text = "By Viveleau 2025 - https://viveleau-services.com/ is the owner"
        
        # Positionner le filigrane en diagonale au centre de la page
        # Utiliser setFillColorRGB avec alpha pour la transparence
        canvas.setFillColorRGB(0, 0, 0, alpha=0.1)  # Noir avec transparence
        canvas.setFont("Helvetica", 16)
        
        # Rotation de 45 degrés
        canvas.rotate(45)
        
        # Positionner le filigrane au centre de la page
        # Répéter le filigrane sur toute la page
        for i in range(-3, 4):
            for j in range(-3, 4):
                canvas.drawCentredString(
                    x=100 + i * 200, 
                    y=100 + j * 150, 
                    text=watermark_text
                )
        
        canvas.restoreState()
    
    # Titre principal
    title = Paragraph("RAPPORT D'ANALYSE HYDRAULIQUE COMPLET", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Date et informations générales
    date_rapport = Paragraph(f"<b>Date du rapport:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
    story.append(date_rapport)
    story.append(Spacer(1, 20))
    
    # Section 1: Données de base
    story.append(Paragraph("1. DONNÉES DE BASE DU SYSTÈME", titre_style))
    
    data_base = [
        ['Paramètre', 'Valeur', 'Unité'],
        ['Diamètre intérieur', f"{resultats['diametre']:.3f}", 'm'],
        ['Matériau de la conduite', st.session_state.donnees_base['materiau'], ''],
        ['Débit nominal', f"{st.session_state.donnees_base['debit_m3h']:.1f}", 'm³/h'],
        ['Fluide', st.session_state.donnees_base['fluide'], ''],
        ['Température', f"{st.session_state.donnees_base['temperature']:.1f}", '°C'],
        ['Longueur totale conduite', f"{st.session_state.geometrie['longueur_totale']:.1f}", 'm'],
        ['Hauteur de montée', f"{st.session_state.geometrie['hauteur_montee']:.1f}", 'm'],
        ['Hauteur de descente', f"{st.session_state.geometrie['hauteur_descente']:.1f}", 'm']
    ]
    
    table_base = Table(data_base, colWidths=[200, 100, 50])
    table_base.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    story.append(table_base)
    story.append(Spacer(1, 20))
    
    # Section 2: Graphiques
    story.append(Paragraph("2. SCHÉMA ET COURBES CARACTÉRISTIQUES", titre_style))
    
    # Sauvegarder les graphiques dans des buffers mémoire
    try:
        # Graphique 1: Schéma de l'installation
        fig_schema = calculateur.dessiner_schema_installation()
        img_buffer1 = io.BytesIO()
        fig_schema.savefig(img_buffer1, format='png', dpi=150, bbox_inches='tight')
        img_buffer1.seek(0)
        
        story.append(Paragraph("<b>Schéma de l'installation:</b>", styles['Normal']))
        img_schema = Image(img_buffer1, width=6*inch, height=3*inch)
        story.append(img_schema)
        story.append(Spacer(1, 10))
        
        # Graphique 2: Courbe du réseau
        fig_courbe = calculateur.dessiner_courbe_reseau_pompes(resultats)
        img_buffer2 = io.BytesIO()
        fig_courbe.savefig(img_buffer2, format='png', dpi=150, bbox_inches='tight')
        img_buffer2.seek(0)
        
        story.append(Paragraph("<b>Courbe du réseau et caractéristiques pompes:</b>", styles['Normal']))
        img_courbe = Image(img_buffer2, width=6*inch, height=4*inch)
        story.append(img_courbe)
        
        # Fermer les figures pour libérer la mémoire
        plt.close(fig_schema)
        plt.close(fig_courbe)
        
    except Exception as e:
        story.append(Paragraph(f"<b>Erreur lors de la génération des graphiques:</b> {str(e)}", styles['Normal']))
    
    story.append(Spacer(1, 20))

        
    
    # Section 3: Résultats détaillés
    story.append(Paragraph("3. RÉSULTATS DES CALCULS DÉTAILLÉS", titre_style))
    
    # Sous-section 3.1: Propriétés du fluide
    story.append(Paragraph("3.1 Propriétés du fluide", styles['Heading2']))
    data_fluide = [
        ['Paramètre', 'Valeur', 'Unité'],
        ['Masse volumique', f"{resultats['proprietes_fluide']['masse_volumique']:.1f}", 'kg/m³'],
        ['Viscosité cinématique', f"{resultats['proprietes_fluide']['viscosite_cinematique']:.2e}", 'm²/s'],
        ['Pression de vapeur', f"{resultats['proprietes_fluide']['pression_vapeur']/1000:.1f}", 'kPa'],
        ['Régime d\'écoulement', resultats['regime_ecoulement'], '']
    ]
    
    table_fluide = Table(data_fluide, colWidths=[200, 100, 50])
    table_fluide.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8f5e8')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(table_fluide)
    story.append(Spacer(1, 10))
    
    # Sous-section 3.2: Caractéristiques d'écoulement
    story.append(Paragraph("3.2 Caractéristiques d'écoulement", styles['Heading2']))
    data_ecoulement = [
        ['Paramètre', 'Valeur', 'Unité'],
        ['Vitesse d\'écoulement', f"{resultats['vitesse']:.2f}", 'm/s'],
        ['Section d\'écoulement', f"{resultats['section']*10000:.1f}", 'cm²'],
        ['Nombre de Reynolds', f"{resultats['nombre_reynolds']:.0f}", ''],
        ['Coefficient de friction', f"{resultats['coefficient_friction']:.4f}", '']
    ]
    
    table_ecoulement = Table(data_ecoulement, colWidths=[200, 100, 50])
    table_ecoulement.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e3f2fd')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(table_ecoulement)
    story.append(Spacer(1, 10))
    
    # Sous-section 3.3: Pertes de charge
    story.append(Paragraph("3.3 Pertes de charge", styles['Heading2']))
    data_pertes = [
        ['Type de pertes', 'Valeur', 'Unité'],
        ['Pertes linéaires totales', f"{resultats['pertes_lineaires']:.2f}", 'm'],
        ['Pertes singulières totales', f"{resultats['pertes_singulieres']:.2f}", 'm'],
        ['Pertes d\'aspiration', f"{resultats['pertes_aspiration']:.2f}", 'm'],
        ['Pertes totales', f"{resultats['pertes_totales']:.2f}", 'm'],
        ['Hauteur manométrique totale', f"{resultats['hauteur_manometrique']:.2f}", 'm']
    ]
    
    table_pertes = Table(data_pertes, colWidths=[200, 100, 50])
    table_pertes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff3cd')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(table_pertes)
    story.append(Spacer(1, 10))
    
    # Sous-section 3.4: Puissances
    story.append(Paragraph("3.4 Calcul des puissances", styles['Heading2']))
    data_puissances = [
        ['Type de puissance', 'Valeur', 'Unité'],
        ['Puissance hydraulique', f"{resultats['puissances']['puissance_hydraulique']:.2f}", 'kW'],
        ['Puissance mécanique', f"{resultats['puissances']['puissance_mecanique']:.2f}", 'kW'],
        ['Puissance électrique', f"{resultats['puissances']['puissance_electrique']:.2f}", 'kW'],
        ['Rendement mécanique', f"{st.session_state.donnees_base['rendement_mecanique']*100:.1f}", '%'],
        ['Rendement électrique', f"{st.session_state.donnees_base['rendement_electrique']*100:.1f}", '%'],
        ['Rendement global', f"{(st.session_state.donnees_base['rendement_mecanique'] * st.session_state.donnees_base['rendement_electrique'])*100:.1f}", '%']
    ]
    
    table_puissances = Table(data_puissances, colWidths=[200, 100, 50])
    table_puissances.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0e6ff')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(table_puissances)
    story.append(Spacer(1, 10))
    
    # Sous-section 3.5: Analyse NPSH
    story.append(Paragraph("3.5 Analyse NPSH", styles['Heading2']))
    statut_npsh = "✅ SUFFISANT" if resultats['marge_npsh'] >= 0.5 else "⚠️ FAIBLE" if resultats['marge_npsh'] >= 0 else "❌ INSUFFISANT"
    
    data_npsh = [
        ['Paramètre NPSH', 'Valeur', 'Unité'],
        ['NPSH requis', f"{st.session_state.donnees_base['npsh_requis']:.2f}", 'm'],
        ['NPSH disponible', f"{resultats['npsh_disponible']:.2f}", 'm'],
        ['Marge NPSH', f"{resultats['marge_npsh']:.2f}", 'm'],
        ['Statut', statut_npsh, '']
    ]
    
    table_npsh = Table(data_npsh, colWidths=[200, 100, 50])
    table_npsh.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8d7da')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(table_npsh)
    story.append(Spacer(1, 10))
    
    # Sous-section 3.6: Analyse coup de bélier
    story.append(Paragraph("3.6 Analyse coup de bélier", styles['Heading2']))
    risque_belier = "ÉLEVÉ" if resultats['coup_belier']['surpression_max'] > 500000 else "MODÉRÉ" if resultats['coup_belier']['surpression_max'] > 200000 else "FAIBLE"
    
    data_belier = [
        ['Paramètre coup de bélier', 'Valeur', 'Unité'],
        ['Célérité de l\'onde', f"{resultats['coup_belier']['celerite_onde']:.0f}", 'm/s'],
        ['Temps de parcours', f"{resultats['coup_belier']['temps_parcours']:.2f}", 's'],
        ['Surpression maximale', f"{resultats['coup_belier']['surpression_max']/1000:.1f}", 'kPa'],
        ['Dépression au réservoir', f"{resultats['coup_belier']['depression_reservoir']:.2f}", 'm'],
        ['Niveau de risque', risque_belier, '']
    ]
    
    table_belier = Table(data_belier, colWidths=[200, 100, 50])
    table_belier.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fd7e14')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffe5d0')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(table_belier)
    
    # Construire le document avec le filigrane
    doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)
    buffer.seek(0)
    return buffer
# Le reste du code (fonction main()) reste inchangé...

def main():
    """Fonction principale de l'application"""
    
    st.markdown('<h1 class="main-header">🌊 Note de calcul pompage - By ViveLeau</h1>', 
                unsafe_allow_html=True)
    
    # Initialisation du calculateur
    calculateur = CalculateurPertesCharge()
    
    # Barre latérale
    afficher_sidebar()
    
    # Calculs
    try:
        resultats = calculateur.calculer_pertes_totales()
    except Exception as e:
        st.error(f"Erreur dans le calcul: {e}")
        return
    
    # Affichage du schéma et de la courbe côte à côte
    st.markdown('<div class="section-header">📐 Schéma de l\'Installation et Courbe du Réseau</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_schema = calculateur.dessiner_schema_installation()
        st.pyplot(fig_schema)
    
    with col2:
        fig_courbe = calculateur.dessiner_courbe_reseau_pompes(resultats)
        st.pyplot(fig_courbe)
    
    # Affichage des propriétés du fluide
    st.markdown('<div class="section-header">💧 Propriétés du Fluide</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Fluide", st.session_state.donnees_base['fluide'])
        st.metric("Température", f"{st.session_state.donnees_base['temperature']:.1f} °C")
        st.metric("Débit", f"{st.session_state.donnees_base['debit_m3h']:.1f} m³/h")
    
    with col2:
        st.metric("Masse volumique", f"{resultats['proprietes_fluide']['masse_volumique']:.1f} kg/m³")
        st.metric("Viscosité cinématique", f"{resultats['proprietes_fluide']['viscosite_cinematique']:.2e} m²/s")
        st.metric("Débit équivalent", f"{resultats['debit_m3s']:.4f} m³/s")
    
    with col3:
        st.metric("Pression de vapeur", f"{resultats['proprietes_fluide']['pression_vapeur']/1000:.1f} kPa")
        st.metric("Régime d'écoulement", resultats['regime_ecoulement'])
        st.metric("Vitesse écoulement", f"{resultats['vitesse']:.2f} m/s")
    
    # Affichage des résultats principaux
    st.markdown('<div class="section-header">📊 Résultats des Calculs</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.metric("Section d'écoulement", f"{resultats['section']*10000:.1f} cm²")
        st.metric("Nombre de Reynolds", f"{resultats['nombre_reynolds']:.0f}")
        st.metric("Coefficient de friction", f"{resultats['coefficient_friction']:.4f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.metric("Pertes linéaires", f"{resultats['pertes_lineaires']:.2f} m")
        st.metric("Pertes singulières", f"{resultats['pertes_singulieres']:.2f} m")
        st.metric("Pertes totales", f"{resultats['pertes_totales']:.2f} m")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.metric("Hauteur manométrique", f"{resultats['hauteur_manometrique']:.2f} m")
        st.metric("Puissance hydraulique", f"{resultats['puissances']['puissance_hydraulique']:.2f} kW")
        st.metric("Pertes aspiration", f"{resultats['pertes_aspiration']:.2f} m")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Calculs de puissance
    st.markdown('<div class="section-header">⚡ Calculs de Puissance</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.metric("Rendement mécanique", f"{st.session_state.donnees_base['rendement_mecanique']*100:.1f} %")
        st.metric("Puissance mécanique", f"{resultats['puissances']['puissance_mecanique']:.2f} kW")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.metric("Rendement électrique", f"{st.session_state.donnees_base['rendement_electrique']*100:.1f} %")
        st.metric("Puissance électrique", f"{resultats['puissances']['puissance_electrique']:.2f} kW")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.metric("Rendement global", f"{(st.session_state.donnees_base['rendement_mecanique'] * st.session_state.donnees_base['rendement_electrique'])*100:.1f} %")
        st.metric("Énergie spécifique", f"{resultats['puissances']['puissance_electrique']/st.session_state.donnees_base['debit_m3h']*1000:.2f} Wh/m³")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Analyse coup de bélier
    st.markdown('<div class="section-header">🌊 Analyse Coup de Bélier</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Célérité de l'onde", f"{resultats['coup_belier']['celerite_onde']:.0f} m/s")
        st.metric("Temps de parcours", f"{resultats['coup_belier']['temps_parcours']:.2f} s")
    
    with col2:
        st.metric("Pente Bergeron", f"{resultats['coup_belier']['pente_bergeron']:.2e}")
        st.metric("Surpression max", f"{resultats['coup_belier']['surpression_max']/1000:.1f} kPa")
    
    with col3:
        st.metric("Dépression réservoir", f"{resultats['coup_belier']['depression_reservoir']:.2f} m")
        st.metric("Module fluide", f"{resultats['proprietes_fluide']['module_elasticite']/1e9:.1f} GPa")
    
    with col4:
        # Évaluation du risque
        risque = "Élevé" if resultats['coup_belier']['surpression_max'] > 500000 else "Modéré" if resultats['coup_belier']['surpression_max'] > 200000 else "Faible"
        couleur_risque = "red" if risque == "Élevé" else "orange" if risque == "Modéré" else "green"
        st.markdown(f'<div style="background-color: {couleur_risque}20; padding: 1rem; border-radius: 10px; border-left: 5px solid {couleur_risque}">'
                   f'<h4 style="margin: 0; color: {couleur_risque}">Risque coup de bélier: {risque}</h4>'
                   f'</div>', unsafe_allow_html=True)
    
    # Résultats NPSH
    st.markdown('<div class="section-header">⚡ Analyse NPSH</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("NPSH requis", f"{st.session_state.donnees_base['npsh_requis']:.2f} m")
        st.metric("NPSH disponible", f"{resultats['npsh_disponible']:.2f} m")
    
    with col2:
        st.metric("Marge NPSH", f"{resultats['marge_npsh']:.2f} m")
        
        # Affichage conditionnel pour le NPSH
        if resultats['marge_npsh'] >= 0.5:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.success("✅ NPSH suffisant")
            st.write(f"Marge: {resultats['marge_npsh']:.2f} m")
            st.markdown('</div>', unsafe_allow_html=True)
        elif resultats['marge_npsh'] >= 0:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.warning("⚠️ Marge NPSH faible")
            st.write(f"Marge: {resultats['marge_npsh']:.2f} m")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.error("❌ NPSH insuffisant")
            st.write(f"Déficit: {abs(resultats['marge_npsh']):.2f} m")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.metric("Hauteur géodésique", f"{st.session_state.donnees_base['hauteur_geodesique_aspiration']:.2f} m")
        st.metric("Pression amont", f"{st.session_state.donnees_base['pression_amont']/1000:.1f} kPa")
    
    # Détails des pertes singulières
    if resultats['details_singuliers']:
        st.markdown('<div class="section-header">📋 Détail des Pertes Singulières</div>', unsafe_allow_html=True)
        
        details_data = []
        for detail in resultats['details_singuliers']:
            details_data.append({
                'Point singulier': detail['nom'],
                'Coefficient K': f"{detail['coefficient']:.3f}",
                'Perte de charge (m)': f"{detail['perte']:.4f}"
            })
        
        df_details = pd.DataFrame(details_data)
        st.dataframe(df_details, use_container_width=True)
    
    # Export des résultats
    st.markdown('<div class="section-header">📤 Export des Résultats</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export Excel
        if st.button("💾 Générer Rapport Excel Détaillé"):
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Feuille 1: Résultats principaux
                data_principale = {
                    'Paramètre': [
                        'Diamètre intérieur (m)', 'Matériau', 'Débit (m³/h)', 'Débit (m³/s)', 'Fluide',
                        'Température (°C)', 'Longueur totale (m)', 'Longueur aspiration (m)', 
                        'Hauteur de montée (m)', 'Hauteur de descente (m)', 'Vitesse d\'écoulement (m/s)',
                        'Section (m²)', 'Nombre de Reynolds', 'Coefficient de friction', 'Rugosité absolue (m)',
                        'Rugosité relative', 'Régime d\'écoulement', 'Pertes linéaires (m)', 'Pertes singulières (m)',
                        'Pertes totales (m)', 'Pertes aspiration (m)', 'Hauteur manométrique (m)',
                        'Puissance hydraulique (kW)', 'Puissance mécanique (kW)', 'Puissance électrique (kW)',
                        'Rendement mécanique', 'Rendement électrique', 'NPSH requis (m)', 'NPSH disponible (m)',
                        'Marge NPSH (m)', 'Célérité onde (m/s)', 'Temps parcours (s)', 'Surpression max (Pa)',
                        'Dépression réservoir (m)'
                    ],
                    'Valeur': [
                        f"{resultats['diametre']:.3f}", st.session_state.donnees_base['materiau'],
                        f"{st.session_state.donnees_base['debit_m3h']:.1f}", f"{resultats['debit_m3s']:.4f}",
                        st.session_state.donnees_base['fluide'], f"{st.session_state.donnees_base['temperature']:.1f}",
                        f"{st.session_state.geometrie['longueur_totale']:.1f}", f"{st.session_state.geometrie['longueur_aspiration']:.1f}",
                        f"{st.session_state.geometrie['hauteur_montee']:.1f}", f"{st.session_state.geometrie['hauteur_descente']:.1f}",
                        f"{resultats['vitesse']:.2f}", f"{resultats['section']:.6f}", f"{resultats['nombre_reynolds']:.0f}",
                        f"{resultats['coefficient_friction']:.4f}", f"{resultats['rugosite']:.6f}",
                        f"{resultats['rugosite_relative']:.6f}", resultats['regime_ecoulement'],
                        f"{resultats['pertes_lineaires']:.3f}", f"{resultats['pertes_singulieres']:.3f}",
                        f"{resultats['pertes_totales']:.3f}", f"{resultats['pertes_aspiration']:.3f}",
                        f"{resultats['hauteur_manometrique']:.3f}", f"{resultats['puissances']['puissance_hydraulique']:.3f}",
                        f"{resultats['puissances']['puissance_mecanique']:.3f}", f"{resultats['puissances']['puissance_electrique']:.3f}",
                        f"{st.session_state.donnees_base['rendement_mecanique']:.3f}", f"{st.session_state.donnees_base['rendement_electrique']:.3f}",
                        f"{st.session_state.donnees_base['npsh_requis']:.2f}", f"{resultats['npsh_disponible']:.3f}",
                        f"{resultats['marge_npsh']:.3f}", f"{resultats['coup_belier']['celerite_onde']:.0f}",
                        f"{resultats['coup_belier']['temps_parcours']:.2f}", f"{resultats['coup_belier']['surpression_max']:.0f}",
                        f"{resultats['coup_belier']['depression_reservoir']:.2f}"
                    ]
                }
                
                df_principale = pd.DataFrame(data_principale)
                df_principale.to_excel(writer, sheet_name='Résultats Principaux', index=False)
                
                # Feuille 2: Points singuliers
                if resultats['details_singuliers']:
                    data_singuliers = []
                    for detail in resultats['details_singuliers']:
                        data_singuliers.append({
                            'Point singulier': detail['nom'],
                            'Coefficient K': f"{detail['coefficient']:.3f}",
                            'Perte de charge (m)': f"{detail['perte']:.4f}"
                        })
                    
                    df_singuliers = pd.DataFrame(data_singuliers)
                    df_singuliers.to_excel(writer, sheet_name='Points Singuliers', index=False)
            
            st.download_button(
                label="📥 Télécharger le Rapport Excel",
                data=output.getvalue(),
                file_name=f"analyse_hydraulique_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    with col2:
        # Export PDF amélioré
        if st.button("📄 Générer Rapport PDF Complet"):
            pdf_buffer = exporter_pdf(resultats, calculateur)
            st.download_button(
                label="📥 Télécharger le Rapport PDF Complet",
                data=pdf_buffer.getvalue(),
                file_name=f"rapport_hydraulique_complet_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
            
          
if __name__ == "__main__":

    main()





