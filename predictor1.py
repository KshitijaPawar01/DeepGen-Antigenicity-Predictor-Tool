"""
DeepGEN - Protein Antigenicity Predictor
Fixed version with proper docstrings and complete main() function
"""

# ================================================================
# FIX 1: Ensure Python can load user-installed packages (tqdm, HF)
# ================================================================
import sys
import site

# Add user site-packages FIRST
sys.path.append(r"C:\Users\Kshitija\AppData\Roaming\Python\Python311\site-packages")

# ================================================================
# Standard libs
# ================================================================
import os
import re
import json
import csv
import time
import pandas as pd
import warnings
from pathlib import Path

# Third-party libs (these now load successfully)
import numpy as np
import pandas as pd
from tqdm import tqdm

# Machine learning
import torch
import joblib
import argparse
from sklearn.preprocessing import StandardScaler
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests

# BioPython
from Bio import SeqIO
from Bio.PDB import (
    PDBParser, DSSP, PPBuilder, NeighborSearch, ShrakeRupley
)
from Bio.PDB.vectors import calc_dihedral
from Bio.PDB import PDBParser, PPBuilder, Select, PDBIO, is_aa

# Graph analysis
import networkx as nx

# HuggingFace transformers
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification

warnings.filterwarnings("ignore")


# ====== GLOBAL OBJECTS ======
parser = PDBParser(QUIET=True)
sr = ShrakeRupley()

# ==========================
# PATH CONFIGURATION
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "results")
MODELS_DIR = os.path.join(BASE_DIR, "Models")

# Model paths
PROTBERT_DIR = os.path.join(MODELS_DIR, "checkpoint-334")
PHYSICO_MODEL_PATH = os.path.join(MODELS_DIR, "Physico_Gradient_Boosting.joblib")
STRUCT_MODEL_PATH = os.path.join(MODELS_DIR, "Structural_Gradient_Boosting.joblib")
AAINDEX_PATH = os.path.join(MODELS_DIR, "aaindex1.txt")

# Ensure required folders exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_SEQUENCES = 100

# Accuracy dictionary
ACCURACIES = {
    "protbert": 0.86,
    "physchem": 0.86,
    "struct": 0.73
}

# Consensus function
def consensus_prediction(prob_dict):
    probs = list(prob_dict.values())
    accs = [ACCURACIES[k] for k in prob_dict.keys()]
    weighted_prob = sum(p * a for p, a in zip(probs, accs)) / sum(accs)
    c_base = 2 * abs(weighted_prob - 0.5)
    c_final = c_base * (sum(accs) / len(accs))
    final_class = "Antigenic" if weighted_prob >= 0.5 else "Non-antigenic"
    return final_class, weighted_prob, c_final

# Load model + tokenizer
tokenizer = AutoTokenizer.from_pretrained(PROTBERT_DIR)
model = AutoModelForSequenceClassification.from_pretrained(PROTBERT_DIR)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# Sequence cleaning
valid_aa = set("ACDEFGHIKLMNPQRSTVWY")

def clean_sequence(seq):
    seq = seq.upper()
    if not set(seq).issubset(valid_aa):
        return None
    return seq

# Tokenization
def tokenize_sequences(sequences, max_length=1024):
    spaced_seqs = [" ".join(seq) for seq in sequences]
    encodings = tokenizer(
        spaced_seqs,
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt"
    )
    return encodings

# Load from FASTA
def load_sequences_from_fasta(fasta_path):
    sequences, ids = [], []
    for record in SeqIO.parse(fasta_path, "fasta"):
        if len(sequences) >= MAX_SEQUENCES:
            break
        cleaned_seq = clean_sequence(str(record.seq))
        if cleaned_seq is None:
            continue
        if len(cleaned_seq) > 10:
            sequences.append(cleaned_seq)
            ids.append(record.id)
    return ids, sequences

