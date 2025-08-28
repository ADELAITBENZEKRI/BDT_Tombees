import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO
import logging
import traceback
import numpy as np
import re
###

# Configuration d'accès
PASSWORD = "2025"  # Changez ce mot de passe

# Vérification de l'authentification
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Accès Application")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("auth_form"):
            password = st.text_input("Mot de passe d'accès:", type="password")
            if st.form_submit_button("🔓 Se connecter"):
                if password == PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Accès refusé")
    st.stop()

# Si authentifié, afficher l'application principale
st.sidebar.write(f"✅ Connecté")
if st.sidebar.button("🚪 Déconnexion"):
    st.session_state.authenticated = False
    st.rerun()
####


import json
import os
from datetime import datetime

def save_portfolio_to_file(portfolio_data):
    """Sauvegarder le portefeuille dans un fichier JSON"""
    try:
        # Convertir les objets non sérialisables en strings
        serializable_data = []
        for item in portfolio_data:
            serializable_item = item.copy()
            # Convertir les dates en strings
            if 'added_date' in serializable_item:
                serializable_item['added_date'] = str(serializable_item['added_date'])
            if 'maturity_date' in serializable_item:
                serializable_item['maturity_date'] = str(serializable_item['maturity_date'])
            serializable_data.append(serializable_item)
            
        with open('albarid_portfolio.json', 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde: {str(e)}")
        return False

def load_portfolio_from_file():
    """Charger le portefeuille depuis un fichier JSON"""
    try:
        if os.path.exists('albarid_portfolio.json'):
            with open('albarid_portfolio.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convertir les dates strings en objets datetime si nécessaire
                for item in data:
                    if 'added_date' in item and isinstance(item['added_date'], str):
                        try:
                            item['added_date'] = datetime.strptime(item['added_date'], '%d-%m-%Y %H:%M')
                        except:
                            pass
                return data
    except Exception as e:
        st.error(f"Erreur lors du chargement: {str(e)}")
    return []
    
###

def add_bam_footer_with_links():
    """Footer avec des liens réels modifiés selon les demandes"""
    footer_style = """
    <style>
    .bam-footer-real {
        position: relative;
        width: 100%;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        color: #495057;
        text-align: center;
        padding: 15px 0;
        font-size: 13px;
        border-top: 3px solid #d4af37;
        margin-top: 40px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .bam-footer-real a {
        color: #495057;
        text-decoration: none;
        margin: 0 15px;
        font-weight: 600;
        transition: color 0.3s ease;
    }
    .bam-footer-real a:hover {
        color: #0056b3;
        text-decoration: none;
    }
    .bam-footer-real .copyright {
        margin-bottom: 8px;
        font-weight: bold;
        color: #343a40;
    }
    .bam-footer-real .separator {
        color: #adb5bd;
        margin: 0 5px;
    }
    </style>
    """
    
    footer_html = """
    <div class="bam-footer-real">
        <div class="copyright">Copyright © AL BARID BANK 2025</div>
        <div class="links">
            <a href="/plan-site" target="_blank">Plan du site</a>
            <span class="separator">|</span>
            <a href="mailto:adelaitbenzekri@gmail.com">Contactez-nous</a>
            <span class="separator">|</span>
            <a href="https://www.bkam.ma" target="_blank">Liens utiles (BAM)</a>
        </div>
    </div>
    """
    
    st.markdown(footer_style, unsafe_allow_html=True)
    st.markdown(footer_html, unsafe_allow_html=True)

# Utilisation dans votre application
add_bam_footer_with_links()








##
st.sidebar.image("/content/logo ALBARID.png", width=300)
#
# Configuration de la page
st.set_page_config(page_title="Tableau de Bord d'Analyse des BDT", layout="wide")

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Titre
st.title("Tableau de Bord d'Analyse des Tombées de BDT")

# Initialisation de l'état de la session
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'raw_results' not in st.session_state:
    st.session_state.raw_results = None
if 'instruments_details' not in st.session_state:
    st.session_state.instruments_details = None

# Fonctions utilitaires
def number_to_text(value):
    """Convertit un nombre en texte avec unités (millions, milliards)"""
    try:
        value = abs(float(value))
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:,.2f} milliards"
        elif value >= 1_000_000:
            return f"{value / 1_000_000:,.2f} millions"
        else:
            return f"{value:,.2f}"
    except (ValueError, TypeError):
        return "N/A"

def format_amount(value):
    """Formate un montant avec sa représentation textuelle"""
    try:
        return f"{float(value):,.2f} ({number_to_text(value)})"
    except (ValueError, TypeError):
        return "N/A"

def safe_datetime_conversion(date_str, dayfirst=True):
    """Convertit une chaîne en datetime de manière sécurisée"""
    try:
        if pd.isna(date_str):
            return pd.NaT
        if isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, str) and date_str.strip() == '':
            return pd.NaT
        return pd.to_datetime(date_str, dayfirst=dayfirst, errors='coerce')
    except Exception:
        return pd.NaT

# Interface utilisateur
st.sidebar.header("Contrôles")
uploaded_file = st.sidebar.file_uploader("Télécharger un fichier Excel", type=["xls"])

# Création des onglets
tab1, tab2, tab3, tab4 = st.tabs(["Traitement des données", "Résultats des coupons", "Visualisations et rapports", "Portefeuille AL BARID BANK"])

