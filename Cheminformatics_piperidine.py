# -*- coding: utf-8 -*-
"""TF_grupo6.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1l0OO4iyAjpBTqRXNDHbPkByzdk4QBE5C

> **Objetivo**

Nuestro grupo de trabajo recibió una propuesta para colaborar y desarrollar un nuevo tratamiento para la Equizofrenia. Es por esto que nos planteamos realizar una análisis quimioinformático para obtener una lista de candidatos a droga que contengan piperidina.

#Preparación de la notebook

En la celda que se encuentra a continuación vamos a importar e instalar todas las librerías que se van a usar.

- Instalación: Usando el comando !pip install seguido del nombre de las librerias.

- Importación: Usando el comando import vamos a poder utilizar las librerias instaladas.
"""

# Instalar las librerias
!pip install pandas rdkit rdkit tqdm useful_rdkit_utils seaborn scikit-posthocs chembl_downloader chembl_webresource_client xlsxwriter git+https://github.com/ikmckenz/adme-pred-py.git pubchempy

# Importar libreria para cambiar el directorio y guardar archivos
import os
# Importar libreria para ver una barra con el progreso de cada comando
from tqdm.auto import tqdm
tqdm.pandas()
# Importar librerias para guardar, trabajar con tablas y grandes cantidades de datos
import pandas as pd
import numpy as np
# Importar las librerias de RDKit
from rdkit import Chem, DataStructs
from rdkit.Chem import Draw, AllChem
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem.Fingerprints import FingerprintMols
from rdkit.Chem.Draw import SimilarityMaps
from rdkit.Chem import PandasTools
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem import Descriptors
# Importar libreria de PubChem
import pubchempy as pcp
# Importar libreria de ChEMBL
from chembl_webresource_client.new_client import new_client
# Importar libreria de IPython para visualizar moléculas
from IPython.display import SVG
# Importar las librerias para graficar
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.gridspec as gridspec
import seaborn as sns
# Importar libreria de ADME
from adme_pred import ADME
# Importar las funciones de 'scipy'
from scipy.cluster.hierarchy import dendrogram, linkage, is_valid_linkage, cut_tree
# Importar las funciones de 'sklearn'
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import AgglomerativeClustering
from sklearn import metrics
# Importar el módulo sys
import sys
np.set_printoptions(threshold=sys.maxsize)
# Importar el módulo de advertencias
import warnings
import time

# Configurar el manejo de advertencias
warnings.filterwarnings('ignore')

"""# Búsqueda bibliográfica tanto del grupo funcional como de las características de la patología.

La esquizofrenia es una enfermedad psiquiátrica caracterizada por un conjunto de síntomas que incluyen el delirio y las alucinaciones, conocidos como los síntomas clásicos de la psicosis o síntomas positivos:
 * Desorganización del pensamiento,
 * Síntomas deficitarios de función cerebral como la reducción de las emociones, el lenguaje y la motivación,
 * Disminución en la función cognitiva.

> Se cree que la esquizofrenia es una interacción compleja entre factores predisponentes genéticos y ambientales que afectan la función cerebral al perturbar la cognición, el procesamiento y la interpretación de estímulos y experiencias.
> > Tratamiento:
Se utilizan antipsicóticos de primera (típicos)  y/o segunda generación(atípicos). Estos actúan principalmente sobre los síntomas positivos.
> > > Estos medicamentos funcionan al afectar los neurotransmisores en el cerebro, como la dopamina y la serotonina, para aliviar los síntomas de la esquizofrenia, como alucinaciones, delirios, pensamiento desorganizado.
> > > > En particular, en el campo de los antipsicóticos, algunos compuestos que contienen el **grupo piperidina** han demostrado actividad antipsicótica y han sido utilizados en la práctica clínica.

**Se nos propuso que la busqueda se base en moléculas que posean al grupo piperidina para sugerirlas como candidatas.**

Busqueda del grupo funcional utilizando bases de datos

- https://pubchem.ncbi.nlm.nih.gov/compound/8082
- https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL15487/

**Características del grupo funcional:**

La piperidina es un componente que se encuntra en el cerebro de los mamíferos y allí afecta el mecanismo sináptico en el SNC e influye en los mecanismos neurales que gobiernan la regulación del comportamiento emocional, el sueño y la función extrapiramidal.

La piperidina es un compuesto orgánico de fórmula molecular (CH2)5NH. Esta amina heterocíclica consta de un anillo de seis miembros que contiene cinco puentes de metileno y un puente de amina.
"""