SIGNIFICANT_FEATURES = [
    "AAC_A","AAC_R","AAC_C","AAC_Q","AAC_H","AAC_L","AAC_S","AAC_T","AAC_V","DPC_AA","DPC_AR","DPC_AN","DPC_AL","DPC_AV","DPC_RA","DPC_RD","DPC_RL","DPC_RW","DPC_RV","DPC_NA","DPC_NQ","DPC_NG","DPC_NK","DPC_NP","DPC_NW","DPC_DR","DPC_DE","DPC_CN","DPC_CK","DPC_CP","DPC_CS","DPC_CT","DPC_QA","DPC_QN","DPC_QQ","DPC_QG","DPC_QI","DPC_QM","DPC_QS","DPC_EC","DPC_EQ","DPC_EE","DPC_EH","DPC_GN","DPC_GK","DPC_GT","DPC_GY","DPC_HA","DPC_HR","DPC_HI","DPC_HV","DPC_IH","DPC_LA","DPC_LR","DPC_KA","DPC_KG","DPC_MY","DPC_FA","DPC_PI","DPC_PS","DPC_SC","DPC_SQ","DPC_SS","DPC_ST","DPC_TE","DPC_TK","DPC_TT","DPC_WM","DPC_YQ","DPC_YL","DPC_VR","DPC_VQ","DPC_VI","DPC_VL","DPC_VV","ANDN920101_mean","ANDN920101_std","ARGP820101_mean","ARGP820101_std","ARGP820102_std","ARGP820103_std","BEGF750101_mean","BEGF750101_std","BEGF750103_mean","BHAR880101_std","BIGC670101_mean","BIGC670101_std","BIOV880102_std","BULH740101_mean","BULH740102_mean","BULH740102_std","BUNA790101_mean","BUNA790101_std","BUNA790102_mean","BUNA790103_mean","BURA740101_mean","BURA740101_std","CHAM810101_mean","CHAM820101_mean","CHAM820101_std","CHAM820102_mean","CHAM830101_mean","CHAM830101_std","CHAM830103_std","CHAM830104_mean","CHAM830106_mean","CHAM830106_std","CHAM830108_mean","CHOC750101_mean","CHOC750101_std","CHOC760101_mean","CHOC760101_std","CHOC760102_std","CHOC760103_std","CHOC760104_std","CHOP780101_mean","CHOP780101_std","CHOP780201_mean","CHOP780201_std","CHOP780202_mean","CHOP780203_mean","CHOP780203_std","CHOP780204_mean","CHOP780204_std","CHOP780205_mean","CHOP780206_mean","CHOP780206_std","CHOP780208_mean","CHOP780208_std","CHOP780209_mean","CHOP780210_mean","CHOP780210_std","CHOP780211_mean","CHOP780211_std","CHOP780212_mean","CHOP780212_std","CHOP780213_mean","CHOP780213_std","CHOP780214_mean","CHOP780214_std","CHOP780216_mean","CHOP780216_std","CIDH920101_mean","CIDH920101_std","CIDH920102_mean","CIDH920102_std","CIDH920103_mean","CIDH920104_mean","CIDH920104_std","CIDH920105_mean","CIDH920105_std","COHE430101_mean","CRAJ730102_mean","CRAJ730102_std","CRAJ730103_mean","DAWD720101_mean","DAWD720101_std","DAYM780201_mean","DAYM780201_std","DESM900102_std","EISD840101_std","EISD860102_mean","EISD860102_std","EISD860103_std","FASG760101_std","FASG760102_mean","FASG760103_mean","FASG760104_std","FASG760105_std","FAUJ880101_std","FAUJ880102_mean","FAUJ880102_std","FAUJ880103_mean","FAUJ880103_std","FAUJ880106_mean","FAUJ880106_std","FAUJ880107_mean","FAUJ880108_mean","FAUJ880108_std","FAUJ880109_std","FAUJ880110_mean","FAUJ880110_std","FAUJ880111_mean","FAUJ880111_std","FAUJ880113_mean","FAUJ880113_std","FINA770101_mean","FINA770101_std","FINA910101_mean","FINA910101_std","FINA910102_mean","FINA910102_std","FINA910104_mean","GARJ730101_std","GEIM800101_mean","GEIM800102_std","GEIM800103_std","GEIM800104_mean","GEIM800106_mean","GEIM800106_std","GEIM800107_mean","GEIM800108_mean","GEIM800108_std","GEIM800109_std","GEIM800110_mean","GEIM800110_std","GEIM800111_mean","GEIM800111_std","GOLD730101_mean","GOLD730101_std","GOLD730102_mean","GOLD730102_std","GRAR740101_mean","GRAR740101_std","GRAR740102_std","GRAR740103_mean","GRAR740103_std","GUYH850101_std","HOPA770101_mean","HOPA770101_std","HUTJ700101_mean","HUTJ700101_std","HUTJ700102_mean","HUTJ700102_std","HUTJ700103_mean","ISOY800101_mean","ISOY800101_std","ISOY800102_mean","ISOY800102_std","ISOY800103_mean","ISOY800103_std","ISOY800104_mean","ISOY800104_std","ISOY800106_std","ISOY800107_std","JANJ780101_std","JANJ780102_std","JANJ780103_std","JANJ790101_std","JANJ790102_std","JOND750101_mean","JOND750101_std","JOND920102_std","KANM800101_mean","KANM800102_mean","KANM800103_mean","KANM800103_std","KANM800104_mean","KARP850101_mean","KARP850101_std","KARP850103_std","KHAG800101_mean","KLEP840101_mean","KLEP840101_std","KRIW710101_std","KRIW790102_std","KRIW790103_mean","KRIW790103_std","KYTJ820101_std","LEVM760102_mean","LEVM760102_std","LEVM760103_mean","LEVM760104_mean","LEVM760104_std","LEVM760105_mean","LEVM760105_std","LEVM760106_mean","LEVM760106_std","LEVM760107_std","LEVM780101_mean","LEVM780103_mean","LEVM780103_std","LEVM780104_mean","LEVM780106_mean","LEVM780106_std","LEWP710101_mean","LIFS790101_mean","LIFS790102_mean","MANP780101_mean","MAXF760101_mean","MAXF760102_std","MAXF760104_mean","MAXF760104_std","MAXF760106_mean","MAXF760106_std","MCMT640101_std","MEIH800102_std","MEIH800103_std","NAGK730101_mean","NAGK730102_mean","NAGK730103_mean","NAGK730103_std","NAKH900104_std","NAKH900106_std","NAKH900107_mean","NAKH900108_mean","NAKH900108_std","NAKH900110_std","NAKH900111_mean","NAKH900111_std","NAKH920105_mean","NAKH920105_std","NAKH920108_mean","NAKH920108_std","NISK800101_mean","NISK860101_mean","NOZY710101_std","OOBM770101_std","OOBM770104_std","OOBM770105_std","OOBM850101_mean","OOBM850101_std","OOBM850102_std","OOBM850105_std","PALJ810101_mean","PALJ810102_mean","PALJ810102_std","PALJ810103_std","PALJ810104_mean","PALJ810105_mean","PALJ810106_mean","PALJ810106_std","PALJ810108_mean","PALJ810109_mean","PALJ810114_mean","PALJ810114_std","PALJ810115_mean","PALJ810116_mean","PARJ860101_mean","PLIV810101_mean","PONP800101_mean","PONP800102_std","PONP800103_std","PONP800104_mean","PONP800105_mean","PONP800105_std","PONP800108_std","PRAM820101_std","PRAM820102_mean","PRAM820102_std","PRAM820103_mean","PRAM900101_std","PRAM900102_mean","PRAM900104_mean","PRAM900104_std","PTIO830101_mean","PTIO830101_std","PTIO830102_mean","QIAN880101_mean","QIAN880102_mean","QIAN880103_mean","QIAN880104_mean","QIAN880105_mean","QIAN880106_mean","QIAN880106_std","QIAN880107_mean","QIAN880107_std","QIAN880108_mean","QIAN880108_std","QIAN880109_mean","QIAN880109_std","QIAN880110_mean","QIAN880110_std","QIAN880111_mean","QIAN880111_std","QIAN880112_mean","QIAN880113_mean","QIAN880114_mean","QIAN880114_std","QIAN880115_mean","QIAN880115_std","QIAN880116_mean","QIAN880116_std","QIAN880120_mean","QIAN880121_mean","QIAN880122_mean","QIAN880123_mean","QIAN880123_std","QIAN880124_mean","QIAN880125_mean","QIAN880125_std","QIAN880126_mean","QIAN880126_std","QIAN880127_std","QIAN880129_mean","QIAN880130_mean","QIAN880130_std","QIAN880131_mean","QIAN880131_std","QIAN880132_mean","QIAN880133_mean","QIAN880133_std","QIAN880134_mean","QIAN880134_std","QIAN880135_mean","QIAN880135_std","QIAN880136_mean","QIAN880137_std","QIAN880138_std","QIAN880139_mean","RACS770101_mean","RACS770102_std","RACS770103_std","RACS820101_mean","RACS820101_std","RACS820103_std","RACS820104_mean","RACS820104_std","RACS820106_mean","RACS820108_mean","RACS820108_std","RACS820110_mean","RACS820110_std","RACS820112_std","RACS820113_mean","RACS820114_mean","RADA880101_std","RADA880102_mean","RADA880103_std","RADA880104_std","RADA880105_std","RADA880106_mean","RADA880106_std","RADA880107_std","RADA880108_std","RICJ880101_std","RICJ880102_std","RICJ880103_mean","RICJ880103_std","RICJ880104_std","RICJ880105_mean","RICJ880106_std","RICJ880108_mean","RICJ880109_mean","RICJ880109_std","RICJ880110_mean","RICJ880111_std","RICJ880112_mean","RICJ880115_mean","RICJ880117_mean","ROBB760101_mean","ROBB760101_std","ROBB760102_mean","ROBB760102_std","ROBB760103_mean","ROBB760103_std","ROBB760104_mean","ROBB760105_mean","ROBB760106_mean","ROBB760108_mean","ROBB760109_mean","ROBB760110_mean","ROBB760110_std","ROBB760111_std","ROBB760112_mean","ROBB760112_std","ROBB760113_mean","ROBB790101_mean","ROSG850101_mean","ROSG850101_std","ROSG850102_std","ROSM880102_std","SIMZ760101_mean","SIMZ760101_std","SNEP660101_mean","SNEP660104_mean","SUEM840101_mean","SUEM840101_std","SWER830101_mean","TANS770101_mean","TANS770102_std","TANS770103_std","TANS770104_mean","TANS770104_std","TANS770105_std","TANS770107_mean","TANS770107_std","TANS770108_mean","TANS770109_mean","TANS770109_std","TANS770110_mean","TANS770110_std","VASM830101_mean","VASM830101_std","VASM830102_mean","VASM830103_std","VELV850101_mean","VENT840101_mean","VHEG790101_std","WARP780101_std","WERD780102_std","WOEC730101_std","WOLR810101_std","WOLS870103_mean","YUTK870101_mean","YUTK870102_mean","YUTK870103_mean","YUTK870104_mean","ZASB820101_std","ZIMJ680101_mean","ZIMJ680101_std","ZIMJ680102_mean","ZIMJ680102_std","ZIMJ680103_mean","ZIMJ680103_std","ZIMJ680104_mean","ZIMJ680104_std","AURR980101_mean","AURR980101_std","AURR980103_mean","AURR980104_mean","AURR980104_std","AURR980105_mean","AURR980105_std","AURR980106_std","AURR980108_std","AURR980109_mean","AURR980109_std","AURR980110_mean","AURR980111_mean","AURR980111_std","AURR980112_mean","AURR980112_std","AURR980113_mean","AURR980113_std","AURR980114_mean","AURR980114_std","AURR980115_mean","AURR980116_mean","AURR980117_mean","AURR980117_std","AURR980118_mean","AURR980119_std","AURR980120_std","ONEK900101_mean","ONEK900101_std","ONEK900102_mean","ONEK900102_std","VINM940102_mean","VINM940104_std","MUNV940101_mean","MUNV940101_std","MUNV940102_mean","MUNV940102_std","MUNV940103_mean","MUNV940104_mean","MUNV940104_std","MUNV940105_mean","MUNV940105_std","KIMC930101_mean","KIMC930101_std","BLAM930101_mean","BLAM930101_std","PARS000101_mean","PARS000102_std","KUMS000101_mean","KUMS000102_mean","KUMS000103_mean","KUMS000104_mean","TAKK010101_mean","TAKK010101_std","FODM020101_mean","FODM020101_std","NADH010101_mean","NADH010102_std","NADH010103_std","NADH010105_mean","NADH010105_std","NADH010106_std","NADH010107_mean","NADH010107_std","KOEP990101_mean","KOEP990102_std","FUKS010101_mean","FUKS010101_std","FUKS010102_std","FUKS010104_std","FUKS010105_mean","FUKS010105_std","FUKS010106_mean","FUKS010106_std","FUKS010107_std","FUKS010108_mean","FUKS010109_mean","FUKS010110_mean","FUKS010111_std","FUKS010112_mean","YANJ020101_mean","YANJ020101_std","TSAJ990101_mean","TSAJ990101_std","TSAJ990102_mean","TSAJ990102_std","COSI940101_mean","PONP930101_mean","WILM950101_mean","WILM950101_std","WILM950103_mean","WILM950103_std","KUHL950101_std","JURD980101_std","BASU050101_mean","BASU050102_mean","BASU050103_mean","SUYM030101_std","PUNT030101_std","GEOR030101_std","GEOR030102_std","GEOR030105_std","GEOR030106_std","GEOR030107_std","GEOR030108_mean","GEOR030109_mean","GEOR030109_std","ZHOH040101_mean","ZHOH040101_std","ZHOH040102_mean","ZHOH040102_std","BAEK050101_mean","HARY940101_mean","HARY940101_std","PONJ960101_mean","PONJ960101_std","DIGM050101_std","WOLR790101_std","OLSK800101_std","GUYH850103_mean","GUYH850104_std","GUYH850105_std","JACR890101_std","COWR900101_std","BLAS910101_mean","CORJ870101_std","CORJ870102_mean","CORJ870103_mean","CORJ870103_std","CORJ870104_mean","CORJ870104_std","CORJ870105_mean","CORJ870105_std","CORJ870106_mean","CORJ870106_std","CORJ870107_mean","CORJ870107_std","CORJ870108_mean","CORJ870108_std","MIYS990101_mean","MIYS990102_mean","MIYS990103_std","ENGD860101_std","FASG890101_std","KARS160101_std","KARS160102_std","KARS160103_std","KARS160104_std","KARS160105_mean","KARS160105_std","KARS160106_std","KARS160107_mean","KARS160107_std","KARS160108_std","KARS160109_mean","KARS160109_std","KARS160110_mean","KARS160110_std","KARS160111_mean","KARS160111_std","KARS160112_mean","KARS160112_std","KARS160113_std","KARS160114_mean","KARS160115_mean","KARS160117_std","KARS160118_std","KARS160119_std","KARS160121_std","KARS160122_mean","KARS160122_std","SMPP_ANDN920101_moment1","SMPP_ANDN920101_moment2","SMPP_ARGP820101_moment1","SMPP_ARGP820101_moment2","SMPP_ARGP820102_moment2","SMPP_ARGP820102_moment3","SMPP_ARGP820103_moment2","SMPP_ARGP820103_moment3","SMPP_BEGF750101_moment1","SMPP_BEGF750101_moment2","SMPP_BEGF750101_moment3","SMPP_BEGF750103_moment1","SMPP_BHAR880101_moment2","SMPP_BHAR880101_moment3","SMPP_BIGC670101_moment1","SMPP_BIGC670101_moment2","SMPP_BIOV880101_moment3"
]

