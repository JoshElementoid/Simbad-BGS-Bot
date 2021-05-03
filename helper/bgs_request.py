# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 00:04:49 2021

@author: Josh
"""


import requests
import json


def flatten_pages (req_url, req_params):
    """
    Returns a flattened list of "docs" dictionary for Elite BGS's
    multi-page request responses
    """
    
    cur_page = 1
    next_page = True
    response_total = []    
    
    session = requests.Session()
    
    while next_page:
        headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
        
        req_params["page"] = cur_page
        response = session.get(url=req_url,
                                params=req_params,
                                headers=headers)
        response.raw.chunked = True
        response.encoding = "utf-8"
        
        content = json.loads(response.content)
        response_total.append(content["docs"]) 
        
        cur_page += 1
        next_page = content["hasNextPage"]

    flattened = [item for sublist in response_total for item in sublist]
    
    return flattened


def get_control_sys (name="Simbad Regime", fac_detail=True):
    
    """
    Returns a list of dicts containing information about every system
    controlled by Simbad.
    
    """
    
    bgs_endpt = "https://elitebgs.app/api/ebgs/v5/systems?"
    params = {"faction": name,
              "factionControl": "true",
              "factionDetails": str(fac_detail).lower()
        }
    
    ctrl_sys_docs = flatten_pages(bgs_endpt, params)


    return ctrl_sys_docs
    

def get_influence (name="Simbad Regime"):
    """
    Returns a list of [system, Simbad influence, last updated]
    for all of Simbad's controlled systems

    """

    bgs_endpt = "https://elitebgs.app/api/ebgs/v5/factions?"
    params = {"name": name,
        }    
    
    response = flatten_pages(bgs_endpt, params)

    return response[0]["faction_presence"]