# Exploración: interactuamos con la base de datos ChEMBL, y obtenemos información de moleculas que coinicden con el nombre "Piperdine"
piperidine = new_client.molecule.filter(pref_name__iexact='piperidine')
piperidine

# Identificadores
# InChI=1S/C5H11N/c1-2-4-6-5-3-1/h6H,1-5H2
# InChIKey=NQRYJNQNLNOLGT-UHFFFAOYSA-N
# SMILES=C1CCNCC1

"""# Recolectar los datos de ChEMBL las moléculas que tengan Piperidina como subestructura y que tengan una fase máxima de ensayos clínicos de 4."""

# Filtramos de la base de datos deChEMBL aquellas moléculas que cumplan con los dos requisitos pedidos.
substructure_piperidine = new_client.substructure.filter(smiles="C1CCNCC1", max_phase = 4)
print(len(substructure_piperidine))
# Obtenemos un tabla de 112 moleculas

"""# Explorar la diversidad estructural haciendo una clusterización por fingerprints"""

### Preparación de las tablas

#Filtrar los datos utilizando el SMILES como identificador y seleccionar solo las columnas 'molecule_chembl_id' y 'molecule_structures'.
data = new_client.substructure.filter(smiles="C1CCNCC1", max_phase = 4).only(['molecule_chembl_id', 'molecule_structures'])
#Generar una tabla con los datos obtenidos
data_frame = pd.DataFrame.from_dict(data)

#El identificador SMILES de cada molécula se encuntra contenido en la columna "molecule_structures. Entonces vamos a extraer esta información.
lista_smiles = []                                                   # Armar una lista vacia donde vamos a guardar los smiles
for i in range(len(data_frame)):
  smiles = data_frame["molecule_structures"][i]["canonical_smiles"] # Recorrer cada fila de la columna de "molecula_structure" de la tabla "data_frame y asignarle el smiles correspondiente
  lista_smiles.append(smiles)                                       # Agregar a la lista cada smiles obtenido a la lista "lista_smiles"
data_frame["canonical_smiles"] = lista_smiles                       # Agregar la columna a nuestro data frame

chEMBL_id = data_frame['molecule_chembl_id']
smiles = data_frame['canonical_smiles']                                 # Seleccionar la columna de los smiles
tabla_piperidine = pd.DataFrame()                                       # Generar una tabla que contenga los smiles
IDs = range(0,112)
tabla_piperidine["ID"] = IDs
tabla_piperidine['chEMBL_ID'] = chEMBL_id
tabla_piperidine['smiles'] = smiles
PandasTools.AddMoleculeColumnToFrame(tabla_piperidine, smilesCol='smiles') # Agregar una columna de moléculas a la tabla utilizando la columna 'smiles'

tabla_piperidine.head(2)

### Clusterizacion por Fingerprint

fps = [FingerprintMols.FingerprintMol(mol) for mol in tabla_piperidine['ROMol']]   # Crear una lista de huellas moleculares para cada molécula en la columna 'ROMol'
type(fps[0])                                                                       # Por el tipo de datos necesitamos crea un array llamado 'vector' a partir del primer elemento de la lista 'fps'
vector = np.array(fps[0])

size = len(tabla_piperidine)          # Obtener el tamaño de la tabla 'tabla_piperidine'
hmap = np.empty(shape=(size, size))   # Crear un arreglo vacío para almacenar la matriz de similitud

table = pd.DataFrame()                                                                # Crear un DataFrame vacío
for i in range(len(tabla_piperidine)):                                                # Iterar sobre las filas de la tabla
    for j in range(len(tabla_piperidine)):                                            # Iterar sobre las columnas de la tabla
        similarity = DataStructs.FingerprintSimilarity(fps[i], fps[j])                # Calcular la similitud de huellas moleculares entre fps[i] y fps[j]
        hmap[i, j] = similarity                                                       # Almacenar la similitud en la matriz hmap
        table.loc[tabla_piperidine['ID'][i], tabla_piperidine['ID'][j]] = similarity  # Agregar la similitud al DataFrame 'table' con los índices correspondientes