class AntigenicFeatureExtractor:
    def __init__(self, aaindex_file_path=None):
        if aaindex_file_path is None:
            aaindex_file_path = os.path.join(MODELS_DIR, "aaindex1.txt")
        self.amino_acids = ['A','R','N','D','C','Q','E','G','H','I',
                            'L','K','M','F','P','S','T','W','Y','V']
        self.aaindex_properties = self.parse_aaindex_file(aaindex_file_path)

    def parse_aaindex_file(self, filepath):
        aaindex_data = {}
        canonical_order = list("ARNDCQEGHILKMFPSTWYV")
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
        except FileNotFoundError:
            print(f"AAindex file not found at {filepath}")
            return {}
        entries = content.split('//')
        for entry in entries:
            lines = entry.strip().split('\n')
            property_id = None
            description = None
            values = {}
            value_lines = []
            for i, line in enumerate(lines):
                l = line.strip()
                if l.startswith('H '):
                    property_id = l[2:].strip()
                elif l.startswith('D '):
                    description = l[2:].strip()
                elif l.startswith('I '):
                    vi = i + 2
                    while vi < len(lines):
                        vline = lines[vi].strip()
                        if not vline or vline[0] in "HDRJATCI/":
                            break
                        value_lines.append(vline)
                        vi += 1
                    float_values = []
                    for vblock in value_lines:
                        for v in vblock.split():
                            if v.upper() != "NA":
                                try:
                                    float_values.append(float(v))
                                except:
                                    pass
                    if len(float_values) >= 10:
                        for n, aa in enumerate(canonical_order):
                            if n < len(float_values):
                                values[aa] = float_values[n]
                    break
            if property_id and len(values) >= 10:
                mean_val = np.mean(list(values.values()))
                complete_values = {aa: values.get(aa, mean_val) for aa in canonical_order}
                aaindex_data[property_id] = {
                    'description': description if description else property_id,
                    'values': complete_values
                }
        return aaindex_data

    def read_fasta_file(self, filepath):
        sequences = []
        ids = []
        try:
            for record in SeqIO.parse(filepath, "fasta"):
                seq = str(record.seq).upper()
                clean_seq = ''.join([aa for aa in str(record.seq).upper() if aa in self.amino_acids])
                if len(clean_seq)>=10:
                    ids.append(record.id)
                    sequences.append(clean_seq)
        except Exception as e:
            print(f"Error reading FASTA file {filepath}: {e}")
        return ids, sequences

    def extract_amino_acid_composition(self, sequences):
        aac_features = []
        for seq in sequences:
            composition = []
            seq_length = len(seq)
            for aa in self.amino_acids:
                count = seq.count(aa)
                composition.append(count / seq_length if seq_length > 0 else 0)
            aac_features.append(composition)
        return np.array(aac_features)

    def extract_dipeptide_composition(self, sequences):
        dipeptides = [aa1 + aa2 for aa1 in self.amino_acids for aa2 in self.amino_acids]
        dpc_features = []
        for seq in sequences:
            composition = []
            total_dipeptides = len(seq) - 1 if len(seq) > 1 else 0
            for dipep in dipeptides:
                count = sum(1 for i in range(len(seq) - 1) if seq[i:i+2] == dipep)
                composition.append(count / total_dipeptides if total_dipeptides > 0 else 0)
            dpc_features.append(composition)
        return np.array(dpc_features)

    def extract_aaindex_features(self, sequences):
        aaindex_features = []
        for seq in sequences:
            seq_features = []
            for prop_id, prop_data in self.aaindex_properties.items():
                prop_values = prop_data['values']
                if len(seq) == 0:
                    seq_features.extend([0, 0, 0, 0])
                    continue
                values = [prop_values[aa] for aa in seq if aa in prop_values]
                if values:
                    seq_features.extend([
                        np.mean(values),
                        np.std(values) if len(values) > 1 else 0,
                        np.min(values),
                        np.max(values)
                    ])
                else:
                    seq_features.extend([0, 0, 0, 0])
            aaindex_features.append(seq_features)
        return np.array(aaindex_features)

    def extract_smpp_features(self, sequences, moments=[1, 2, 3]):
        smpp_features = []
        key_properties = list(self.aaindex_properties.keys())[:10]
        for seq in sequences:
            seq_features = []
            for prop_id in key_properties:
                if prop_id not in self.aaindex_properties:
                    continue
                prop_values = self.aaindex_properties[prop_id]['values']
                if len(seq) == 0:
                    seq_features.extend([0] * len(moments))
                    continue
                values = [prop_values[aa] for aa in seq if aa in prop_values]
                if values:
                    for moment in moments:
                        if moment == 1:
                            seq_features.append(np.mean(values))
                        elif moment == 2:
                            seq_features.append(np.var(values))
                        elif moment == 3:
                            if len(values) > 2:
                                mean_val = np.mean(values)
                                std_val = np.std(values)
                                skew = np.mean([((x - mean_val) / std_val) ** 3 for x in values]) if std_val > 0 else 0
                                seq_features.append(skew)
                            else:
                                seq_features.append(0)
                else:
                    seq_features.extend([0] * len(moments))
            smpp_features.append(seq_features)
        return np.array(smpp_features)

    def extract_all_features(self, sequences):
        aac_features = self.extract_amino_acid_composition(sequences)
        dpc_features = self.extract_dipeptide_composition(sequences)
        aaindex_features = self.extract_aaindex_features(sequences)
        smpp_features = self.extract_smpp_features(sequences)
        all_features = np.hstack([aac_features, dpc_features, aaindex_features, smpp_features])
        feature_names = []
        feature_names.extend([f'AAC_{aa}' for aa in self.amino_acids])
        dipeptides = [aa1 + aa2 for aa1 in self.amino_acids for aa2 in self.amino_acids]
        feature_names.extend([f'DPC_{dp}' for dp in dipeptides])
        for prop_id in self.aaindex_properties.keys():
            feature_names.extend([f'{prop_id}_mean', f'{prop_id}_std',
                                  f'{prop_id}_min', f'{prop_id}_max'])
        key_properties = list(self.aaindex_properties.keys())[:10]
        for prop_id in key_properties:
            feature_names.extend([f'SMPP_{prop_id}_moment1', f'SMPP_{prop_id}_moment2',
                                  f'SMPP_{prop_id}_moment3'])
        return all_features, feature_names


