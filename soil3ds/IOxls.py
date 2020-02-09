import xlrd
#from rpy_options import set_options
#set_options(RHOME='c:/progra~1/R/R-2.12.1')
#from rpy import r

def get_xls_col(sheet):
    """ recupere dans une feuille excel donnees par colone  """
    res=[]
    for i in range(sheet.ncols):
        res.append(sheet.col(i))

    # retient seulement les valeurs du dictionnaire
    for i in range(len(res)):
        for j in range(len(res[0])):
            res[i][j]=res[i][j].value

    return res

def get_xls_row(sheet):
    """ recupere dans une feuille excel donnees par colone  """
    res=[]
    for i in range(sheet.nrows):
        res.append(sheet.row(i))

    # retient seulement les valeurs du dictionnaire
    for i in range(len(res)):
        for j in range(len(res[0])):
            res[i][j]=res[i][j].value

    return res



def t_list(tab):
    """transpose tab"""
    res = []
    for j in range(len(tab[0])):
        v = []
        for i in range(len(tab)):
            v.append(tab[i][j])
        
        res.append(v)

    return res

#def as_matrix(tab):
#    """ converts a list of list or a python array into an R matrix Robj """
#    r.rbind.local_mode(0)
#    r.c.local_mode(0)
#    x = r.c(tab[0])
#    for i in range (1,len(tab)):
#        x = r.rbind(x, r.c(tab[i]))
#
#    return x

def conv_dataframe(tab):
    """ converti liste de liste en dictionnaire; prend la cle comme le pemier element de la liste"""
    """ format a priori compatible pour conversion en data.frame R"""
    dat = {}
    for i in range(len(tab)):
        dat[str(tab[i][0])] = tab[i][1:]

    return dat #r.as_data_frame(dat)

def conv_list(tab):
    """ converti dictionnaireen liste de liste en ;  cle comme pemier element de la liste"""
    """ format compatible pour mes_csv"""
    dat = []
    for i in list(tab.keys()):
        v = [i]
        dat.append(v)

    count = 0
    for i in list(tab.keys()):
        for j in range(len(tab[i])):
            dat[count].append(tab[i][j])

        count = count+1

    return dat 

def extract_dataframe(dat, ls_cles, cle, val=None):
    """ extrait dans listes de cles ls_cles les lignes pour lesquelles cle=val; toutes si val=None """
    #cree liste d'index ou cle = val

    id = []
    for i in range(len(dat[cle])):
        if val == None:
            id.append(i)
        else:
            if dat[cle][i] == val:
                id.append(i)

    x = {}
    for k in ls_cles: # recupere les paires interessantes
        v = []
        for i in id: # les id respectant cle=val
            v.append(dat[k][i])

        x[k] = v

    return x
    #extract_dataframe(dat, cles, 'geno', geno)
    #extract_dataframe(dat, cles, 'geno')



def extract_list(dat, ls_id, ls_vals, L1=1):
    """ extrait avec un ET les lignes pour les quelles les colonnes numerotees ls_id prennent les valeurs ls_vals"""

    res = []
    for i in range(L1, len(dat)):
        bol = 1
        for j in range(len(ls_id)):
            if dat[i][ls_id[j]] == ls_vals[j]:
                bol = bol*1
            else :
                bol = bol*0

        if bol == 1:
            res.append(dat[i])

    return res


def read_plant_param(xls_path, onglet):
    """ lit l'onglet d'un fichier xls pour cree un dico de parametre plante (L-egume)- se base sur 3 colones 'name', 'nb_par' (0 si sclaire, n si vecteur), 'id_par'
    ; presuppose que valeurs a mettre dans un vecteur sont deja ordonnees"""
    book=xlrd.open_workbook(xls_path)
    shc = get_xls_col(book.sheet_by_name(onglet))
    dico_shc = conv_dataframe(shc)

    g = {}
    g['name']=onglet
    for i in range(len(dico_shc['name'])):
        if dico_shc['nb_par'][i] == 1: #si scalaire
            g[str(dico_shc['name'][i])]=dico_shc['value'][i]
        elif dico_shc['nb_par'][i] > 1 and dico_shc['id_par'][i] == 0:#si vecteur et sur la premier valeur
            paramlist=[]
            for j in range(int(dico_shc['nb_par'][i])):
                paramlist.append(dico_shc['value'][i+j])

            g[str(dico_shc['name'][i])]=paramlist   

    return g
    #path_source=r'H:\devel\grassland\grassland\L-gume\Parametres_plante.xls' 
    #onglet = 'geno_test'
    #g4 = read_plant_param(path_source, onglet)