linked = linkage(hmap, 'complete')                                              # Clusterización (agrupación de moleculas) utilizando el método "complete" (algoritmos de clusterización) de la matriz de similitud 'hmap'
                                                                                ### Complete: la distancia entre dos clústeres es la distancia máxima entre los miembros de los dos clústeres

print(is_valid_linkage(linked))                                                 # Verifica la validez de la matriz, es "True"
labelList = [tabla_piperidine['ID'][i] for i in range(len(tabla_piperidine))]   # Crear una lista de etiquetas 'labelList' para las moléculas en la tabla

# El resultado final es una estructura jerárquica de clusteres que puede visualizarse como un dendrograma.

# Definir la función para generar el grafico
def plot_dendrogram(model, **kwargs):            # Crea una matriz de clustering y luego traza el dendrograma
    counts = np.zeros(model.children_.shape[0])  # Crea los conteos de muestras bajo cada nodo
    n_samples = len(model.labels_)
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1               # Nodo hoja
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count
    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)
    dendrogram(linkage_matrix, **kwargs)         # Trama el dendrograma correspondiente

# Generar el dendrograma
Clustering_fps = dendrogram(linked, orientation='left', labels=labelList, distance_sort='descending', show_leaf_counts=True,  above_threshold_color='y')

# Es recomendable generar un grafico que muestre la similitud entre moléculas y como se clusterizan.

# Esto nos dará los clústeres en orden según el último dendrograma
new_data = list(reversed(Clustering_fps['ivl']))

# Creamos una nueva tabla con el orden del agrupamiento jerárquico (HCL)
hmap_2 = np.empty(shape=(size, size))
for index, i in enumerate(new_data):
    for jndex, j in enumerate(new_data):
        hmap_2[index, jndex] = table.loc[i].at[j]

# Crear una figura con tamaño de 30x30 pulgadas
figure = plt.figure(figsize=(30,30))

# Crear una rejilla de subtramas con 2 filas y 7 columnas
gs1 = gridspec.GridSpec(2, 7)
gs1.update(wspace=0.01)

# Subtrama para el dendrograma
ax1 = plt.subplot(gs1[0:-1, :2])
dendrogram(linked, orientation='left', distance_sort='descending', show_leaf_counts=True, no_labels=True)
ax1.spines['left'].set_visible(False)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Subtrama para la matriz de similitud
ax2 = plt.subplot(gs1[0:-1, 2:6])
f = ax2.imshow(hmap_2, cmap='plasma', interpolation='nearest')
ax2.set_title('Fingerprint Similarity', fontsize=20, weight='bold')
ax2.set_xticks(range(len(new_data)))
ax2.set_yticks(range(len(new_data)))
ax2.set_xticklabels(new_data, rotation=90, size=8)
ax2.set_yticklabels(new_data, size=8)

# Subtrama para la barra de color
ax3 = plt.subplot(gs1[0:-1, 6:7])
m = plt.colorbar(f, cax=ax3, shrink=0.75, orientation='vertical', spacing='uniform', pad=0.01)
m.set_label('Fingerprint Similarity')

# Configurar los parámetros de las etiquetas de los ejes
plt.tick_params('both', width=2)

# Mostrar el gráfico
plt.plot()

# Guardamos la figura en un archivo
plt.savefig('fps_clustering.png')

n = 3                                                         # Indicar la cantidad de clusters
clusters = cut_tree(linked, n)                                # Obtener los clusters utilizando cut_tree con un número específico de clusters
tabla_piperidine['Cluster_fingerprints'] = clusters.flatten() # Agregar el número de cluster a la tabla

#Cluster 2: Agrupa las moleculas con mayor similitud, identificadas con los siguientes ID: 9, 10, 11, 14, 33, 40, 46, 47, 60, 61, 62, 72, 73, 76, 84, 109
numero_compuesto_1 = 84
numero_compuesto_2 = 60

# Calcular la similitud de huellas moleculares entre los dos compuestos
similarity = DataStructs.FingerprintSimilarity(fps[numero_compuesto_1], fps[numero_compuesto_2])
print(similarity)

# Mostrar las moléculas en una cuadrícula con sus leyendas
Draw.MolsToGridImage([tabla_piperidine['ROMol'][numero_compuesto_1], tabla_piperidine['ROMol'][numero_compuesto_2]], legends=[str(numero_compuesto_1), str(numero_compuesto_2)])