# Prediction
def predict(sequences, batch_size=16):
    all_probs, all_preds = [], []
    with torch.no_grad():
        for i in range(0, len(sequences), batch_size):
            batch_seqs = sequences[i:i+batch_size]
            encodings = tokenize_sequences(batch_seqs)
            input_ids = encodings["input_ids"].to(device)
            attention_mask = encodings["attention_mask"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)

            all_probs.extend(probs.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())
    return np.array(all_preds), np.array(all_probs)


# Load from PDB
def extract_sequence_from_pdb(pdb_path):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("pdb_struct", pdb_path)
    seq = "".join(str(pp.get_sequence()) for pp in PPBuilder().build_peptides(structure))
    pdb_id = os.path.splitext(os.path.basename(pdb_path))[0]
    return [pdb_id], [seq]


def predict_with_all_models(seq_ids, sequences, extractor, scaler,
                      struct_model=None, struct_scaler=None, pdb_paths=None):
    results = []

    # Load physicochemical model
    physico_model = joblib.load(PHYSICO_MODEL_PATH)

    if struct_model and pdb_paths:
        # This is for future structural features - currently not implemented
        struct_pred_dict = {}
    else:
        struct_pred_dict = {}

    for sid, seq in zip(seq_ids, sequences):
        # ProtBERT prediction
        _, protbert_probs = predict([seq])
        prob_protbert = protbert_probs[0,1]

        # Physicochemical prediction
        features, feature_names = extractor.extract_all_features([seq])
        features_df = pd.DataFrame(features, columns=feature_names)
        features_df = features_df[SIGNIFICANT_FEATURES]
        features = features_df.values

        if scaler is not None:
            try:
                features_scaled = scaler.transform(features)
            except Exception:
                features_scaled = features
        else:
            features_scaled = features

        prob_physico = physico_model.predict_proba(features_scaled)[0, 1]

        prob_struct = struct_pred_dict.get(sid, None)

        prob_dict = {
            "protbert": prob_protbert,
            "physchem": prob_physico
        }
        if prob_struct is not None:
            prob_dict["struct"] = prob_struct

        final_class, final_prob, confidence = consensus_prediction(prob_dict)

        results.append({
            "Sequence_ID": sid,
            "Sequence": seq,
            "ProtBERT_Prob": float(prob_protbert),
            "Physico_Prob": float(prob_physico),
            "Structural_Prob": float(prob_struct) if prob_struct is not None else None,
            "Consensus_Class": final_class,
            "Consensus_Prob": float(final_prob),
            "Consensus_Confidence": float(confidence)
        })

    return pd.DataFrame(results)