def read_sol_param(xls_path, onglet):
    """ lecture du fichier sol dans par_SN et mise en forme du dictionnaire par_sol"""
    par_SN = read_plant_param(xls_path, onglet)
    par_sol = {}
    for i in range(len(par_SN['soil_number'])):
        id = str(int(par_SN['soil_number'][i]))
        par_sol[id] = {'soil number': id, 'teta_sat': par_SN['teta_sat'][i], 'teta_fc': par_SN['teta_fc'][i], 'teta_wp': par_SN['teta_wp'][i], 'teta_ad': par_SN['teta_ad'][i],'DA':par_SN['DA'][i]}

    return par_SN, par_sol
    #idealement a faire: enlever par_sol et lire dnas le module sol directement dans le par_SN


def read_met_file(meteo_path, ongletM):
    """ lecture de fichier meteo / Mng """
    #meteo_path = os.path.join(path_leg,'meteo_exemple2.xls')#r'H:\devel\grassland\grassland\L-gume\meteo_exemple2.xls'
    #ongletM = 'Avignon30'#'exemple'#'morpholeg15'#'testJLD'#'competiluz'#
    met = xlrd.open_workbook(meteo_path)
    meteo = conv_dataframe(get_xls_col(met.sheet_by_name(ongletM)))
    for k in ['month', 'day', 'DOY']: meteo[k] = list(map(int, meteo[k]))

    return meteo


def modif_param(gx, ongletP, ongletScenar, idscenar, idlist=1, mn_sc=None):
    """ met a jour ParamP d'un genotype gx pour les variables et valeurs indiques dans ongletScnar """
    """ fait rien si ongletScenar='default' ou iscenar<0 ou onglet correspond pas a celui a modifier; sinon va modifier selon fichier scenario"""
    if ongletP == ongletScenar and idscenar > 0 and mn_sc != None:  # si onglet correspond a ongletscenat a modifier
        usc = xlrd.open_workbook(mn_sc)
        ls_sc = conv_dataframe(get_xls_col(usc.sheet_by_name(ongletScenar)))
        nb_modif = len(list(ls_sc.keys())) - 1  # nb de param a modifier
        ls_sc['id_scenario'] = list(map(int, ls_sc['id_scenario']))

        if nb_modif > 0:  # s'il y a des parametre a modifier
            idok = ls_sc['id_scenario'].index(idscenar)
            keys_modif = list(ls_sc.keys())
            keys_modif.remove('id_scenario')
            for k in keys_modif:
                if str(ls_sc[k][idok]) != '' or str(ls_sc[k][idok]) != 'NA':  # y a un valeur specifiee
                    if type(gx[k]) == type(0.):  # gere uniquement les parametres avec 1 seule valeur float (pas liste)
                        gx[k] = ls_sc[k][idok]
                    elif type(gx[k]) == list:  # pour les liste, gere uniquement un id de la liste (1 par defaut)
                        gx[k][idlist] == ls_sc[k][idok]
    return gx



def dic2vec(nbplantes, dic):
    """ mise en liste 'nump'par plante un dico deja par plante """
    res3 = []
    for nump in range(nbplantes):
        try:
            key_ = str(nump)
            res3.append(dic[key_])
        except:
            res3.append(0.)

    return res3


# plus utilise ds l-egume
def dic_sum(ls_dict):
    "somme par cle les element de dico d'un meme format ; e.g [{0: 0, 1: 1, 2: 2}, {0: 3, 1: 4, 2: 5}] "
    # prepa d'un dico nul avec meme cles
    res = {}
    for k in list(ls_dict[0].keys()): res[k] = 0.
    # somme des dico
    for k in list(ls_dict[0].keys()):
        for i in range(len(ls_dict)):
            res[k] += ls_dict[i][k]

    return res


def append_dic(dic, key, element):
    """ add an element to a list in a dictionnary or create the list if the key is not present"""
    try:
        dic[key].append(element)
    except:
        dic[key] = [element]


def add_dic(dadd, dini):
    """ add the values of the k keys of a dictionary dadd to an existing dictionnary dini with the same keys - creates keys in dini if not already existing"""
    for k in list(dadd.keys()):
        try:
            dini[k] += dadd[k]
        except:
            dini[k] = dadd[k]
    return dini


def sum_ls_dic(dic):
    """ sum of the element by keys in a dictionnary of lists """
    for k in list(dic.keys()):
        dic[k] = sum(dic[k])

