# -*- coding: utf-8 -*-
"""
Created on Sat Oct  8 12:55:51 2022

@author: khanh
"""



from __future__ import print_function, division
import os
import re
import sys

import pandas as pd
import numpy as np
from numpy import array,argmax,linalg as la

from keras.preprocessing.sequence import pad_sequences


DATA_DIR = '/home/anhvietnx1/acp-ope/'
pd.set_option('display.max_columns',None)
np.set_printoptions(threshold=np.inf)

def parse_stream(f, comment=b'#'):
    name = None
    sequence = []
    for line in f:
        if line.startswith(comment):
            continue
        line = line.strip()
        if line.startswith(b'>'):
            if name is not None:
                yield name, b''.join(sequence)
            name = line[1:]
            sequence = []
        else:
            sequence.append(line.upper())
    if name is not None:
        yield name, b''.join(sequence)

def fasta2csv(inFasta):
    FastaRead=pd.read_csv(inFasta,header=None)
    print(FastaRead.shape)
    print(FastaRead.head())
    seqNum=int(FastaRead.shape[0]/2)
    csvFile=open(os.path.join(DATA_DIR, "dataset", "testFasta.csv"),"w")
    csvFile.write("PID,Seq\n")
    
    #print("Lines:",FastaRead.shape)
    #print("Seq Num:",seqNum)
    for i in range(seqNum):
      csvFile.write(str(FastaRead.iloc[2*i,0])+","+str(FastaRead.iloc[2*i+1,0])+"\n")
            
         
    csvFile.close()
    TrainSeqLabel=pd.read_csv(os.path.join(DATA_DIR, "dataset", "testFasta.csv"),header=0)
    path=os.path.join(DATA_DIR, "dataset", "testFasta.csv")
    if os.path.exists(path):
     
        os.remove(path)  
     
    return TrainSeqLabel

inFastaTest=os.path.join(DATA_DIR, "dataset", "ACP20mainTest.fasta")

mainTest = fasta2csv(inFastaTest)

i=0
mainTest["Tags"]=mainTest["Seq"]
for pid in mainTest["PID"]:
  mainTest["Tags"][i]=pid[len(pid)-1]
  if mainTest["Tags"][i]=="1":
    mainTest["Tags"][i]=1
  else:
    mainTest["Tags"][i]=0
  i=i+1
ACP_y_test = mainTest["Tags"].values
ACP_y_test_ = np.array([np.array(i) for i in ACP_y_test])

x_test = {}
protein_index = 1
for line in mainTest["Seq"]:
  x_test[protein_index] = line
  protein_index = protein_index + 1
maxlen_test = max(len(x) for x in x_test.values())

maxlen = maxlen_test

#Convert amino acids to vectors
def OE(seq_temp):
    seq = seq_temp
    chars = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y']
    fea = []
    tem_vec =[]
    #k = 6
    for i in range(len(seq)):
        if seq[i] =='A':
            tem_vec = [1]
        elif seq[i]=='C':
            tem_vec = [2]
        elif seq[i]=='D':
            tem_vec = [3]
        elif seq[i]=='E' or seq[i]=='U':
            tem_vec = [4]
        elif seq[i]=='F':
            tem_vec = [5]
        elif seq[i]=='G':
            tem_vec = [6]
        elif seq[i]=='H':
            tem_vec = [7]
        elif seq[i]=='I':
            tem_vec = [8]
        elif seq[i]=='K':
            tem_vec = [9]
        elif seq[i]=='L':
            tem_vec = [10]
        elif seq[i]=='M' or seq[i]=='O':
            tem_vec = [11]
        elif seq[i]=='N':
            tem_vec = [12]
        elif seq[i]=='P':
            tem_vec = [13]
        elif seq[i]=='Q':
            tem_vec = [14]
        elif seq[i]=='R':
            tem_vec = [15]
        elif seq[i]=='S':
            tem_vec = [16]
        elif seq[i]=='T':
            tem_vec = [17]
        elif seq[i]=='V':
            tem_vec = [18]
        elif seq[i]=='W':
            tem_vec = [19]
        elif seq[i]=='X' or seq[i]=='B' or seq[i]=='Z':
            tem_vec = [20]    
        elif seq[i]=='Y':
            tem_vec = [21]
        #fea = fea + tem_vec +[i]
        fea.append(tem_vec)
    return fea

x_test_oe = []
for i in x_test:
  oe_feature = OE(x_test[i])
  x_test_oe.append(oe_feature)

x_test_ = np.array(pad_sequences(x_test_oe, padding='post', maxlen=maxlen))

handcraft_AAC_test = [[0] * 21 for _ in range(len(x_test_oe))]
for row in range(len(x_test_oe)):
  seq = x_test_oe[row]
  for i in seq:
    col = i[0]-1
    handcraft_AAC_test[row][col] += 1/len(seq)
