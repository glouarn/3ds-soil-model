#############
# GL - test sol 1D, ls_roots et ls_epsi constants
# choix : ongletIn = 'Lusignan30_1' # pour sol avec 1 unique voxel/compartiment
# choix : ongletIn = 'Lusignan30' # pour sol avec 30 voxels verticaux
#############

import os
import soil3ds
from soil3ds import soil_moduleN as solN
from scipy import *

from legume import initialisation # require legume package for 'init_sol_fromLpy' function
from legume import IOxls
#from soil3ds import IOxls

path_ = os.path.dirname(os.path.abspath(soil3ds.__file__))  # path ou trouver les inputs
path_leg = os.path.join(path_, 'test', 'inputs')


def critN(MS, a=4.8, b=-0.33):
    """ courbe critique de dilution de l'N """
    return min(6.5, a * MS ** b)  # en %


## 1) lecture fichier initialisation
meteo_path = os.path.join(path_leg, 'meteo_exemple.xls')  # 'meteo_exemple_debugL_gl.xls')#r'H:\devel\grassland\grassland\L-gume\meteo_exemple2.xls'
ongletM = 'Lusignan30'  # 'Lusignan302ans'#'DivLeg15'#'morpholeg15'#'combileg15'#'combileg16'#'Avignon30'#'exemple'#'morpholeg15'#'testJLD'#'competiluz'#
meteo = IOxls.read_met_file(meteo_path, ongletM)

## lecture fichier management
mn_path = os.path.join(path_leg, 'management_exemple.xls')  # 'management_exemple3_debugL_gl.xls')#r'H:\devel\grassland\grassland\L-gume\management_exemple.xls'
ongletMn = 'Lusignan30IrrN2'  # 'Lusignan30IrrN2ans'#'DivLeg15'#'Lusignan30IrrN'#'illimite-sanscoupe'#'combileg15-irrigajusteeLUZTVMIN'#'combileg16-irrigajusteeMIN'#'Lusignan30'#'Avignon30IrrN'#'Avignon30'#
mng = IOxls.read_met_file(mn_path, ongletMn)

inis_path = os.path.join(path_leg, 'Init_sol_exemple.xls')  # 'Initialisation_sol_exemple.xls')
ongletIn = 'Lusignan30'#'Lusignan30_1'  #
inis = IOxls.read_plant_param(inis_path, ongletIn)

# lecture des parametres du sol
path_sol = os.path.join(path_leg, 'Parametres_sol_exemple.xls')  # 'Parametres_sol_exemple2_debugL_glbis.xls')#
ongletS = 'lusignan99'  # 'morpholeg'#'combileg2015vshallow'#'combileg16vshallow'#'ASCHYD11'#
par_SN, par_sol = IOxls.read_sol_param(path_sol, ongletS)

# Param Plante
plant_path = os.path.join(path_leg, 'Parametres_plante_exemple.xls')  # 'Initialisation_sol_exemple.xls')
ongletP = 'Orca'  #
ParamP = IOxls.read_plant_param(plant_path, ongletP)

# 2) definition du pattern et discretisation sol
cote = 100.
pattern8 = [[0, 0], [cote, cote]]
Lsol = max((pattern8[1][0] - pattern8[0][0]) / 100., (pattern8[1][1] - pattern8[0][1]) / 100.)  # m
largsol = min((pattern8[1][0] - pattern8[0][0]) / 100., (pattern8[1][1] - pattern8[0][1]) / 100.)  # m
surfsolref = Lsol * largsol  # m2
dz_sol = inis['dz_sol']  # 4.#5. #cm
ncouches_sol = int(inis['ncouches_sol'])  # 4#10#30
prof_sol_max = ncouches_sol * dz_sol  # 80.

discret_solXY = list(map(int, inis['discret_solXY']))  # [10,10]# nb de discretisation du sol en X et en Y
# lims_sol = rtd.lims_soil(pattern8, dxyz=[[Lsol / discret_solXY[0]] * discret_solXY[0],
#                                         [largsol / discret_solXY[1]] * discret_solXY[1],
#                                         [dz_sol / 100.] * ncouches_sol])

opt_residu = 0

# debut, fin de simulation
DOY_deb, DOY_fin = 100, 300  # 239,623

# initialisation sol
meteo_j = IOxls.extract_dataframe(meteo, ['TmoyDay', 'I0', 'Et0', 'Precip', 'Tsol'], 'DOY', val=DOY_deb)
S, Tsol = initialisation.init_sol_fromLpy(inis, meteo_j, par_sol, par_SN, discret_solXY, dz_sol, pattern8, opt_residu, obstarac=None)


# simulation d'un sol 1D
##vegetation avec racine, LAI et MSaerien constants
R1 = S.m_1 * 200.  # vert_roots(S.dxyz, [0.000000001,0.,0.,0.]) #pas zero sinon buf FTSW
# R1[0,:,:] = R1[0,:,:]+0.000000001 #ajoute epsilon ds 1er horizon
ls_roots = [R1]
ls_epsi = [0.2]