# =====================================================
#                VALIDATION FUNCTIONS
# =====================================================

def validate_fasta(filepath):
    r"""Validate FASTA file"""
    try:
        seq_ids, sequences = load_sequences_from_fasta(filepath)
        if not sequences:
            return False, "No valid sequences found in FASTA file"
        if any(len(seq) < 20 for seq in sequences):
            return False, "All sequences must be at least 20 amino acids long"
        return True, (seq_ids, sequences)
    except Exception as e:
        return False, f"FASTA validation error: {str(e)}"


def validate_pdb(filepath):
    r"""Validate PDB file"""
    try:
        seq_ids, sequences = extract_sequence_from_pdb(filepath)
        if not sequences:
            return False, "Could not extract sequence from PDB file"
        if any(len(seq) < 20 for seq in sequences):
            return False, "Sequence from PDB must be at least 20 amino acids long"
        return True, (seq_ids, sequences, filepath)
    except Exception as e:
        return False, f"PDB validation error: {str(e)}"


# =====================================================
#                PREDICTION RUNNER
# =====================================================

def run_prediction(data):
    r"""Run the actual prediction pipeline"""
    try:
        # Initialize extractor
        extractor = AntigenicFeatureExtractor(AAINDEX_PATH)
        
        # Check if we have PDB data
        if len(data) == 3:
            seq_ids, sequences, pdb_path = data
            pdb_paths = [pdb_path]
            struct_model = None  # Not loading struct model for now
        else:
            seq_ids, sequences = data
            pdb_paths = None
            struct_model = None
        
        # Run predictions
        results_df = predict_with_all_models(
            seq_ids=seq_ids,
            sequences=sequences,
            extractor=extractor,
            scaler=None,
            struct_model=struct_model,
            struct_scaler=None,
            pdb_paths=pdb_paths
        )
        
        # Convert DataFrame to list of dicts
        results = results_df.to_dict('records')
        
        # Convert numpy types to native Python types for JSON
        for result in results:
            for key, value in result.items():
                if hasattr(value, 'item'):
                    result[key] = value.item()
                elif value is None or (isinstance(value, float) and np.isnan(value)):
                    result[key] = None
        
        return results
        
    except Exception as e:
        import traceback
        return [{"error": f"Prediction failed: {str(e)}", "traceback": traceback.format_exc()}]