"""# Elegir el mejor criterio de drogabilidad para seleccionar los candidatos para tratar la patología.

**Criterios elegidos:**
- Lipinski: reglas para predecir que tan adecuado podría ser un compuesto químico para ser administrado oralmente a un paciente.
- Veber: reglas para evaluar la biodisponibilidad oral
- BBB: capacidad de un compuesto para atravesar la BBB es crucial en el diseño de fármacos para el tratamiento de enfermedades del sistema nervioso central.
- PAINS (Pan Assay Interference Structure): compuestos de interferencia pan-ensayo que se hacen pasar por posibles candidatos a fármacos
- Brenk: filtro de alertas estructurales encuentra fragmentos "supuestamente tóxicos, químicamente reactivos, metabólicamente inestables o con propiedades que generan una mala farmacocinética"
"""

# Obtención de las propiedades fisicoquimicas

# Crear listas vacías para almacenar los descriptores
TPSA_list = []
logP_list = []
MW_list = []
HDonor_list = []
HAceptor_list = []
Rotativos_list = []

# Calcular los descriptores para cada molécula en la columna 'ROMol' de la tabla "tabla_piperidine"
for i in range(len(tabla_piperidine)):
    TPSA_value = Descriptors.TPSA(tabla_piperidine['ROMol'][i], includeSandP=True)
    TPSA_list.append(TPSA_value)
    logP_value = Descriptors.MolLogP(tabla_piperidine['ROMol'][i])
    logP_list.append(logP_value)
    MW_value = Descriptors.ExactMolWt(tabla_piperidine['ROMol'][i])
    MW_list.append(MW_value)
    HDonor_value = Descriptors.NumHDonors(tabla_piperidine['ROMol'][i])
    HDonor_list.append(HDonor_value)
    HAceptor_value = Descriptors.NumHAcceptors(tabla_piperidine['ROMol'][i])
    HAceptor_list.append(HAceptor_value)
    Rotativos_value = Descriptors.NumRotatableBonds(tabla_piperidine['ROMol'][i])
    Rotativos_list.append(Rotativos_value)

# Agregar las listas de descriptores a la tabla
tabla_piperidine['TPSA'] = TPSA_list
tabla_piperidine['logP'] = logP_list
tabla_piperidine['MW'] = MW_list
tabla_piperidine['HDonor'] = HDonor_list
tabla_piperidine['HAceptor'] = HAceptor_list
tabla_piperidine['Rotativos'] = Rotativos_list

# Agregar una nueva columna para cada criterio a evaluar y asignarle un valor inicial de 0
tabla_piperidine['lipinski'] = 0
tabla_piperidine['Veber'] = 0
tabla_piperidine['BBB'] = 0

# Recorrer el DataFrame utilizando un bucle for y el índice i y comprobar las condiciones a cumplir para criterio y actualizar las filas de las columna correspondiente.

for i in range(len(tabla_piperidine)):
    if tabla_piperidine['MW'][i] <= 500 and tabla_piperidine['logP'][i] <= 5 and tabla_piperidine['HDonor'][i] <= 5 and tabla_piperidine['HAceptor'][i] <= 10:
        tabla_piperidine['lipinski'][i] = True
    else:
      tabla_piperidine['lipinski'][i] = False

for i in range(len(tabla_piperidine)):
    if tabla_piperidine['TPSA'][i] <= 140 and tabla_piperidine['Rotativos'][i] <= 10:
        tabla_piperidine['Veber'][i] = True
    else:
      tabla_piperidine['Veber'][i] = False

for i in range(len(tabla_piperidine)):
    if tabla_piperidine['TPSA'][i] < 100 and tabla_piperidine['TPSA'][i] > 0 and tabla_piperidine['logP'][i] < 6 and tabla_piperidine['logP'][i] > 0 :
        tabla_piperidine['BBB'][i] = True
    else:
      tabla_piperidine['BBB'][i] = False

# Creamos una instancia del objeto ADME y pasamos las moléculas como argumento
mol = [ADME(mol) for mol in tabla_piperidine['smiles']]
tabla_piperidine['ADME'] = mol
# Determina si la molécula tiene PAINS y BRENK
pains = [mol.pains() for mol in tabla_piperidine['ADME']]
brenk = [mol.brenk() for mol in tabla_piperidine['ADME']]
# Agregar las listas a la tabla
tabla_piperidine['PAINS'] = pains
tabla_piperidine['BRENK'] = brenk

