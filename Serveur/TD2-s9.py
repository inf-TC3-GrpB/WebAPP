# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 12:01:14 2020

@author: gaubi
"""

import http.server
import socketserver
import datetime
import sqlite3
import re
import json




class RequestHandler(http.server.SimpleHTTPRequestHandler): # définition du nouveau handler, classe dérivée de http.server.SimpleHTTPRequestHandler

    static_dir = '/client' # sous-répertoire racine des documents statiques
    
    
    
    def do_GET(self): # on surcharge la méthode qui traite les requêtes GET    
        
        re_pays=re.match('.*/country/(\w+).*',self.path) #trouve le pays correspondant dans une URL /country/pays
        
        
        
        exceptions=[self.path[0:5]!='/time',self.path[0:10]!='/countries',re_pays==None,self.path[0:8]!='/service']  #définit tous les cas d'utilisation non habituels       
        
        if not False in exceptions : #si la requete correspond à un cas d'utilisation classique
            self.path = self.static_dir + self.path  # on modifie le chemin d'accès en insérant un répertoire préfixe 
            http.server.SimpleHTTPRequestHandler.do_GET(self) # on traite la requête via la classe parent
           
        
        else : #si la requete ne correspond pas à un cas d'utilisation classique 
            
            
            if self.path[0:5]=='/time':  #si le chemin se termine par '/time'
                self.temps() #affiche la page date/heure si la requete correspond
            
            elif self.path[0:8]=='/service':
                
                if self.path[0:18]=='/service/countries':
                    self.lister_pays()  #affiche une page contenant la liste des pays et leurs caractéristiques si l'URL correspond                
                    self.carac_pays_json()   #envoie les informations json
                
                elif re_pays!=None:  #si /country/France par ex est dans le path
                    pays=re_pays.group(1)  #récupère la string contenant le nom du pays dans l'URL
                    self.carac_pays_modif(pays)   #affiche une page contenant les caractéristiques d'un pays si l'URL correspond                   
                    self.carac_pays_json(pays)  #envoie les informations json  
            
            
            
            
            elif self.path[0:10]=='/countries':
                self.lister_pays()  #affiche une page contenant la liste des pays et leurs caractéristiques si l'URL correspond
                
            
            
            elif re_pays!=None:
                pays=re_pays.group(1)  #récupère la string contenant le nom du pays dans l'URL
                self.carac_pays_modif(pays)   #affiche une page contenant les caractéristiques d'un pays si l'URL correspond
                            
           
            
        
        
    
    
    
    

    def send(self,body,headers=[]):     
        
        encoded = bytes(body, 'UTF-8')  # on encode la chaine de caractères à envoyer, body est une string           
        self.send_response(200)   # on envoie la ligne de statut       
        [self.send_header(*t) for t in headers] # on envoie les lignes d'entête et la ligne vide
        self.send_header('Content-Length',int(len(encoded)))
        self.end_headers()        
        self.wfile.write(encoded) # on envoie le corps de la réponse
        
    
    
    
    
    def temps(self):  #affichage de la page date/heure si le path correspond 
        if self.path[0:5]=='/time':  #si le chemin se termine par '/time'
            affichage_date=datetime.datetime.today().ctime() #obtention de l'affichage de date/heure 
            
            response='<!DOCTYPE html><title>Continent Asiatique</title>' + \
"<meta charset='utf-8'><p>Voici l'heure du serveur : {} GMT </p>"\
.format(affichage_date)
            headers=[('Content-Type','text/html;charset=utf-8')]
            self.send(response,headers) 
            
    
    
    
    
    def get_info_pays_db(self,country=None):
        conn=sqlite3.connect('pays.sqlite')  #connexion à la base de données      
        c=conn.cursor()
              
              
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")  #requête permettant d'avoir la liste des tables
        a=c.fetchall()  #stocke les résultats de la requête sous une forme alambiquée
        liste_tables=[a[i][0] for i in range(len(a))]  #stocke la liste des tables de la database (strings)
        
        if 'countries' in liste_tables : #vérifie que la table countries existe         
            c.execute("PRAGMA table_info(countries)")#requête permettant d'avoir la liste des colonnes de la table countries
            a=c.fetchall()   #stocke les résultats de la requête sous une forme alambiquée
            liste_colonnes=[a[i][1] for i in range(len(a))]  #stocke la liste des colonnes de la table countries (strings)
            
            if country!=None: #Si on veut un pays en particulier
                c.execute("SELECT * FROM countries WHERE wp="+"'"+country+"'")
                a=c.fetchall()
                
                if len(a)!=0:  #vérifie que le pays existe dans la base données
                    caracteristiques_pays={liste_colonnes[i]:a[0][i] for i in range(len(liste_colonnes))}   #crée le dictionnaire contenant pour chaque colonne de la db en clef, en élément les infos correspondantes du pays
                    return caracteristiques_pays
                
                else: #Si le pays n'existe pas
                    return None
            else: #si on veut les infos de tous les pays
                c.execute("SELECT * FROM countries") #obtient les infos de tous les pays
                a=c.fetchall()
                if len(a)==0: #s'il n'y a aucun pays dans la database
                    return None
                
                else: #s'il y a au moins un pays dans la database
                    
                    caracteristiques_pays={a[i][0]:{liste_colonnes[j]:a[i][j] for j in range(len(liste_colonnes))}for i in range(len(a))} #dictionnaire avec la clef primaire comme clefs, et comme éléments un dictionnaire de clefs la liste des colonnes et d'éléments pour un pays, ses infos            
                    return caracteristiques_pays     
        
    
    def affichage_infos_pays(self,caracteristiques_pays):        
        if  caracteristiques_pays!=None:
            affichage="{} : wp={} ;  Capital={} ; Latitude={} ; Longitude={} ; Continent={}".format(caracteristiques_pays['name'],caracteristiques_pays['wp'],caracteristiques_pays['capital'],caracteristiques_pays['latitude'],caracteristiques_pays['longitude'],caracteristiques_pays['continent'].capitalize())
            return affichage
    
    
    
    
    def lister_pays(self):  #affiche une page avec la liste des pays si le path correspond
       caracteristiques_pays=self.get_info_pays_db() #dictionnaire de tous les pays contenant en élément un dictionnaire contenant leurs infos            
            
       if caracteristiques_pays==None:  #si la DB ne comporte aucun pays
            self.send_error(404,'No country in database')
       
       else:  #si la DB comporte au moins un pays
            response='<!DOCTYPE html>' + \
"<head>"+\
'<title>Continent Asiatique</title>'+\
"<meta charset='utf-8'>"+\
'<link rel="stylesheet" href="/special.css" type="text/css"> '+\
'</head>'+\
"<body>"+\
'<div id="page">'+\
'<h1 id="special">Liste des pays : </h1>'+\
"<ul>"
            i=1  #compteur des pays
            for pays in caracteristiques_pays.keys():   #ajoute le i-ème pays à la ième ligne               
                response=response + \
'<li class="ok">'+"["+str(i)+"] - "+caracteristiques_pays[pays]['name']+'</li>'
                i+=1
                
            response=response+\
'</ul>'+\
'</div>'+\
'</body>'
            headers = [('Content-Type','text/html;charset=utf-8')]
            self.send(response,headers)
         
        
        
        

       
                
                
                
    def carac_pays(self,country=None):
        
        if country!=None:  #si on veut afficher les infos d'un seul pays
            caracteristiques_pays=self.get_info_pays_db(country)  #dictionnaire des infos du pays
            
            if caracteristiques_pays!=None: #si le pays existe bien dans la base de données            
                response='<!DOCTYPE html><title>Continent Asiatique</title>' + \
"<meta charset='utf-8'><p>Caractéristiques du pays :  </p>"                
                    
                for clef in caracteristiques_pays.keys():  #ajoute la caractéristique cllef à la ligne suivante de la réponse à afficher
                    response=response + \
"<p>{} : {}  </p>"\
.format(clef,caracteristiques_pays[clef])                      
                self.send(response)       
                    
                
            else:  #Si le pays n'existe pas dans la base données
                response='<!DOCTYPE html><title>Continent Asiatique</title>' + \
"<meta charset='utf-8'><p>Ce pays n'est pas présent sur ce continent</p>"
                headers = [('Content-Type','text/html;charset=utf-8')]
                self.send(response,headers)
        
        else: #si on veut afficher les infos de tous les pays
            caracteristiques_pays=self.get_info_pays_db() #dictionnaire de tous les pays contenant en élément un dictionnaire contenant leurs infos            
            
            if caracteristiques_pays!=None:  #si la DB comporte au moins un pays
                response='<!DOCTYPE html><title>Continent Asiatique</title>' + \
"<meta charset='utf-8'><p>Liste des pays et de leurs caractéristiques : </p>"+\
"<head>"+\
'<title>Continent Asiatique</title>'+\
"</head>"+\
"<body>"
                for pays in caracteristiques_pays.keys():                    
                    response=response + \
"<p> {} </p>"\
.format(self.affichage_infos_pays(caracteristiques_pays[pays]))
                
                response=response+\
"</body>"
                headers = [('Content-Type','text/plain;charset=utf-8')]
                self.send(response,headers)
                
            else:  #si la DB ne comporte aucun pays
                self.send_error(404,'No country in database')        
                
                
                    
            



                
                
    def carac_pays_modif(self,country=None):
        
        if country!=None:  #si on veut afficher les infos d'un seul pays
            caracteristiques_pays=self.get_info_pays_db(country)  #dictionnaire des infos du pays
            
            if caracteristiques_pays!=None: #si le pays existe bien dans la base de données            
                
                response='<!DOCTYPE html>' + \
"<head>"+\
'<title>Continent Asiatique</title>'+\
"<meta charset='utf-8'>"+\
'<link rel="stylesheet" href="/special.css" type="text/css"> '+\
'</head>'+\
'<body>'+\
'<div id="page">'+\
'<h1 id="special">{}</h1>'\
.format(caracteristiques_pays['name']) + \
'<ul>'+\
'<li class="ok">Continent : {}</li>'\
.format(caracteristiques_pays['continent'].capitalize())+\
'<li class="ok">Capital : {}</li>'\
.format(caracteristiques_pays['capital'].capitalize())+\
'<li class="ok">Latitude : {}</li>'\
.format(caracteristiques_pays['latitude'])+\
'<li class="ok">Longitude : {}</li>'\
.format(caracteristiques_pays['longitude'])+\
'</ul>'+\
'</div>'+\
'</body>'  #../.. après href permet de retourner à la racine, car sinon /country/France par ex amène ds le repertoire /country/France (qui n'existe pas)
                headers = [('Content-Type','text/html;charset=utf-8')]
                self.send(response,headers)
                       
                    
                
            else:  #Si le pays n'existe pas dans la base données
                self.send_error(404,'Country not found')
                
                
                

        
        
        
        
            
        
    
    
    
    
    
    def carac_pays_json(self,country=None):
    
        if country!=None:  #si on veut un pays en particulier
            
            dict_pays=self.get_info_pays_db(country)
            
            if dict_pays!=None:  #si le pays existe dans la database       
                json_data=json.dumps(dict_pays,indent=4)
                
                headers=[('Content-Type','application/json')]
                self.send(json_data,headers)  #envoi de la réponse
                
            else : #si le pays n'existe pas dans la database
                self.send_error(404,'Country not found')
        
        else: #si on veut les infos de tous les pays
            
            dict_pays=self.get_info_pays_db()
            
            if dict_pays!=None: #s'il y a des pays dans la database
                json_data=json.dumps(dict_pays,indent=4)
                headers=[('Content-Type','application/json')]
                self.send(json_data,headers)  #envoi de la réponse
            
            else: #s'il n'y a aucun pays dans la database 
                self.send_error(404,'No countries in database')
        
        




            
    

    
httpd = socketserver.TCPServer(("", 8080), RequestHandler)# instanciation et lancement du serveur
httpd.serve_forever()