"""
Fixed output handling functions - REPLACE the save_outputs function
"""
'''
def save_outputs(results):
    """
    Save prediction results to JSON and CSV files in web-accessible directory
    
    Args:
        results: List of dictionaries containing prediction results
        
    Returns:
        dict: {
            "json_result": absolute_path_to_json,
            "csv_result": absolute_path_to_csv,
            "success": True/False
        }
    """
    try:
        # Generate timestamp for unique filenames
        timestamp = int(time.time() * 1000)  # Use milliseconds for uniqueness
        
        # Create output filenames
        json_filename = f"result_{timestamp}.json"
        csv_filename = f"result_{timestamp}.csv"
        
        json_file = os.path.join(RESULTS_DIR, json_filename)
        csv_file = os.path.join(RESULTS_DIR, csv_filename)
        
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4)
            os.chmod(json_file, 0o644)  # Make readable by web server
        except Exception as e:
            print(f"Error saving JSON: {str(e)}", file=sys.stderr)
            raise
        
        try:
            df = pd.DataFrame(results)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            os.chmod(csv_file, 0o644)  # Make readable by web server
        except Exception as e:
            print(f"Error saving CSV: {str(e)}", file=sys.stderr)
            raise
        
        if not os.path.exists(json_file):
            raise Exception(f"JSON file not created: {json_file}")
        if not os.path.exists(csv_file):
            raise Exception(f"CSV file not created: {csv_file}")
        
        return {
            "json_result": json_file,
            "csv_result": csv_file,
            "success": True
        }
        
    except Exception as e:
        print(f"Error saving outputs: {str(e)}", file=sys.stderr)
        return {
            "json_result": None,
            "csv_result": None,
            "success": False,
            "error": str(e)
        }


def main(input_path, file_type):
    r"""Main execution function called from PHP"""
    try:
        # Validate input file exists
        if not os.path.exists(input_path):
            return json.dumps({"error": "Input file not found on server.", "path": input_path})

        # Validate based on file type
        if file_type == "fasta":
            valid, data = validate_fasta(input_path)
        elif file_type == "pdb":
            valid, data = validate_pdb(input_path)
        else:
            return json.dumps({"error": f"Unsupported file type: {file_type}"})

        if not valid:
            return json.dumps({"error": data})

        # Run predictions
        results = run_prediction(data)
        
        # Check for errors in results
        if results and isinstance(results[0], dict) and "error" in results[0]:
            return json.dumps(results[0])
        
        # Save outputs - now returns dict with success flag
        output_result = save_outputs(results)
        
        if not output_result["success"]:
            return json.dumps({"error": output_result.get("error", "Failed to save output files")})
        
        return json.dumps({
            "status": "success",
            "json_result": output_result["json_result"],
            "csv_result": output_result["csv_result"],
            "count": len(results)
        })
        
    except Exception as e:
        import traceback
        return json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc()
        })
'''
# =====================================================
#                OUTPUT FUNCTIONS
# =====================================================