tabla_piperidine.head(2)
tabla_piperidine.to_csv("Tabla_completa.csv")

"""# Seleccionar el/los mejores candidatos a droga de cada cluster según el criterio del punto 4."""

# Separar los datos por clusters
Cluster_0 = tabla_piperidine.loc[tabla_piperidine['Cluster_fingerprints'] == 0]
Cluster_1 = tabla_piperidine.loc[tabla_piperidine['Cluster_fingerprints'] == 1]
Cluster_2 = tabla_piperidine.loc[tabla_piperidine['Cluster_fingerprints'] == 2]

# Selección de las moleculas segun los criterios de drogabilidad y en cada cluster
Seleccion_0 = Cluster_0[(Cluster_0["lipinski"] == True)
                         & (Cluster_0["Veber"] == True)
                         & (Cluster_0["BBB"] == True)
                         & (Cluster_0["PAINS"] == False)
                         & (Cluster_0["BRENK"] == False)]

Seleccion_1 = Cluster_1[(Cluster_1["lipinski"] == True)
                         & (Cluster_1["Veber"] == True)
                         & (Cluster_1["BBB"] == True)
                         & (Cluster_1["PAINS"] == False)
                         & (Cluster_1["BRENK"] == False)]

Seleccion_2 = Cluster_2[(Cluster_2["lipinski"] == True)
                         & (Cluster_2["Veber"] == True)
                         & (Cluster_2["BBB"] == True)
                         & (Cluster_2["PAINS"] == False)
                         & (Cluster_2["BRENK"] == False)]

# Visualización de las propiedades fisicoquimícas de las moléculas elegidas
fig,axs = plt.subplots(1,6, figsize = (10,5), sharey=True)

sns.histplot(Seleccion_0['MW'], ax=axs[0])
sns.histplot(Seleccion_0['HDonor'], ax=axs[1])
sns.histplot(Seleccion_0['HAceptor'], ax=axs[2])
sns.histplot(Seleccion_0['logP'], ax=axs[3])
sns.histplot(Seleccion_0['TPSA'], ax=axs[4])
sns.histplot(Seleccion_0['Rotativos'], ax=axs[5])

fig.suptitle("compuestos seleccionados Cluster 0")
fig.tight_layout()

plt.ylim(0, 20)
plt.savefig('sns_0_histogramas.png')

fig,axs = plt.subplots(1,6, figsize = (10,5), sharey=True)

sns.histplot(Seleccion_1['MW'], ax=axs[0])
sns.histplot(Seleccion_1['HDonor'], ax=axs[1])
sns.histplot(Seleccion_1['HAceptor'], ax=axs[2])
sns.histplot(Seleccion_1['logP'], ax=axs[3])
sns.histplot(Seleccion_1['TPSA'], ax=axs[4])
sns.histplot(Seleccion_1['Rotativos'], ax=axs[5])

fig.suptitle("compuestos seleccionados Cluster 1")
fig.tight_layout()

plt.ylim(0, 20)
plt.savefig('sns_1_histogramas.png')

fig,axs = plt.subplots(1,6, figsize = (10,5), sharey=True)

sns.histplot(Seleccion_2['MW'], ax=axs[0])
sns.histplot(Seleccion_2['HDonor'], ax=axs[1])
sns.histplot(Seleccion_2['HAceptor'], ax=axs[2])
sns.histplot(Seleccion_2['logP'], ax=axs[3])
sns.histplot(Seleccion_2['TPSA'], ax=axs[4])
sns.histplot(Seleccion_2['Rotativos'], ax=axs[5])

fig.suptitle("compuestos seleccionados Cluster 2")
fig.tight_layout()

plt.ylim(0, 20)
plt.savefig('sns_2_histogramas.png')

Seleccion_0_index = Seleccion_0.reset_index()
Chem.Draw.MolsToGridImage(Seleccion_0_index['ROMol'], legends = [(str(Seleccion_0_index['index'][i])) for i in range(len(Seleccion_0_index))])