hc_AAC_test = np.array(handcraft_AAC_test)

comb = []
for i in range(1,22):
  for j in range(i,22):
    comb.append([i,j])
comb_index = {}
for i in range(len(comb)):
  comb_index[tuple(comb[i])] = i

handcraft_DPC_test = [[0] * len(comb) for _ in range(len(x_test_oe))]
for row in range(len(x_test_oe)):
  seq = x_test_oe[row]
  for i in range(len(seq)-1):
    a = sorted([seq[i][0],seq[i+1][0]])
    index = comb_index[tuple(a)]
    handcraft_DPC_test[row][index] += 1/(len(seq)-1)
hc_DPC_test = np.array(handcraft_DPC_test)

def readFasta(file):
    if os.path.exists(file) == False:
        print('Error: "' + file + '" does not exist.')
        sys.exit(1)

    with open(file) as f:
        records = f.read()

    if re.search('>', records) == None:
        print('The input file seems not in fasta format.')
        sys.exit(1)

    records = records.split('>')[1:]
    myFasta = []
    for fasta in records:
        array = fasta.split('\n')
        name, sequence = array[0].split()[0], re.sub('[^ARNDCQEGHILKMFPSTWYV-]', '-', ''.join(array[1:]).upper())
        myFasta.append([name, sequence])

    return myFasta
def generateGroupPairs(groupKey):
    gPair = {}
    for key1 in groupKey:
        for key2 in groupKey:
            gPair[key1+'.'+key2] = 0
    return gPair


def CKSAAGP(fastas, gap = 5, **kw):

    group = {
        'alphaticr': 'GAVLMI',
        'aromatic': 'FYW',
        'postivecharger': 'KRH',
        'negativecharger': 'DE',
        'uncharger': 'STCPNQ'
    }

    AA = 'ARNDCQEGHILKMFPSTWYV'

    groupKey = group.keys()

    index = {}
    for key in groupKey:
        for aa in group[key]:
            index[aa] = key

    gPairIndex = []
    for key1 in groupKey:
        for key2 in groupKey:
            gPairIndex.append(key1+'.'+key2)

    encodings = []
    header = ['#']
    for g in range(gap + 1):
        for p in gPairIndex:
            header.append(p+'.gap'+str(g))
    encodings.append(header)

    for i in fastas:
        name, sequence = i[0], re.sub('-', '', i[1])
        code = [name]
        for g in range(gap + 1):
            gPair = generateGroupPairs(groupKey)
            sum = 0
            for p1 in range(len(sequence)):
                p2 = p1 + g + 1
                if p2 < len(sequence) and sequence[p1] in AA and sequence[p2] in AA:
                    gPair[index[sequence[p1]]+'.'+index[sequence[p2]]] = gPair[index[sequence[p1]]+'.'+index[sequence[p2]]] + 1
                    sum = sum + 1

            if sum == 0:
                for gp in gPairIndex:
                    code.append(0)
            else:
                for gp in gPairIndex:
                    code.append(gPair[gp] / sum)

        encodings.append(code)

    return encodings

handcraft_CKSAAGP_test = CKSAAGP(readFasta(inFastaTest))
handcraft_CKS_test = []
for i in range(1,len(handcraft_CKSAAGP_test)):
  handcraft_CKS_test.append(handcraft_CKSAAGP_test[i][1:])
hc_CKS_test = np.array(handcraft_CKS_test)

def TransDict_from_list(groups):
  transDict = dict()
  tar_list = ['0', '1', '2', '3', '4', '5', '6']
  result = {}
  index = 0
  for group in groups:
    g_members = sorted(group)  # Alphabetically sorted list
    for c in g_members:
        # print('c' + str(c))
        # print('g_members[0]' + str(g_members[0]))
        result[c] = str(tar_list[index])  # K:V map, use group's first letter as represent.
    index = index + 1
  return result
def translate_sequence(seq, TranslationDict):
  '''
  Given (seq) - a string/sequence to translate,
  Translates into a reduced alphabet, using a translation dict provided
  by the TransDict_from_list() method.
  Returns the string/sequence in the new, reduced alphabet.
  Remember - in Python string are immutable..
  '''
  import string
  from_list = []
  to_list = []
  for k, v in TranslationDict.items():
      from_list.append(k)
      to_list.append(v)
  # TRANS_seq = seq.translate(str.maketrans(zip(from_list,to_list)))
  TRANS_seq = seq.translate(str.maketrans(str(from_list), str(to_list)))
  # TRANS_seq = maketrans( TranslationDict, seq)
  return TRANS_seq
def get_3_protein_trids():
  nucle_com = []
  chars = ['0', '1', '2', '3', '4', '5', '6']
  base = len(chars)
  end = len(chars) ** 3
  for i in range(0, end):
      n = i
      ch0 = chars[n % base]
      n = n / base
      ch1 = chars[int(n % base)]
      n = n / base
      ch2 = chars[int(n % base)]
      nucle_com.append(ch0 + ch1 + ch2)
  return nucle_com
