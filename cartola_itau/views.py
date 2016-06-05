#from django.http import Http404, HttpResponse
from django.shortcuts import render
import requests
import json as json
import pandas as pd




########### GLOBAL PROCEDURES ############################


### Log in na API
def globo_token():
    payload = {
        'payload': {
        'email': "ferbester@gmail.com",
        'password': "Qzwxecr44",
        'serviceId': 438
        }
    }
# Connects to API and saves code to globo_GLBID
    ENDPOINT_URL = 'https://login.globo.com/api/authentication'
    response = requests.post(ENDPOINT_URL, data=json.dumps(payload), headers={ 'content-type': 'application/json' })
    return { 'X-GLB-Token': response.cookies.get('GLBID')}


### checa se API de pontuados
### esta ativa e retorna bool
def checa_pontuados():
    url_parciais = requests.get('https://api.cartolafc.globo.com/atletas/pontuados')
    parciais = json.loads(url_parciais.text)
    
    if parciais.keys()[0] == 'mensagem':
        return 1
    else:
        return 0
        
### Retorna status do mercado
### em string
def info_mercado():
# Pegando informacoes do mercado 
    url_mercado = requests.get('https://api.cartolafc.globo.com/mercado/status')
    mercado = json.loads(url_mercado.text)
    mer_fechamento = mercado['fechamento']
    if mercado['status_mercado'] == 1:
        return 'STATUS MERCADO: Aberto (fecha dia {}/{}/{} as {}:{})'.format(mer_fechamento['dia'],mer_fechamento['mes'],
                                                          mer_fechamento['ano'],mer_fechamento['hora'],
                                                          mer_fechamento['minuto'])
    elif mercado['status_mercado'] == 3:
        return u'STATUS MERCADO: Em Atualizacao'
    elif mercado['status_mercado'] == 2:
        return 'STATUS MERCADO: Fechado'                                          

### busca parciais de jogadores 
### e returns dict
def jog_parciais():
        
    url_parciais = requests.get('https://api.cartolafc.globo.com/atletas/pontuados')
    parciais = json.loads(url_parciais.text)
    
    if checa_pontuados():
        return {}
    else:       
        dict_parciais = {}
        for atleta in parciais["atletas"].keys():
            dict_parciais[atleta] =  parciais["atletas"][atleta]["pontuacao"]
        return dict_parciais


def membros_liga():
    url_liga = requests.get('https://api.cartolafc.globo.com/auth/liga/cartola-fc-do-itau', headers=globo_token())
    liga = json.loads(url_liga.text)
    membros = liga["times"]

    if checa_pontuados():   
        point_list =  [dict(dict([("Nome",membro["nome_cartola"])] + list(membro["pontos"].items()) + [("time_id",membro["time_id"])] + [("parcial",0)]))
                        for membro in membros]       
        return pd.DataFrame(point_list)    
    else:  
#        dict_memparcial = {}
        point_list = []
        for membro in membros:
            
            url_memtimes = requests.get('https://api.cartolafc.globo.com/time/{}'.format(
                            membro["slug"]))
            mematletas = json.loads(url_memtimes.text)["atletas"]
            
            dict_parciais = jog_parciais()
            parcial = 0
            num_jog = 0
            for mem in mematletas:        
                if str(mem["atleta_id"]) in dict_parciais:
                    parcial = parcial + dict_parciais[str(mem["atleta_id"])]
                    num_jog = num_jog + 1
#                    dict_memparcial[membro["time_id"]] = parcial
            point_list.append(dict([("Nome",membro["nome_cartola"])] + list(membro["pontos"].items()) + [("time_id",membro["time_id"])] + [("parcial",parcial)]))
        return pd.DataFrame(point_list)



def parcial_sort(var, data):
    if var == 'parcial':
        data['.'] = data[var].rank(ascending=0)
        return data.sort('parcial', ascending=0)[['.','Nome', var]]
    else:
        data['parcial_'+var] = data[var] + data['parcial']
        data['.'] = data['parcial_'+var].rank(ascending=0)
        if checa_pontuados():    
            return data.sort('parcial_'+var, ascending=0)[['.','Nome' , var]]
        else:
            return data.sort('parcial_'+var, ascending=0)[['.','Nome', 'parcial_'+var , var]]        

############# REQUEST PROCEDURES #########################

def pagina_inicial(request):

    point_dict = membros_liga()

    html_mes = parcial_sort('mes',point_dict).rename(columns = {'mes':'Pontos', 'parcial_mes':'Pontos (Atualizado)'}).to_html(index=False)
    html_campeonato = parcial_sort('campeonato',point_dict).rename(columns = {'campeonato':'Pontos', 'parcial_campeonato':'Pontos (Atualizado)'}).to_html(index=False)
#    html = membros_liga().fillna(0).to_html(index=False)   
    mercado = info_mercado()

    if checa_pontuados():        
        return render(request, 'rankings.html', {'html_mes': html_mes, 'html_campeonato': html_campeonato, 'mercado' :mercado})    
    else:
        html_pontuados = parcial_sort('parcial',point_dict).rename(columns = {'Parcial':'Pontos'}).to_html(index=False)
        return render(request, 'rankings_pontuados.html', {'html_pontuados': html_pontuados,'html_mes': html_mes, 'html_campeonato': html_campeonato, 'mercado' :mercado})    
    
def regras(request):
    return render(request, 'regras.html', {'mercado' :info_mercado()})     





 