with tab1:
    st.header("Traitement des données")
    
    if uploaded_file is not None:
        if st.button("Charger et traiter les données"):
            try:
                # Charger les données
                df = pd.read_excel(uploaded_file)
                st.session_state.raw_data = df
                
                # Traitement des données
                df_processed = df.copy()
                
                # 1. Supprimer la colonne "Valeur Nominale" si elle existe
                if 'Valeur Nominale' in df_processed.columns:
                    df_processed = df_processed.drop(columns=['Valeur Nominale'])
                
                # 2. Changement des noms de colonnes
                column_mapping = {
                    'Code ISIN': 'INSTRID',
                    'Maturit&eacute;': 'Maturite',
                    'Date d\'&eacute;mission': 'ISSUEDT',
                    'Date d\'&eacute;ch&eacute;ance': 'MATURITYDT_L',
                    'Taux Nominal %': 'INTERESTRATE'
                }
                
                df_processed = df_processed.rename(columns=column_mapping)
                
                # 3. Ajouter et initialiser PARVALUE à 100000 pour toutes les lignes
                df_processed['PARVALUE'] = 100000.0
                
                # 4. Suppression des espaces à l'intérieur des chiffres pour les autres colonnes numériques
                numeric_columns = ['Encours', 'INTERESTRATE', 'Prix Pied de Coupon %', 
                                  'Coupon Couru Unitaire', 'Prix']
                
                for col in numeric_columns:
                    if col in df_processed.columns:
                        df_processed[col] = df_processed[col].astype(str).apply(lambda x: re.sub(r'\s+', '', x))
                
                # Conversion des colonnes numériques
                for col in numeric_columns:
                    if col in df_processed.columns:
                        # Remplacer les virgules par des points
                        df_processed[col] = df_processed[col].str.replace(',', '.')
                        # Convertir en float
                        df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
                
                # 5. Ajout de la colonne ISSUESIZE = Encours / PARVALUE
                if 'Encours' in df_processed.columns:
                    df_processed['ISSUESIZE'] = df_processed['Encours'] / df_processed['PARVALUE']
                
                # 6. Ajout de la colonne INTERESTPERIODCTY basée sur la maturité
                def determine_periodicity(maturite):
                    if pd.isna(maturite):
                        return None
                    maturite = str(maturite).lower()
                    if 'ans' in maturite or '52 semaines' in maturite or '52 semaines' in maturite:
                        return 'ANLY'
                    elif '26 semaines' in maturite:
                        return 'HFLY'
                    elif '13 semaines' in maturite:
                        return 'QTLY'
                    else:
                        # Par défaut, on considère que c'est annuel
                        return 'ANLY'
                
                df_processed['INTERESTPERIODCTY'] = df_processed['Maturite'].apply(determine_periodicity)
                
                # Conversion des dates
                df_processed['MATURITYDT_L'] = df_processed['MATURITYDT_L'].apply(safe_datetime_conversion)
                df_processed['ISSUEDT'] = df_processed['ISSUEDT'].apply(safe_datetime_conversion)
                
                # Suppression des doublons basée sur INSTRID
                df_processed = df_processed.drop_duplicates(subset=['INSTRID'], keep='first')
                
                st.session_state.processed_data = df_processed
                st.session_state.step = 2
                
                st.success("Données traitées avec succès!")
                
                # Afficher un aperçu des données
                st.subheader("Aperçu des données traitées")
                st.dataframe(df_processed.head(), use_container_width=True)
                
            except Exception as e:
                st.error(f"Erreur lors du traitement: {str(e)}")
                logger.error(traceback.format_exc())
    
    elif st.session_state.processed_data is not None:
        st.subheader("Données déjà traitées")
        st.dataframe(st.session_state.processed_data.head(), use_container_width=True)
    else:
        st.info("Veuillez télécharger un fichier Excel pour commencer le traitement.")