# NEW VERSION
def main(input_path, file_type):
    r"""Main execution function called from PHP"""
    try:
        # Validate input file exists
        if not os.path.exists(input_path):
            return json.dumps({"error": "Input file not found on server.", "path": input_path})

        # Validate based on file type
        if file_type == "fasta":
            valid, data = validate_fasta(input_path)
        elif file_type == "pdb":
            valid, data = validate_pdb(input_path)
        else:
            return json.dumps({"error": f"Unsupported file type: {file_type}"})

        if not valid:
            return json.dumps({"error": data})

        # Run predictions
        results = run_prediction(data)
        
        # Check for errors in results
        if results and isinstance(results[0], dict) and "error" in results[0]:
            return json.dumps(results[0])
        
        # Save outputs
        json_out, csv_out = save_outputs(results)

        return json.dumps({
            "status": "success",
            "json_result": json_out,
            "csv_result": csv_out,
            "count": len(results)
        })
        
    except Exception as e:
        import traceback
        return json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc()
        })


# =====================================================
#                MAIN ENTRY POINT
# =====================================================

def main(input_path, file_type):
    r"""Main execution function called from PHP"""
    try:
        # Validate input file exists
        if not os.path.exists(input_path):
            return json.dumps({"error": "Input file not found on server.", "path": input_path})

        # Validate based on file type
        if file_type == "fasta":
            valid, data = validate_fasta(input_path)
        elif file_type == "pdb":
            valid, data = validate_pdb(input_path)
        else:
            return json.dumps({"error": f"Unsupported file type: {file_type}"})

        if not valid:
            return json.dumps({"error": data})

        # Run predictions
        results = run_prediction(data)
        
        # Check for errors in results
        if results and isinstance(results[0], dict) and "error" in results[0]:
            return json.dumps(results[0])
        
        # Save outputs
        json_out, csv_out = save_outputs(results)

        return json.dumps({
            "status": "success",
            "json_result": json_out,
            "csv_result": csv_out,
            "count": len(results)
        })
        
    except Exception as e:
        import traceback
        return json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc()
        })

# =====================================================
#                CLI EXECUTION
# =====================================================

if __name__ == "__main__":
    try:
        # Enable better error output
        sys.stderr = sys.stdout
        
        if len(sys.argv) < 3:
            print(json.dumps({
                "error": "Usage: predictor.py <input_path> <file_type>",
                "example": "predictor.py input.fasta fasta"
            }))
            sys.exit(1)
        
        input_file = sys.argv[1]
        file_type = sys.argv[2].lower()
        
        # Execute main and print result
        result = main(input_file, file_type)
        print(result)
        
    except Exception as e:
        import traceback
        print(json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc()
        }))
        sys.exit(1)
