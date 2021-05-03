# -*- coding: utf-8 -*-
"""
Created on Sat May  1 23:54:54 2021

@author: Josh
"""


import os, time, math, json
import numpy as np

from datetime import datetime
from matplotlib import pyplot as plt
from helper import bgs_request

class bgs_info (object):
    
    def __init__(self, ctrl_path, inf_path, fac_name="Simbad Regime", update=False):
        
        """ 
        The bgs_info class needs 2 things to initialize:
            1) path to a json with controlled system information, and
            2) path to a json with the faction influence information.
        
        Both must be in Elite BGS's API response format.
        
        BGS information comes from the 2 json files.
        
        """
        
        self.ctrl_path = ctrl_path
        self.inf_path = inf_path
        self.fac_name = fac_name
    
        if update:
            self.update_info()
    
        with open(ctrl_path, "r") as f:
            self.ctrl_full = json.load(f)
            f.close()   
        
        with open(inf_path, "r") as f:
            self.fac_inf = json.load(f)
            f.close()
        
        # Sort by your influence:
        self.ctrl_full = sorted(self.ctrl_full, 
                                key=lambda x: -bgs_info.get_fac_inf(x, self.fac_name))
        
        return
    
    
    ##### UPDATE #####
    
    def update_info (self, msg="on"): 
        """
        Updates the 2 json files by sending another request to EliteBGS's API
        and rewriting the local json files.
        
        """
        
        if msg.lower() == "on":
            print("Updating, this will take a minute")
        
        self.ctrl_full = bgs_request.get_control_sys(name=self.fac_name)
        self.fac_inf = bgs_request.get_influence(name=self.fac_name)

        with open(self.ctrl_path, "w") as f:
            json.dump(self.ctrl_full, f)
            f.close()   
            
        with open(self.inf_path, "w") as f:
            json.dump(self.fac_inf, f)
            f.close()
        
        if msg.lower() == "on":
            print("Updating completed")

        return
    

    def last_updated (self):
        """
        Returns a string of how long ago the last update was
        
        """
        last_update = os.path.getmtime(self.ctrl_path)
        now = time.time()
        since_update = now - last_update
        
        formatted = "Last Updated: {:.0f} Hours {:.0f} Minutes ago".format(
            (since_update//3600),(since_update//60)%60 )
        
        
        return formatted
    
    
    ##### EXPANSION #####

    def expansion_info (self, min_inf=0.7, time="relative"):
        """
        Returns a list of [system_name, influence, "max" inf, last_updated]
        for all CONTROLLED systems with influence > 70%. 
        
        If time=="absolute", last_updated will be a UTC time string
        
        Elif time=="relative", last_updated will instead be a tuple 
        (days, hours, minutes) of how long ago it was updated
        
        """

        ctrl_names = [sys["name"] for sys in self.ctrl_full]
        
        ## Finding [system_name, influence, last_updated]  
        
        # List of systems where you have >70%
        ctrl_over_70 = [bgs_info.name_inf_updated(sys)
            for sys in self.fac_inf 
            if sys["influence"] > min_inf
        ]
        
        ctrl_over_70 = sorted(ctrl_over_70, key=lambda x: -x[1])
        
        ctrl_over_70 = [x for x in ctrl_over_70 if x[0] in ctrl_names]            
        ctrl_over_70_names = [x[0] for x in ctrl_over_70]
        
        ## Finding theoretical max inf, which needs population, which is in the
        #  other json...
        relevant_ctrl_sys = [x for x in self.ctrl_full
                             if x["name"] in ctrl_over_70_names]
        
        max_inf = [bgs_info.max_influence(sys,self.fac_name) 
                   for sys in relevant_ctrl_sys]
        
        # Putting it all together
        full_info = [[*x,y] for x,y in zip(ctrl_over_70, max_inf)] 
        
        
        ## Formatting
        if time.lower()=="relative":
            full_info = [[a,b,bgs_info.time_difference(c),d] 
                         for a,b,c,d in full_info] 
        
        return full_info
        

    ##### VULNERABILITY #####

    def vulnerability (self, time="relative"):
        """    
        Returns:
            1) A list of ["system_name", num_factions, last_updated]
               of all your controlled systems if the number of factions 
               in that system is less than 7
               
            2) A list of [system_name, retreating_faction_inf, last_updated]
               of all your controlled systems if there is a faction in retreat
               in that system. 
               
            last_updated is a tuple (d,h,m) of time since the system was last
            updated
    
        """
        ctrl_7 = [bgs_info.less_than_seven(x) for x in self.ctrl_full]
        ctrl_7 = sorted([x for x in ctrl_7 if x],
                        key=lambda x: x[1])
        
        ctrl_retreat = [bgs_info.active_retreat(x) for x in self.ctrl_full]
        ctrl_retreat = [x for x in ctrl_retreat if x]
        
        if time.lower() == "relative":
            ctrl_7 = [
                [a, b, bgs_info.time_difference(c)]
                 for a,b,c in ctrl_7
            ]
            
            ctrl_retreat = [
                [a, b, bgs_info.time_difference(c)]
                 for a,b,c in ctrl_retreat
            ]
        
        return ctrl_7, ctrl_retreat
    
    
    ##### RECON #####
    
    def recon (self, days, time="relative"):
        """
        Returns a list of [system_name, last_updated] for all systems your
        faction have a PRESENCE in that hasn't been updated in more than days days
        
        """
        # I tried my best to make this look readable
        older = [ 
                  [sys["system_name"], sys["updated_at"]]
                  for sys in self.fac_inf if bgs_info.age(sys, days) 
       ] 
        
        if time.lower() == "relative":
            older = [
                      [x, bgs_info.time_difference(y)] 
                     for x,y in older
            ]
            
        older = sorted(older, key=lambda x: (x[1][0], 
                                             x[1][1], 
                                             x[1][2]),
               reverse=True)
        
        return older
    
    
    ##### STATUS #####
    
    def status (self):
        dinf = [bgs_info.get_recon_info(sys)
                for sys in self.ctrl_full
        ]
        
        dinf = sorted(dinf, key=lambda x: x[2])
        
        g,y,r = bgs_info.status_report(dinf)
        
                
        return g,y,r 
    

    def plot(self, what):
        """
        Makes some matplotlib plots, for fun
        
        """
        if what.lower() == "influence":
            # Histogram of faction influence in controlled systems
            expansion_inf = [b for a,b,c,d in self.expansion_info(0)]
            
            size = 5
            lowest, highest = min(expansion_inf), max(expansion_inf)

            bin_low = size*round(lowest/size)
            bin_high = size*round(highest/size)

            ## Matplotlib wizardy:
            fig, ax = plt.subplots(constrained_layout=True)
            
            ax.set_title("{} Influence in Controlled Systems".format(
                self.fac_name))
            ax.set_xlabel("Influence (%)")
            ax.set_ylabel("Number of Systems")
                  
            ax.hist(expansion_inf, 
                    edgecolor="black",
                    bins=np.arange(bin_low,bin_high,size))
            
        return fig


    def __repr__(self):
        return "I'm not sure what to put here yet"
        
       
    ##### HELPER STUFF #####:
    
    @staticmethod
    def time_difference(time_str):
        """
        Finds the last updated given the last_updated string in the JSON data.
        Returns d,h,m which are the days,hours,minutes since the EDDN (EliteBGS)
        update for that system, respectively.
        
        """
        time = time_str.split(".")[0].replace("T", " ")
        time_format = "%Y-%m-%d %H:%M:%S"
        
        last_updated = datetime.strptime(time, time_format)
        
        time_diff = datetime.utcnow() - last_updated
        sec = time_diff.seconds
        
        d,h,m = time_diff.days, sec//3600, (sec//60) %60
        
        return d,h,m


    ### Expansion ###
    
    @staticmethod
    def name_inf_updated (sys):
        name = sys["system_name"]
        inf_percentage = 100*sys["influence"]
        last_updated = sys["updated_at"]
    
        return [name, inf_percentage, last_updated]    
    
    
    @staticmethod
    def sys_fac_influences (sys):
        """
        Returns a sorted list of [faction, influence] for a particular system.

        """
    
        facs = sys["factions"]
        
        fac_inf = [
            [f["name"], f["faction_details"]["faction_presence"]["influence"]] 
            for f in facs
        ]
        
        fac_inf = sorted(fac_inf, key=lambda x: -x[1])
        
        return fac_inf

    
    @staticmethod
    def max_influence (sys, name="Simbad Regime"):
        """
        Finds the max ending influence for a system based on its population and
        starting INF
        """    
        
        faction = [x for x in sys["factions"] 
                   if x["name_lower"] == name.lower()][0]
        
        pop = sys["population"]
        
        inf_start = faction["faction_details"]["faction_presence"]["influence"]
        inf_start *= 100 
        
        nume = inf_start + (36-math.log2(pop))
        denom = 100 + (36-math.log2(pop))
        
        max_inf = 100*nume / denom
        
        return max_inf


    @staticmethod
    def get_fac_inf (sys, name):
        """
        Finds your influence in a sys
        
        """
        faction = [x for x in sys["factions"] 
                   if x["name_lower"]==name.lower()][0]
        
        inf = faction["faction_details"]["faction_presence"]["influence"]
        
        return inf
    
    
    ### Vulnerability ###
    
    
    @staticmethod
    def active_retreat (sys):
        """
        Given a sys in the Systems json format, returns a list 
        [faction_name, faction_influence, updated_at] for all retreating factions
        in a system
        
        """
        retreat_fac_info = []
        
        # Locating the states for each faction:
        for fac in sys["factions"]:
            presence = fac["faction_details"]["faction_presence"]
            states = presence["active_states"]
            
            # Change i.e. [ {'state': 'retreat'}, {'state': 'expansion'} ] into
            # ["retreat", "expansion"]
            if any(states):
                state_list = [list(x.values())[0] 
                              for x in states]
                
                if "retreat" in state_list:            
                    name = fac["name"]
                    inf_percentage = 100*presence["influence"]
                    last_updated = sys["updated_at"]
                    
                    retreat_fac_info.append([name,
                                             inf_percentage,
                                             last_updated
                                             ])  
            
        return retreat_fac_info
    
    @staticmethod   
    def less_than_seven (sys):
        
        num_factions = len(sys["factions"])
        
        if num_factions < 7:
            return [sys["name"],
                    num_factions,  
                    sys["updated_at"]]

    ### Recon ###
    
    @staticmethod 
    def age(sys, days):
        """
        Returns the boolean of if a system's last updated is older than days
        
        """
        last_updated_utc = sys["updated_at"]
        last_updated = bgs_info.time_difference(last_updated_utc)
        
        return last_updated[0] > days
    
    
    ### Status ###
    
    @staticmethod 
    def get_recon_info (sys):
        name = sys["name"]
        inf_diff = bgs_info.sys_status(sys)
        last_updated = sys["updated_at"]
        
        return [name, inf_diff, last_updated]
    
    
    @staticmethod
    def sys_status (sys):
        """
        Given a system, returns the difference between the INF of highest inf
        and the INF of the second highest inf factions
        
        """
        
        fac_inf = bgs_info.sys_fac_influences(sys)
        assert fac_inf == sorted(fac_inf, key=lambda x: -x[1])    
        highest_inf = fac_inf[0][1]
        inf_diff = highest_inf - fac_inf[1][1]
        
        return inf_diff
    
    
    @staticmethod
    def status_report (inf_diff_list, g=20, y=(20, 10), r=10):
        """
        Returns green, yellow, red, which are lists of 
        [system_name, d_inf, last_updated] for all of your controlled
        systems. 
        
        d_inf: Difference in influence between the CF (you) and the 
        faction with the 2nd highest influence.
        
        Green: d_inf > 30%
        Yellow: 20% > d_inf > 10%
        Red: d_inf < 10%
        
        """
        yu, yl = y
        
        inf_diff_list = sorted(inf_diff_list, key=lambda x: -x[1])
        
        names = np.array([x[0] for x in inf_diff_list])
        inf = 100*np.array([x[1] for x in inf_diff_list], dtype="float32")
        last_updated = np.array([x[2] for x in inf_diff_list])
        
        index_g = np.argwhere(inf>g)
        index_y = np.argwhere(np.logical_and(yu>inf, inf>yl))
        index_r = np.argwhere(inf<r)
        
        green = np.hstack( 
            (names[index_g], inf[index_g], last_updated[index_g]) 
        )
        
        yellow = np.hstack(
            (names[index_y], inf[index_y], last_updated[index_y])
        )
        
        red = np.hstack(
            (names[index_r], inf[index_r], last_updated[index_r])
            )
        
        return green, yellow, red






