with tab2:
    st.header("Résultats des coupons")
    
    if st.session_state.step >= 2 and st.session_state.processed_data is not None:
        if st.button("Calculer les coupons"):
            try:
                df = st.session_state.processed_data.copy()
                
                # Vérifier et supprimer les colonnes existantes pour éviter les doublons
                coupon_cols = [col for col in df.columns if 'CouponPayDate' in col or 'CouponAmount' in col or 'AnnualCouponAmount' in col]
                if coupon_cols:
                    df = df.drop(columns=coupon_cols)
                
                # Calcul du coupon annuel
                df["AnnualCouponAmount"] = df["Encours"] * (df["INTERESTRATE"] / 100)
                
                # Fonction pour calculer les dates de coupon
                def calculate_coupon_dates(row):
                    try:
                        issue_date = safe_datetime_conversion(row["ISSUEDT"])
                        maturity_date = safe_datetime_conversion(row["MATURITYDT_L"])
                        
                        if pd.isna(issue_date) or pd.isna(maturity_date):
                            return [maturity_date] if not pd.isna(maturity_date) else []
                        
                        frequency = str(row.get("INTERESTPERIODCTY", "")).upper()
                        coupon_dates = []

                        if frequency == "ANLY":  # Annuel
                            current_date = issue_date + relativedelta(years=1)
                            while current_date < maturity_date:
                                coupon_dates.append(current_date)
                                current_date = current_date + relativedelta(years=1)
                            
                        elif frequency == "HFLY":  # Semestriel
                            current_date = issue_date + relativedelta(months=6)
                            while current_date < maturity_date:
                                coupon_dates.append(current_date)
                                current_date = current_date + relativedelta(months=6)
                            
                        elif frequency == "QTLY":  # Trimestriel
                            current_date = issue_date + relativedelta(months=3)
                            while current_date < maturity_date:
                                coupon_dates.append(current_date)
                                current_date = current_date + relativedelta(months=3)
                        
                        # Ajouter la date de maturité comme dernier coupon
                        if not pd.isna(maturity_date) and maturity_date not in coupon_dates:
                            coupon_dates.append(maturity_date)

                        return sorted(coupon_dates)
                    except Exception as e:
                        logger.error(f"Erreur pour l'instrument {row.get('INSTRID', 'inconnu')}: {str(e)}")
                        return [maturity_date] if not pd.isna(maturity_date) else []
                
                # Fonction pour calculer le montant du coupon
                def calculate_coupon_amount(row, coupon_date):
                    try:
                        if pd.isna(coupon_date):
                            return 0
                        
                        freq = str(row.get("INTERESTPERIODCTY", "")).upper()
                        annual_coupon = row.get("AnnualCouponAmount", 0)
                        
                        if freq == "ANLY":
                            return annual_coupon
                        elif freq == "HFLY":
                            return annual_coupon / 2
                        elif freq == "QTLY":
                            return annual_coupon / 4
                        else:
                            # Par défaut, considérer comme annuel
                            return annual_coupon
                    except Exception as e:
                        logger.error(f"Erreur calcul coupon: {str(e)}")
                        return 0
                
                # Calcul des dates de coupon
                df["CouponPayDate"] = df.apply(calculate_coupon_dates, axis=1)
                
                # Déterminer le nombre maximum de coupons
                max_coupons = df["CouponPayDate"].apply(len).max() if not df["CouponPayDate"].empty else 0
                
                # Créer des colonnes pour chaque coupon
                for i in range(max_coupons):
                    df[f"CouponPayDate_{i+1}"] = df["CouponPayDate"].apply(
                        lambda x: x[i] if i < len(x) else pd.NaT
                    )
                    df[f"CouponAmount_{i+1}"] = df.apply(
                        lambda row: calculate_coupon_amount(row, row[f"CouponPayDate_{i+1}"]), 
                        axis=1
                    )
                
                # Formater les dates
                date_cols = [col for col in df.columns if "CouponPayDate" in col and col != "CouponPayDate"]
                for col in date_cols:
                    df[col] = df[col].apply(
                        lambda x: x.strftime('%d-%m-%Y') if not pd.isna(x) else ""
                    )
                
                st.session_state.processed_data = df
                st.session_state.step = 3
                
                st.success("Calcul des coupons terminé!")
                
                # Afficher un aperçu des données pour vérification
                st.subheader("Aperçu des données après calcul des coupons")
                preview_cols = ['INSTRID', 'ISSUESIZE', 'INTERESTRATE', 'AnnualCouponAmount']
                coupon_preview_cols = [col for col in df.columns if 'CouponAmount_' in col][:3]
                st.dataframe(df[preview_cols + coupon_preview_cols].head(), use_container_width=True)
                
            except Exception as e:
                st.error(f"Erreur lors du calcul des coupons: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Recherche d'instrument par INSTRID
        st.subheader("🔍 Recherche d'instrument")
        
        search_instr = st.text_input("Entrez l'INSTRID de l'instrument à rechercher:")
        
        if search_instr and st.session_state.processed_data is not None:
            instrument_data = st.session_state.processed_data[
                st.session_state.processed_data['INSTRID'].astype(str).str.contains(search_instr, case=False)
            ]
            
            if not instrument_data.empty:
                st.subheader(f"Résultats pour: {search_instr}")
                
                # Afficher les informations de base
                base_cols = ['INSTRID', 'ISSUEDT', 'MATURITYDT_L', 'INTERESTPERIODCTY', 'ISSUESIZE', 'INTERESTRATE', 'AnnualCouponAmount']
                st.dataframe(instrument_data[base_cols], use_container_width=True)
                
                # Afficher les détails des coupons
                coupon_cols = [col for col in instrument_data.columns if "CouponPayDate" in col or "CouponAmount" in col]
                if coupon_cols:
                    coupon_data = instrument_data[coupon_cols].copy()
                    # Transposer seulement les premières lignes pour éviter les problèmes de performance
                    coupon_data_transposed = coupon_data.head().transpose().reset_index()
                    coupon_data_transposed.columns = ['Colonne', 'Valeur']
                    st.subheader("Détails des coupons (premiers instruments)")
                    st.dataframe(coupon_data_transposed, use_container_width=True)
                    
                    # Calcul du total des coupons
                    amount_cols = [col for col in coupon_cols if 'Amount' in col]
                    total_coupons = instrument_data[amount_cols].sum().sum()
                    st.metric("Total des coupons", format_amount(total_coupons))
            else:
                st.warning(f"Aucun instrument trouvé avec INSTRID contenant '{search_instr}'")
    
    else:
        st.info("Veuillez d'abord traiter les données dans l'onglet 'Traitement des données'.")

with tab3:
    st.header("Visualisations et rapports")
    
    if st.session_state.step >= 3 and st.session_state.processed_data is not None:
        if st.button("Analyser les résultats et générer les visualisations"):
            try:
                df = st.session_state.processed_data.copy()
                
                # Fonction pour obtenir les coupons par mois/année
                def get_coupons_by_month_year(row):
                    coupons = {}
                    for i in range(1, 33):  # Jusqu'à 32 coupons possibles
                        date_col = f'CouponPayDate_{i}'
                        amount_col = f'CouponAmount_{i}'
                        
                        if date_col in df.columns and pd.notna(row.get(date_col, "")) and row[date_col] != "":
                            try:
                                date = safe_datetime_conversion(row[date_col], dayfirst=True)
                                if pd.isna(date):
                                    continue
                                    
                                month_year = (date.month, date.year)
                                amount = float(row[amount_col]) if pd.notna(row.get(amount_col, 0)) else 0
                                coupons[month_year] = coupons.get(month_year, 0) + amount
                            except Exception:
                                continue
                    return coupons
                
                results = {}
                instruments_details = {}
                
                for _, row in df.iterrows():
                    # Traitement des maturités
                    maturity_date = safe_datetime_conversion(row['MATURITYDT_L'])
                    if pd.notna(maturity_date):
                        month_year = (maturity_date.month, maturity_date.year)
                        issue_size = row['ISSUESIZE'] if pd.notna(row.get('ISSUESIZE', 0)) else 0
                        
                        if month_year not in results:
                            results[month_year] = {
                                'total_issuesize': 0,
                                'total_coupons': 0,
                                'instruments': set(),
                                'coupon_instruments': set()
                            }
                            instruments_details[month_year] = {
                                'maturity_instruments': [],
                                'coupon_instruments': []
                            }
                        
                        results[month_year]['total_issuesize'] += issue_size * 100000
                        results[month_year]['instruments'].add(row['INSTRID'])
                        instruments_details[month_year]['maturity_instruments'].append({
                            'INSTRID': row['INSTRID'],
                            'ISSUESIZE': issue_size * 100000,
                            'MATURITYDT': maturity_date.strftime('%d-%m-%Y') if pd.notna(maturity_date) else "N/A"
                        })
                    
                    # Traitement des coupons
                    coupons = get_coupons_by_month_year(row)
                    for month_year, amount in coupons.items():
                        if month_year not in results:
                            results[month_year] = {
                                'total_issuesize': 0,
                                'total_coupons': 0,
                                'instruments': set(),
                                'coupon_instruments': set()
                            }
                            instruments_details[month_year] = {
                                'maturity_instruments': [],
                                'coupon_instruments': []
                            }
                        
                        results[month_year]['total_coupons'] += amount
                        results[month_year]['coupon_instruments'].add(row['INSTRID'])

                        # Trouver la date exacte du coupon
                        coupon_date = None
                        for i in range(1, 33):
                            date_col = f'CouponPayDate_{i}'
                            if date_col in row and pd.notna(row.get(date_col, "")) and row[date_col] != "":
                                try:
                                    date = safe_datetime_conversion(row[date_col], dayfirst=True)
                                    if (date.month, date.year) == month_year:
                                        coupon_date = row[date_col]
                                        break
                                except Exception:
                                    continue

                        instruments_details[month_year]['coupon_instruments'].append({
                            'INSTRID': row['INSTRID'],
                            'CouponAmount': amount,
                            'CouponDate': coupon_date or "N/A"
                        })
                
                # Conversion des sets en listes
                for month_year in results:
                    results[month_year]['instruments'] = list(results[month_year]['instruments'])
                    results[month_year]['coupon_instruments'] = list(results[month_year]['coupon_instruments'])
                
                # Tri et filtrage des résultats
                sorted_results = sorted(results.items(), key=lambda x: (x[0][1], x[0][0]))
                filtered_results = [(m_y, data) for m_y, data in sorted_results 
                                  if (m_y[1] > 2024) or (m_y[1] == 2024 and m_y[0] >= 1)]
                
                st.session_state.results = filtered_results
                st.session_state.raw_results = results
                st.session_state.instruments_details = instruments_details
                st.session_state.step = 4
                
                st.success("Analyse terminée!")
                
            except Exception as e:
                st.error(f"Erreur lors de l'analyse: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Affichage des résultats
        if st.session_state.step >= 4:
            # Création du DataFrame de résultats
            results_df = []
            total_issuesize = 0
            total_coupons = 0
            
            for (month, year), data in st.session_state.results:
                month_name = f"{calendar.month_name[month]} {year}"
                total_issuesize += data['total_issuesize'] * 100000
                total_coupons += data['total_coupons'] * 100000
                
                results_df.append({
                    "Mois/Année": month_name,
                    "Taille Émission": data['total_issuesize'],
                    "Coupons": data['total_coupons'],
                    "Nb Instruments": len(data['instruments']),
                    "Total": data['total_issuesize'] + data['total_coupons']
                })
            
            results_df = pd.DataFrame(results_df)
            
            # Filtres
            st.sidebar.header("Filtres")
            years = sorted({y for (_, y), _ in st.session_state.results})
            selected_year = st.sidebar.selectbox("Année", years)
            
            months_in_year = sorted({m for (m, y), _ in st.session_state.results if y == selected_year})
            month_names = [calendar.month_name[m] for m in months_in_year]
            selected_month = st.sidebar.selectbox("Mois", month_names)
            
            # Visualisations
            st.header("Visualisations")
            selected_years = st.multiselect("Années à afficher", years, default=[selected_year])
            
            if selected_years:
                filtered_df = results_df[results_df['Mois/Année'].str.contains('|'.join(map(str, selected_years)))]
                
                if not filtered_df.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.bar(
                            filtered_df, 
                            x="Mois/Année", 
                            y=["Taille Émission", "Coupons"],
                            title="Taille d'émission et coupons",
                            barmode="group"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.line(
                            filtered_df,
                            x="Mois/Année",
                            y="Total",
                            title="Total (Taille + Coupons)"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Aucune donnée à afficher pour les années sélectionnées.")
            
            # Tableau complet
            st.header("Tous les résultats")
            
            # Préparation des données pour l'affichage
            display_data = []
            
            for (month, year), data in st.session_state.results:
                month_name = f"{calendar.month_name[month]} {year}"
                
                # Récupérer les détails des instruments
                details = st.session_state.instruments_details.get((month, year), {})
                
                # Instruments à maturité
                maturity_instruments = details.get('maturity_instruments', [])
                maturity_ids = "\n".join(instr['INSTRID'] for instr in maturity_instruments) if maturity_instruments else ""
                
                # Instruments avec coupons
                coupon_instruments = details.get('coupon_instruments', [])
                coupon_ids = "\n".join([instr['INSTRID'] for instr in coupon_instruments]) if coupon_instruments else ""
                
                display_data.append({
                    "Mois/Année": month_name,
                    "Total Taille Émission": data['total_issuesize'],
                    "Total Coupons": data['total_coupons'],
                    "Nb Instruments Maturité": len(maturity_instruments),
                    "Instruments Maturité": maturity_ids,
                    "Nb Instruments Coupons": len(coupon_instruments),
                    "Instruments Coupons": coupon_ids,
                    "Total (Taille Émission + Coupons)": data['total_issuesize'] + data['total_coupons']
                })
            
            # Création du DataFrame
            display_df = pd.DataFrame(display_data)
            
            # Formatage des montants
            display_df["Total Taille Émission"] = display_df["Total Taille Émission"].apply(format_amount)
            display_df["Total Coupons"] = display_df["Total Coupons"].apply(format_amount)
            display_df["Total (Taille Émission + Coupons)"] = display_df["Total (Taille Émission + Coupons)"].apply(format_amount)
            
            # Affichage du tableau avec mise en forme
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "Instruments Maturité": st.column_config.TextColumn(
                        "Instruments Maturité",
                        help="Liste des instruments arrivant à échéance ce mois",
                        width="medium"
                    ),
                    "Instruments Coupons": st.column_config.TextColumn(
                        "Instruments Coupons",
                        help="Liste des instruments payant des coupons ce mois",
                        width="medium"
                    )
                },
                hide_index=True
            )
            
            # Détails des instruments par mois
            st.header("Détails des instruments par mois")
            
            if hasattr(st.session_state, 'instruments_details'):
                # Sélection du mois
                months = sorted(st.session_state.instruments_details.keys(), key=lambda x: (x[1], x[0]))
                month_options = [f"{calendar.month_name[m]} {y}" for m, y in months]
                
                default_index = 0
                if month_options:
                    default_index = next((i for i, m in enumerate(month_options) if "2025" in m), 0)
                
                selected_month_str = st.selectbox(
                    "Sélectionnez un mois", 
                    month_options,
                    index=default_index
                )
                
                selected_index = month_options.index(selected_month_str)
                selected_month = months[selected_index]
                details = st.session_state.instruments_details.get(selected_month, {})
          
                # Calcul des sommes totales
                total_coupons = sum(instr['CouponAmount'] for instr in details.get('coupon_instruments', []))
                total_maturity = sum(instr['ISSUESIZE'] for instr in details.get('maturity_instruments', []))
                total_flux = total_coupons + total_maturity
                
                # Affichage des totaux avec style
                st.markdown("---")
                col_sum1, col_sum2, col_sum3 = st.columns(3)
                with col_sum1:
                    st.metric("Total coupons versés", format_amount(total_coupons), help="Somme des coupons payés ce mois")
                with col_sum2:
                    st.metric("Total capitaux à échéance", format_amount(total_maturity), help="Somme des capitaux arrivant à échéance ce mois")
                with col_sum3:
                    st.metric("Tombees totales du mois", 
                              format_amount(total_flux), 
                              help="Somme des flux financiers (coupons + capitaux)",
                              delta_color="off")
                
                st.markdown("""
                <style>
                    div[data-testid="stMetric"]:nth-child(3) {
                        border: 1px solid #ff4b4b;
                        border-radius: 5px;
                        background-color: #fff0f0;
                        padding: 5px;
                    }
                    div[data-testid="stMetric"]:nth-child(3) > div > label {
                        color: #ff4b4b !important;
                        font-weight: bold !important;
                    }
                    div[data-testid="stMetric"]:nth-child(3) > div > div {
                        color: #ff4b4b !important;
                        font-weight: bold !important;
                        font-size: 1.3rem !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Graphique combiné des flux
                if total_flux > 0:
                    flux_data = pd.DataFrame({
                        'Type': ['Coupons', 'Capitaux', 'Total'],
                        'Montant': [total_coupons, total_maturity, total_flux],
                        'Couleur': ['#1f77b4', '#ff7f0e', '#ff4b4b']
                    })
                    
                    fig_flux = px.bar(flux_data, 
                                    x='Type', 
                                    y='Montant',
                                    color='Couleur',
                                    title=f"Flux financiers - {selected_month_str}",
                                    labels={'Montant': 'Montant (MAD)', 'Type': ''},
                                    text=[format_amount(x) for x in flux_data['Montant']])
                    
                    fig_flux.update_traces(textposition='outside',
                                        marker_color=flux_data['Couleur'],
                                        showlegend=False)
                    fig_flux.update_layout(yaxis={'visible': False, 'showticklabels': False})
                    
                    st.plotly_chart(fig_flux, use_container_width=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"Instruments à échéance - {selected_month_str}")
                    if details.get('maturity_instruments'):
                        maturity_df = pd.DataFrame(details['maturity_instruments'])
                        maturity_df['ISSUESIZE'] = maturity_df['ISSUESIZE'].apply(format_amount)
                        st.dataframe(maturity_df, hide_index=True, use_container_width=True)
                        
                        fig1 = px.bar(maturity_df.sort_values('ISSUESIZE'), 
                                      x='INSTRID', 
                                      y='ISSUESIZE',
                                      title=f"Capital à échéance - {selected_month_str}",
                                      labels={'ISSUESIZE': 'Montant', 'INSTRID': 'Instrument'})
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("Aucun instrument arrivant à échéance ce mois-ci")
                
                with col2:
                    st.subheader(f"Instruments avec coupons - {selected_month_str}")
                    if details.get('coupon_instruments'):
                        coupon_df = pd.DataFrame(details['coupon_instruments'])
                        coupon_df['CouponAmount'] = coupon_df['CouponAmount'].apply(format_amount)
                        st.dataframe(coupon_df, hide_index=True, use_container_width=True)
                        
                        fig2 = px.bar(coupon_df.sort_values('CouponAmount'), 
                                    x='INSTRID', 
                                    y='CouponAmount',
                                    title=f"Coupons versés - {selected_month_str}",
                                    labels={'CouponAmount': 'Montant', 'INSTRID': 'Instrument'})
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Aucun coupon versé ce mois-ci")
            else:
                st.warning("Aucun détail d'instrument disponible. Veuillez relancer l'analyse.")
            
            # Téléchargement des données
            st.header("📥 Téléchargement des données")
            
            @st.cache_data
            def convert_to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                return output.getvalue()
            
            # Téléchargement des données avec coupons
            excel_data = convert_to_excel(st.session_state.processed_data)
            st.download_button(
                label="Télécharger les données avec coupons",
                data=excel_data,
                file_name="donnees_avec_coupons.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Nouvelle section pour générer des rapports
            st.subheader("Génération de rapports")
            
            # Sélection de l'année pour le rapport
            years = sorted({y for (_, y), _ in st.session_state.results})
            selected_dl_year = st.selectbox("Sélectionnez l'année pour le rapport", years)
            
            if st.button(f"Générer le rapport pour {selected_dl_year}"):
                # Création du DataFrame pour l'année sélectionnée
                year_data = []
                for (month, year), data in st.session_state.results:
                    if year == selected_dl_year:
                        month_name = calendar.month_name[month]
                        year_data.append({
                            'Mois': month_name,
                            'Total Maturités': data['total_issuesize'],
                            'Total Coupons': data['total_coupons'],
                            'Nb Instruments Maturité': len(st.session_state.instruments_details.get((month, year), {}).get('maturity_instruments', [])),
                            'Nb Instruments Coupons': len(st.session_state.instruments_details.get((month, year), {}).get('coupon_instruments', []))
                        })
                
                year_df = pd.DataFrame(year_data)
                
                # Création du fichier Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    year_df.to_excel(writer, sheet_name=f"Flux {selected_dl_year}", index=False)
                    
                    # Ajout des feuilles supplémentaires
                    if selected_dl_year in [2025, 2026]:
                        summary_df = pd.DataFrame([
                            {'Année': selected_dl_year, 
                             'Total Maturités': sum(x['ISSUESIZE'] for x in st.session_state.instruments_details.get((month, selected_dl_year), {}).get('maturity_instruments', [])),
                             'Total Coupons': sum(x['CouponAmount'] for x in st.session_state.instruments_details.get((month, selected_dl_year), {}).get('coupon_instruments', []))
                            } for month in range(1, 13) if (month, selected_dl_year) in st.session_state.instruments_details
                        ])
                        summary_df.to_excel(writer, sheet_name="Résumé", index=False)
                    
                    st.session_state.processed_data.to_excel(writer, sheet_name="Données complètes", index=False)
                
                st.download_button(
                    label=f"Télécharger le rapport {selected_dl_year}",
                    data=output.getvalue(),
                    file_name=f"rapport_flux_{selected_dl_year}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Bouton pour télécharger un rapport complet
            if st.button("Télécharger un rapport complet (2025-2026)"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Feuille 1: Résultats finaux 2025-2026
                    final_results = []
                    for (month, year), data in st.session_state.results:
                        if year in [2025, 2026]:
                            month_name = calendar.month_name[month]
                            final_results.append({
                                'Année': year,
                                'Mois': month_name,
                                'Total Maturités': data['total_issuesize'],
                                'Total Coupons': data['total_coupons'],
                                'Nb Instruments': len(data['instruments'])
                            })
                    pd.DataFrame(final_results).to_excel(writer, sheet_name="Résultats 2025-2026", index=False)
                    
                    # Feuille 2: Données traitées
                    st.session_state.processed_data.to_excel(writer, sheet_name="Données traitées", index=False)
                    
                    # Feuille 3: Résultats après 2026
                    post_2026 = []
                    for (month, year), data in st.session_state.results:
                        if year > 2026:
                            month_name = calendar.month_name[month]
                            post_2026.append({
                                'Année': year,
                                'Mois': month_name,
                                'Total Maturités': data['total_issuesize'],
                                'Total Coupons': data['total_coupons'],
                                'Nb Instruments': len(data['instruments'])
                            })
                    pd.DataFrame(post_2026).to_excel(writer, sheet_name="Résultats après 2026", index=False)
                
                st.download_button(
                    label="Télécharger le rapport complet",
                    data=output.getvalue(),
                    file_name="rapport_complet.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )



    with tab4:
        st.header("📊 Portefeuille d'AL BARID BANK")
        
        # Fonction pour sauvegarder automatiquement
        def save_portfolio_auto():
            """Sauvegarder automatiquement le portefeuille"""
            if 'portfolio' in st.session_state:
                save_portfolio_to_file(st.session_state.portfolio)
        
        # Initialisation du portefeuille dans session_state
        if 'portfolio' not in st.session_state:
            # Charger depuis le fichier
            st.session_state.portfolio = load_portfolio_from_file()
        
        # Section pour afficher tous les instruments disponibles et sélectionner ceux pour AL BARID BANK
        if st.session_state.processed_data is not None:
            st.subheader("📋 Tous les Instruments Disponibles sur le Marché")
            
            # Récupérer tous les INSTRID disponibles (convertir les Timestamps en strings)
            all_instruments_data = []
            for _, row in st.session_state.processed_data.iterrows():
                instrument = {
                    'INSTRID': row.get('INSTRID', ''),
                    'Encours': float(row.get('Encours', 0)),
                    'INTERESTRATE': float(row.get('INTERESTRATE', 0)) if row.get('INTERESTRATE') not in ['N/A', None] else 'N/A',
                    'MATURITYDT_L': str(row.get('MATURITYDT_L', 'N/A'))
                }
                all_instruments_data.append(instrument)
            
            all_instruments = pd.DataFrame(all_instruments_data)
            
            # Ajouter une colonne pour indiquer si l'instrument est dans le portefeuille
            all_instruments['Dans Portefeuille'] = all_instruments['INSTRID'].isin(
                [item['instr_id'] for item in st.session_state.portfolio]
            )
            
            # Afficher le nombre total d'instruments
            total_instruments = len(all_instruments)
            instruments_in_portfolio = all_instruments['Dans Portefeuille'].sum()
            
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            with col_stats1:
                st.metric("Instruments totaux", total_instruments)
            with col_stats2:
                st.metric("Dans portefeuille", instruments_in_portfolio)
            with col_stats3:
                st.metric("Disponibles", total_instruments - instruments_in_portfolio)
            
            # Filtres pour la recherche
            st.subheader("🔍 Filtres de Recherche")
            
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                search_text = st.text_input("Rechercher par INSTRID:", placeholder="MA...")
            
            with col_filter2:
                filter_in_portfolio = st.selectbox(
                    "Filtrer par statut:",
                    ["Tous", "Dans portefeuille", "Hors portefeuille"]
                )
            
            with col_filter3:
                # Option pour trier
                sort_option = st.selectbox(
                    "Trier par:",
                    ["INSTRID", "Encours (décroissant)", "Taux d'intérêt (décroissant)"]
                )
            
            # Appliquer les filtres
            filtered_instruments = all_instruments.copy()
            
            if search_text:
                filtered_instruments = filtered_instruments[
                    filtered_instruments['INSTRID'].str.contains(search_text, case=False, na=False)
                ]
            
            if filter_in_portfolio == "Dans portefeuille":
                filtered_instruments = filtered_instruments[filtered_instruments['Dans Portefeuille'] == True]
            elif filter_in_portfolio == "Hors portefeuille":
                filtered_instruments = filtered_instruments[filtered_instruments['Dans Portefeuille'] == False]
            
            # Appliquer le tri
            if sort_option == "INSTRID":
                filtered_instruments = filtered_instruments.sort_values('INSTRID')
            elif sort_option == "Encours (décroissant)":
                filtered_instruments = filtered_instruments.sort_values('Encours', ascending=False)
            elif sort_option == "Taux d'intérêt (décroissant)":
                # Filtrer les valeurs non numériques pour le tri
                numeric_instruments = filtered_instruments[filtered_instruments['INTERESTRATE'] != 'N/A']
                non_numeric_instruments = filtered_instruments[filtered_instruments['INTERESTRATE'] == 'N/A']
                numeric_instruments = numeric_instruments.sort_values('INTERESTRATE', ascending=False)
                filtered_instruments = pd.concat([numeric_instruments, non_numeric_instruments])
            
            # Afficher les instruments filtrés avec pagination
            st.subheader(f"📋 Instruments ({len(filtered_instruments)} résultats)")
            
            # Pagination
            items_per_page = 10
            total_pages = max(1, (len(filtered_instruments) + items_per_page - 1) // items_per_page)
            
            if total_pages > 1:
                page_number = st.number_input("Page:", min_value=1, max_value=total_pages, value=1)
                start_idx = (page_number - 1) * items_per_page
                end_idx = min(start_idx + items_per_page, len(filtered_instruments))
                current_instruments = filtered_instruments.iloc[start_idx:end_idx]
            else:
                current_instruments = filtered_instruments
            
            # Afficher chaque instrument avec option d'ajout/suppression
            for idx, instrument in current_instruments.iterrows():
                instr_id = instrument['INSTRID']
                
                # Trouver l'instrument dans le portefeuille s'il y est
                portfolio_item = next((item for item in st.session_state.portfolio 
                                    if item['instr_id'] == instr_id), None)
                
                col_inst1, col_inst2, col_inst3, col_inst4, col_inst5 = st.columns([2, 2, 2, 2, 1])
                
                with col_inst1:
                    st.write(f"**{instr_id}**")
                    status = "✅ Dans portefeuille" if instrument['Dans Portefeuille'] else "❌ Hors portefeuille"
                    st.write(status)
                
                with col_inst2:
                    st.write(f"**Taux:** {instrument.get('INTERESTRATE', 'N/A')}%")
                    st.write(f"**Maturité:** {instrument.get('MATURITYDT_L', 'N/A')}")
                
                with col_inst3:
                    st.write(f"**Encours total:** {format_amount(instrument.get('Encours', 0))}")
                    if portfolio_item:
                        st.write(f"**Part AL BARID:** {format_amount(portfolio_item.get('issue_size', 0))}")
                
                with col_inst4:
                    if instrument['Dans Portefeuille']:
                        # Modifier la quantité détenue par AL BARID
                        current_size = portfolio_item.get('issue_size', 0) / 1000000  # Convertir en millions
                        new_size = st.number_input(
                            f"ISSUESIZE AL BARID (M):",
                            min_value=0.0,
                            value=float(current_size),
                            step=0.1,
                            format="%.2f",
                            key=f"edit_{instr_id}"
                        )
                        
                        # Bouton pour mettre à jour
                        if st.button("🔄 Mettre à jour", key=f"update_{instr_id}"):
                            portfolio_index = next(i for i, item in enumerate(st.session_state.portfolio) 
                                                if item['instr_id'] == instr_id)
                            st.session_state.portfolio[portfolio_index]['issue_size'] = new_size * 1000000
                            save_portfolio_auto()  # Sauvegarde automatique
                            st.success(f"Quantité mise à jour pour {instr_id}!")
                            st.rerun()
                    else:
                        # Ajouter au portefeuille
                        al_barid_size = st.number_input(
                            f"ISSUESIZE AL BARID (M):",
                            min_value=0.0,
                            value=0.0,
                            step=0.1,
                            format="%.2f",
                            key=f"add_{instr_id}"
                        )
                
                with col_inst5:
                    if instrument['Dans Portefeuille']:
                        if st.button("🗑️", key=f"remove_{instr_id}", help="Retirer du portefeuille"):
                            st.session_state.portfolio = [item for item in st.session_state.portfolio 
                                                        if item['instr_id'] != instr_id]
                            save_portfolio_auto()  # Sauvegarde automatique
                            st.success(f"{instr_id} retiré du portefeuille!")
                            st.rerun()
                    else:
                        if st.button("➕", key=f"add_btn_{instr_id}", help="Ajouter au portefeuille") and al_barid_size > 0:
                            st.session_state.portfolio.append({
                                'instr_id': instr_id,
                                'issue_size': al_barid_size * 1000000,
                                'added_date': datetime.now().strftime("%d-%m-%Y %H:%M"),
                                'from_data': True,
                                'total_encours': float(instrument.get('Encours', 0)),
                                'interest_rate': float(instrument.get('INTERESTRATE', 0)) if instrument.get('INTERESTRATE') not in ['N/A', None] else 'N/A',
                                'maturity_date': str(instrument.get('MATURITYDT_L', 'N/A'))
                            })
                            save_portfolio_auto()  # Sauvegarde automatique
                            st.success(f"{instr_id} ajouté au portefeuille!")
                            st.rerun()
        
        # Section pour ajouter manuellement des instruments non présents dans les données
        st.subheader("➕ Ajouter un Instrument Manuellement")
        
        col_manual1, col_manual2, col_manual3 = st.columns([2, 2, 1])
        
        with col_manual1:
            manual_instr_id = st.text_input(
                "Code INSTRID:",
                key="manual_instr_input",
                placeholder="Ex: MA1234567890"
            )
        
        with col_manual2:
            manual_issue_size = st.number_input(
                "ISSUESIZE acheté par AL BARID (en millions):",
                min_value=0.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                key="manual_issue_input"
            )
        
        with col_manual3:
            st.write("")
            st.write("")
            if st.button("➕ Ajouter Manuellement", use_container_width=True):
                if manual_instr_id.strip() and manual_issue_size > 0:
                    # Vérifier si l'instrument existe déjà
                    existing_instr = next((item for item in st.session_state.portfolio 
                                        if item['instr_id'] == manual_instr_id), None)
                    
                    if existing_instr:
                        st.warning(f"L'instrument {manual_instr_id} existe déjà dans le portefeuille!")
                    else:
                        # Ajouter au portefeuille
                        st.session_state.portfolio.append({
                            'instr_id': manual_instr_id.strip(),
                            'issue_size': manual_issue_size * 1000000,
                            'added_date': datetime.now().strftime("%d-%m-%Y %H:%M"),
                            'from_data': False,
                            'total_encours': manual_issue_size * 1000000,
                            'interest_rate': 'N/A',
                            'maturity_date': 'N/A'
                        })
                        save_portfolio_auto()  # Sauvegarde automatique
                        st.success(f"Instrument {manual_instr_id} ajouté manuellement!")
                        st.rerun()
                else:
                    st.error("Veuillez remplir tous les champs correctement!")
    
        # Affichage du portefeuille actuel
        st.subheader("🎯 Portefeuille Actuel d'AL BARID BANK")
        
        if not st.session_state.portfolio:
            st.info("Le portefeuille est vide. Ajoutez des instruments pour commencer.")
        else:
            # Calcul des totaux
            total_investment = sum(item['issue_size'] for item in st.session_state.portfolio)
            total_instruments = len(st.session_state.portfolio)
            
            # Métriques
            col_met1, col_met2, col_met3, col_met4 = st.columns(4)
            
            with col_met1:
                st.metric("Nombre d'instruments", total_instruments)
            
            with col_met2:
                st.metric("Investissement total", format_amount(total_investment))
            
            with col_met3:
                avg_investment = total_investment / total_instruments if total_instruments > 0 else 0
                st.metric("Investissement moyen", format_amount(avg_investment))
            
            with col_met4:
                # Calcul de la part de marché
                if st.session_state.processed_data is not None:
                    total_market_encours = st.session_state.processed_data['Encours'].sum()
                    market_share = (total_investment / total_market_encours) * 100 if total_market_encours > 0 else 0
                    st.metric("Part de marché", f"{market_share:.2f}%")
            
            # Visualisations du portefeuille
            st.markdown("### 📊 Visualisations du Portefeuille")
            
            if total_instruments > 0:
                # Préparation des données pour visualisation
                portfolio_df = pd.DataFrame(st.session_state.portfolio)
                
                col_viz1, col_viz2 = st.columns(2)
                
                with col_viz1:
                    # Camembert de répartition
                    fig_pie = px.pie(
                        portfolio_df, 
                        values='issue_size', 
                        names='instr_id',
                        title="Répartition du Portefeuille par Instrument",
                        hover_data=['issue_size'],
                        labels={'issue_size': 'Montant', 'instr_id': 'Instrument'}
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_viz2:
                    # Bar chart des montants
                    fig_bar = px.bar(
                        portfolio_df.sort_values('issue_size', ascending=False),
                        x='instr_id',
                        y='issue_size',
                        title="Montant Investi par Instrument",
                        labels={'issue_size': 'Montant Investi', 'instr_id': 'Instrument'},
                        color='issue_size',
                        color_continuous_scale='Blues'
                    )
                    fig_bar.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_bar, use_container_width=True)
        
        # Section de sauvegarde et export
        st.markdown("---")
        st.subheader("💾 Sauvegarde du Portefeuille")
        
        col_save1, col_save2 = st.columns(2)
        
        with col_save1:
            if st.button("💾 Sauvegarder le Portefeuille", use_container_width=True):
                if st.session_state.portfolio:
                    if save_portfolio_to_file(st.session_state.portfolio):
                        st.success("Portefeuille sauvegardé avec succès!")
                    else:
                        st.error("Erreur lors de la sauvegarde!")
                else:
                    st.warning("Le portefeuille est vide!")
        
        with col_save2:
            if st.button("📤 Exporter le Portefeuille", use_container_width=True):
                if st.session_state.portfolio:
                    portfolio_df = pd.DataFrame(st.session_state.portfolio)
                    csv = portfolio_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name="portefeuille_al_barid_bank.csv",
                        mime="text/csv",
                        key="download_portfolio"
                    )
                else:
                    st.warning("Rien à exporter!")
        
        # Options avancées
        with st.expander("⚙️ Options Avancées"):
            st.warning("Zone de configuration avancée - Utiliser avec précaution")
            
            if st.button("🔄 Réinitialiser le Portefeuille"):
                st.session_state.portfolio = []
                save_portfolio_to_file([])  # Sauvegarder un portefeuille vide
                st.success("Portefeuille réinitialisé!")
                st.rerun()
            
            if st.button("📋 Importer depuis CSV"):
                uploaded_portfolio = st.file_uploader("Choisir un fichier CSV", type=['csv'])
                if uploaded_portfolio:
                    try:
                        import_df = pd.read_csv(uploaded_portfolio)
                        if {'instr_id', 'issue_size'}.issubset(import_df.columns):
                            st.session_state.portfolio = import_df.to_dict('records')
                            save_portfolio_auto()  # Sauvegarde automatique
                            st.success("Portefeuille importé avec succès!")
                            st.rerun()
                        else:
                            st.error("Le fichier CSV doit contenir les colonnes 'instr_id' et 'issue_size'")
                    except Exception as e:
                        st.error(f"Erreur lors de l'import: {str(e)}")

# Message initial
if st.session_state.step == 0:
    st.info("Veuillez télécharger un fichier Excel et suivre les étapes du processus.")