Seleccion_1_index = Seleccion_1.reset_index()
Chem.Draw.MolsToGridImage(Seleccion_1_index['ROMol'], legends = [(str(Seleccion_1_index['index'][i])) for i in range(len(Seleccion_1_index))])

Seleccion_2_index = Seleccion_2.reset_index()
Chem.Draw.MolsToGridImage(Seleccion_2_index['ROMol'], legends = [(str(Seleccion_2_index['index'][i])) for i in range(len(Seleccion_2_index))])

print(len(Seleccion_0), len(Seleccion_1), len(Seleccion_2))
# 30 16 6

# Guarda la información en df
Candidatos_0 = pd.DataFrame(Seleccion_0['chEMBL_ID'])
Candidatos_1 = pd.DataFrame(Seleccion_1['chEMBL_ID'])
Candidatos_2 = pd.DataFrame(Seleccion_2['chEMBL_ID'])

Candidatos_0.to_csv("Candidatos_0.csv")
Candidatos_1.to_csv("Candidatos_1.csv")
Candidatos_2.to_csv("Candidatos_2.csv")

"""# REPORTE

## INTRODUCCIÓN

La esquizofrenia es una enfermedad psiquiátrica caracterizada por un conjunto de síntomas que incluyen el delirio y las alucinaciones, conocidos como los síntomas clásicos de la psicosis o síntomas positivos:
 * Desorganización del pensamiento,
 * Síntomas deficitarios de función cerebral como la reducción de las emociones, el lenguaje y la motivación,
 * Disminución en la función cognitiva.

> Se cree que la esquizofrenia es una interacción compleja entre factores predisponentes genéticos y ambientales que afectan la función cerebral al perturbar la cognición, el procesamiento y la interpretación de estímulos y experiencias.
> > Tratamiento:
Se utilizan antipsicóticos de primera (típicos)  y/o segunda generación(atípicos). Estos actúan principalmente sobre los síntomas positivos.
> > > Estos medicamentos funcionan al afectar los neurotransmisores en el cerebro, como la dopamina y la serotonina, para aliviar los síntomas de la esquizofrenia, como alucinaciones, delirios, pensamiento desorganizado.
> > > > En particular, en el campo de los antipsicóticos, algunos compuestos que contienen el **grupo piperidina** han demostrado actividad antipsicótica y han sido utilizados en la práctica clínica.

## OBJETIVO:

Proponer una lista de moléculas que posean el grupo piperidina para ser presentados como candidatos a drogas con actividad antipsicótica para ser aplicadas como tratamiento en pacientes con Equizofrenia.

## METODOLOGÍA:

Se llevó a cabo un análisis quimioinformático que constó de los siguientes pasos:

1-  Recolección de datos de ChEMBL de las moléculas que tienen Piperidina como subestructura y están una fase máxima de ensayos clínicos de 4.

> Se utilizó la libreria **chembl_webresource_client** con la función **new_client** que nos permitió entrar a la base de datos.

2- Explorar la diversidad estructural a travez de clusterización por fingerprints.

> Se generaron los fingerprint de cada molécula utilizando la función **FingerprintMol** y luego e compararon entre ellas y se midió su similitud con la función **FingerprintSimilarity**. Ambas funciones de la libreria RDKit.
>> Agrupamos las moléculas tienen mayor similitud usando un algoritmo de clusterización. Para esto utilizamos la función **linkage** de la libreria **scipy**.
>>>Como método para calcular distancias elegimos **Complete** donde la distancia entre dos clústeres es la distancia máxima entre los miembros de los dos clústeres

Se genera un grafico que muestra la similitud y como se clusterizan las moléculas.

3- Selección de las moleculas por clusters y criterios de drogabilidad

> Se realizaron los cálculo de propiedades fisicoquímicas de cada molécula utilizando función **Descriptors** de **RDKit**.
- MW: peso molecular exacto de la molécula
- logP: coeficiente de partición octanol-agua de la molécula
- HDonor: número de donodores de enlaces de hidrógeno en la molécula
- HAceptor: número de aceptores de enlaces de hidrógeno en la molécula
- Rotativos: número de enlaces rotativos en la molécula
- TPSA: área superficial topológica mapeada de la molécula

Estos cálculos fueron utilizados para evaluar si las moléculas cumplian con los
**Criterios elegidos:**
- Lipinski: reglas para predecir que tan adecuado podría ser un compuesto químico para ser administrado oralmente a un paciente.
- Veber: reglas para evaluar la biodisponibilidad oral
- BBB: capacidad de un compuesto para atravesar la  barrera hematoencefalica es crucial en el diseño de fármacos para el tratamiento de enfermedades del sistema nervioso central.

Para mejorar nuestra selección decimos utilizar **ADME** y obtener los **pains** y **brenk** de las moléculas.

- PAINS (Pan Assay Interference Structure): compuestos de interferencia pan-ensayo que se hacen pasar por posibles candidatos a fármacos
- Brenk: filtro de alertas estructurales encuentra fragmentos "supuestamente tóxicos, químicamente reactivos, metabólicamente inestables o con propiedades que generan una mala farmacocinética"

Se generan las tablas correspondientes.


## RESULTADOS:

* Se obtuvieron 112 compuestos que poseen como subestructura al grupo piperidina.
* La clusterización resulto en 3 clusters compuestos por 60, 36 y 16 compuestos respectivamente.
* El filtro por los criterios de drogabilidad redujo a 30 moléculas en el cluster 0, 16 para el cluster 1 y 6 para el cluster 2.
* El cluster 2 agrupa los compuestos con mayor similitud y ademas tienen los valores mas bajos de TPSA y LogP. Se adjuntan graficos para una mejor visualización (PropFQ_0.png, PropFQ_1.png, PropFQ_2.png)

Conclusión:

Se proponen seis compuestos que son los agrupados en el cluster 2.
Estas moléculas tienen valores bajos de TPSA y LogP en comparación con los otros compuestos que cumplen con los criterios de drogabilidad. Estas propiedades hacen que aumente la probabilidad de absorción y distribución de un compuesto en el organismo, siendo capaces de atravezar facilmente la barrera hematoencefalica.

Lista de candidatos que se proponen:

CHEMBL19019
https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL19019/

CHEMBL656
https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL656/

CHEMBL33986
https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL33986/

CHEMBL895
https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL895/

CHEMBL963
https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL963/

CHEMBL71752
https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL71752/
"""