def get_4_nucleotide_composition(tris, seq, pythoncount=True):
  seq_len = len(seq)
  tri_feature = [0] * len(tris)
  k = len(tris[0])
  note_feature = [[0 for cols in range(len(seq) - k + 1)] for rows in range(len(tris))]
  if pythoncount:
      for val in tris:
          num = seq.count(val)
          tri_feature.append(float(num) / seq_len)
  else:
      # tmp_fea = [0] * len(tris)
      for x in range(len(seq) + 1 - k):
          kmer = seq[x:x + k]
          if kmer in tris:
              ind = tris.index(kmer)
              # tmp_fea[ind] = tmp_fea[ind] + 1
              note_feature[ind][x] = note_feature[ind][x] + 1
      # tri_feature = [float(val)/seq_len for val in tmp_fea]    #tri_feature type:list len:256
      u, s, v = la.svd(note_feature)
      for i in range(len(s)):
          tri_feature = tri_feature + u[i] * s[i] / seq_len
      # print tri_feature
      # pdb.set_trace()

  return tri_feature
def prepare_feature_kmer(infile):
  protein_seq_dict = {}
  protein_index = 1
  with open(infile, 'r') as fp:
    for line in fp:
      if line[0] != '>':
        seq = line[:-1]
        protein_seq_dict[protein_index] = seq
        protein_index = protein_index + 1
  kmer = []
  groups = ['AGV', 'ILFP', 'YMTS', 'HNQW', 'RK', 'DE', 'C']
  group_dict = TransDict_from_list(groups)
  protein_tris = get_3_protein_trids()
  # get protein feature
  # pdb.set_trace()
  for i in protein_seq_dict:  # and protein_fea_dict.has_key(protein) and RNA_fea_dict.has_key(RNA):
    protein_seq = translate_sequence(protein_seq_dict[i], group_dict)
    # print('oe:',shape(oe_feature))
    # pdb.set_trace()
    # RNA_tri_fea = get_4_nucleotide_composition(tris, RNA_seq, pythoncount=False)
    protein_tri_fea = get_4_nucleotide_composition(protein_tris, protein_seq, pythoncount =False)
    kmer.append(protein_tri_fea)
    protein_index = protein_index + 1
    # chem_fea.append(chem_tmp_fea)
  return np.array(kmer)

kmer_test = prepare_feature_kmer(inFastaTest)

hc_test = np.c_[hc_AAC_test,hc_DPC_test,hc_CKS_test,kmer_test]
hc_test.shape

#model esemble
import joblib
model1 = joblib.load(filename=os.path.join(DATA_DIR, 'models', 'bilstm_main7836.joblib'))
model2 = joblib.load(filename=os.path.join('/home/anhvietnx1/acp-ope/models/lgbm_main7865.joblib'))
model5 = joblib.load(filename=os.path.join(DATA_DIR, 'models', 'CNN_SF_144.joblib'))

result1 = model1.predict([x_test_,hc_test]).tolist()
result1_new = []
for i in result1:
  if i[0] < 0.5:
    result1_new.append(0)
  else:
    result1_new.append(1)
result1_new = np.array(result1_new)

x_test_1 = np.squeeze(x_test_)
X_test = np.c_[hc_test,x_test_1]
result2 = model2.predict(X_test)

x_test_oe = np.load(os.path.join(DATA_DIR, 'models', 'x_test_oe.npy'))
SF_test = np.load(os.path.join(DATA_DIR, 'models', 'SF_ALL_K_test.npy'))
result5 = model5.predict([x_test_oe,SF_test]).tolist()
result5_new = []
for i in result5:
  if i[0] < 0.5:
    result5_new.append(0)
  else:
    result5_new.append(1)
result5_new = np.array(result5_new)

final_result = []
for i in range(len(result1_new)):
  score = result1_new[i]*0.3 + result2[i]*0.5 + result5_new[i]*0.2
  if score >= 0.5:
    final_result.append(1)
  else:
    final_result.append(0)
final_result = np.array(final_result)


y_pred_bilstm = model1.predict([x_test_,hc_test]).ravel()

y_pred_lgbm = model2.predict_proba(X_test)[:, 1]

y_pred_cnn = model5.predict([x_test_oe,SF_test]).ravel()

y_pred_demi = []
y_pred_label = []
for i in range(len(y_pred_bilstm)):
  score = y_pred_bilstm[i]*0.2 + y_pred_lgbm[i]*0.6 + y_pred_cnn[i]*0.2
  y_pred_demi.append(score)
  if score > 0.5:
    y_pred_label.append(1)
  else:
    y_pred_label.append(0)
y_pred_demi = np.array(y_pred_demi)
y_pred_label = np.array(y_pred_label)

print('Prediction result: ', y_pred_label)