# initialise teneur en N des plantes
Npc = 2.  # %
MSa = 1.5  # T.ha-1
QN = MSa * Npc / 100. * 1000  # kg N.ha-1 #%N libre

# initialisation de variables de sorties
cumEV, cumET0, cumPP, cumD, profH20, cumTransp, vlix, azomes = [], [], [], [], [], [], [], []

##boucle journaliere couplage sol-plante
for DOY in range(DOY_deb, DOY_fin):

    # MAJ meteo / mng
    # meteo_j = IOxls.extract_dataframe(meteo, ['TmoyDay','I0','Et0','Precip','Irrig','Coupe','FertNO3','FertNH4','Tsol'], 'DOY', val=DOY)
    meteo_j = IOxls.extract_dataframe(meteo, ['TmoyDay', 'I0', 'Et0', 'Precip', 'Tsol'], 'DOY', val=DOY)
    mng_j = IOxls.extract_dataframe(mng, ['Coupe', 'Irrig', 'FertNO3', 'FertNH4', 'Hcut'], 'DOY', val=DOY)
    print(DOY)
    for k in list(meteo_j.keys()): meteo_j[k] = meteo_j[k][0]
    for k in list(mng_j.keys()): mng_j[k] = mng_j[k][0]

    # entrees eau
    # Precip = meteo_j['Precip']+meteo_j['Irrig']
    Rain = meteo_j['Precip']
    Irrig = mng_j['Irrig']

    # entrees N
    # map_N = 0.*S.m_1[0,:,:]
    mapN_Rain = 1. * S.m_1[0, :, :] * Rain * par_SN['concrr']  # Nmin de la pluie
    mapN_Irrig = 1. * S.m_1[0, :, :] * Irrig * par_SN['concrr']  # Nmin de l'eau d'irrigation
    mapN_fertNO3 = 1. * S.m_1[0, :, :] * mng_j['FertNO3'] * S.m_vox_surf[0, :, :] / 10000.  # kg N par voxel
    mapN_fertNH4 = 1. * S.m_1[0, :, :] * mng_j['FertNH4'] * S.m_vox_surf[0, :, :] / 10000.  # kg N par voxel

    # entre Tsol (lecture)
    S.updateTsol(meteo_j['Tsol'])  # (meteo_j['TmoyDay']) #Tsol forcee comme dans STICS

    # demande N plante pour 1 couvert

    PotN = MSa * critN(MSa) / 100. * 1000  # kg N.ha-1
    demande_N_plt = max(PotN - QN, 0.)  # kg N.ha-1
    ls_demandeN = [sum(demande_N_plt) / 10000.]  # kg N.surface de sol

    # Calcul du bilan hydrique
    ls_transp, evapo_tot, Drainage, stateEV, m_frac_transpi, m_frac_evap, ls_ftsw = S.stepWBmc(
        meteo_j['Et0'] * surfsolref, ls_roots, ls_epsi, Rain * surfsolref, Irrig * surfsolref, S.stateEV,
        ZESX=par_SN['ZESX'], leafAlbedo=0.15, U=S.Uval, b=S.b_, FTSWThreshold=0.4, treshEffRoots=0.5, opt=1)

    # Calcul du bilan N

    # Mineralisation / Nitif /Inflitration N
    S.stepNB(par_SN)
    S.stepNitrif(par_SN)
    S.stepNINFILT(mapN_Rain, mapN_Irrig, mapN_fertNO3, mapN_fertNH4, Drainage, opt_infil=1)

    # uptake plante
    ActUpNtot, ls_Act_Nuptake_plt, ls_DQ_N, idmin = S.stepNuptakePlt(par_SN, [ParamP], ls_roots, m_frac_transpi,
                                                                     ls_demandeN)

    # update QN et Npc
    QN += sum(ActUpNtot) * 10000  # kg N.ha-1
    Npc = QN / (MSa * 10)

    # sorties
    print(DOY, 'tsw_t: ', S.tsw_t[0, 0, 0], 'evapotot: ', evapo_tot)  # sum3(S.tsw_t)
    print('Npc', Npc)
    # print('QN', QN)
    HAx = S.HRp()
    cumEV.append(evapo_tot)
    cumTransp.append(sum(ls_transp))
    cumET0.append(meteo_j['Et0'] * surfsolref)
    cumPP.append(meteo_j['Precip'] * surfsolref)
    cumD.append(Drainage[-1][0][0])
    profH20.append([DOY] + HAx[:, 0, 0].tolist() + [evapo_tot, Drainage[-1][0][0]])

    vlix.append(S.lixiNO3 * 10000)
    azomes.append(S.m_NH4.sum() + S.m_NO3.sum() * 10000)

##termes du bilan hydrique global
S.CloseWbalance()  # -> equilibre
S.CloseCbalance()  # -> equilibre
S.CloseNbalance()  # -> equilibre