piperdine_sub = "C1CCNCC1"
substructure = Chem.MolFromSmiles(piperdine_sub)

# Creación de moléculas a partir de representaciones SMILES para los compuestos
CHEMBL19019 = Chem.MolFromSmiles('O=C1CC[C@@]2(O)[C@H]3Cc4ccc(O)c5c4[C@@]2(CCN3CC2CC2)[C@H]1O5')
CHEMBL656 = Chem.MolFromSmiles('COc1ccc2c3c1O[C@H]1C(=O)CC[C@@]4(O)[C@@H](C2)N(C)CC[C@]314')
CHEMBL33986 = Chem.MolFromSmiles('Oc1ccc2c(c1)[C@@]13CCCC[C@@]1(O)[C@@H](C2)N(CC1CCC1)CC3')
CHEMBL895 = Chem.MolFromSmiles('Oc1ccc2c3c1O[C@H]1[C@@H](O)CC[C@@]4(O)[C@@H](C2)N(CC2CCC2)CC[C@]314')
CHEMBL963 = Chem.MolFromSmiles('CN1CC[C@]23c4c5ccc(O)c4O[C@H]2C(=O)CC[C@@]3(O)[C@H]1C5')
CHEMBL71752 = Chem.MolFromSmiles('CCOC(=O)C1=C[C@]2(CC)CCCN3CCc4c(n1c1ccccc41)[C@@H]32')

# Creación de una lista de moléculas a partir de las representaciones SMILES
lista_moleculas = [CHEMBL19019,
                CHEMBL656,
                CHEMBL33986,
                CHEMBL895,
                CHEMBL963,
                CHEMBL71752
               ]

# Creación de una lista de átomos resaltados para cada molécula en `lista_moleculas` que coinciden con la estructura del benceno (`benceno`).
lista_atomos_resaltados = [mol.GetSubstructMatch(substructure) for mol in lista_moleculas]

# Generación de una imagen en forma de cuadrícula que muestra las estructuras de las moléculas en `lista_moleculas`,
# con los átomos resaltados según la lista `lista_atomos_resaltados`.
Draw.MolsToGridImage(lista_moleculas,
                     highlightAtomLists = lista_atomos_resaltados,
                    )