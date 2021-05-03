# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 17:32:49 2021

@author: Josh
"""


import discord

from discord.ext import commands
from helper.gal_helper import bgs_info

from static.paths import *
from config.welcome_messages import *
from config.role_perms import * 




############################################################
# Most of the code in the bot file is just for             #    
# string formatting and sending it to the Discord channel. #
# I absolutely hate string formatting and the code for it  #
# is neither efficient nor readable.                       #
                                                           #
# The "interesting" stuff is in the "gal_helper"           #
############################################################



### Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', 
                   intents=intents, 
                   help_command=None)  # Bot commands start with "$"


### "Global" variables

# Loading in json data

simbad = bgs_info(simbad_controlled_full_path, 
                  simbad_controlled_influence_path,
                  "Simbad Regime",
                   False)

### Bot commands

@bot.event
async def on_ready ():
    print("Stayin' Alive")
    

@bot.command()
async def oops (ctx, *args):
    
    ### Finding bot command
    if len(args) == 0:
        command = 'help'
    else:
        command = args[0].lower()
    
    
    ### Find when the last request was made:
    
    ### Update json files
    if command == "update":
        await ctx.send("Beginning update, this will take a minute")
        simbad.update_info()
        await ctx.send("Update done!")
    
    
    ## Simbad controlled systems with Inf > 70%
    if command == "expansion":
        full_info = simbad.expansion_info()
        since_update = simbad.last_updated()
        
        # I absolutely hate string formatting, and I am so terrible at it
        
        template = "{0:15} | {1:5}   | {2:5}   | {3:15}\n" 
        msg = template.format("System", "Inf %", '"Max" %', "Last Updated")
        msg += 52*"=" +"\n"
        
        for name,inf,update,max_inf in full_info:
            inf_2f = "{:.2f}".format(inf)
            max_inf_2f = "{:.2f}  ".format(max_inf)
            
            day,hour,mins = [str(x) for x in update]
            
            formatted = "{}D {}H {}M".format(day.zfill(2),
                                             hour.zfill(2),
                                             mins.zfill(2))
            
            msg += template.format(name, inf_2f, max_inf_2f, formatted)
            msg += 52*"—"+"\n"
            
        msg += simbad.last_updated()
        
        await ctx.send("**List of all Simbad controlled systems with >70% Influence**")
        await ctx.send("```{}```".format(msg))
    
    
    elif command == "vulnerability":
        # ctrl_7: less than 7 factions in system
        # ctrl_retreat: system with at least 1 retreating faction
        ctrl_7, ctrl_retreat = simbad.vulnerability()
        
        template = "{0:15} |{1:5} | {2:15}\n" 
        msg = template.format("System", "Fac #/INF", "Last Updated")
        msg += 41*"=" +"\n"
    
        for x,y,z in ctrl_7:
            name = "{}".format(x)
            num_factions = " {}       ".format(int(y))
            d,h,m = [str(foo) for foo in z]
            
            formatted = "{}D {}H {}M".format(d.zfill(2),
                                 h.zfill(2),
                                 m.zfill(2))
            
            msg += template.format(name, num_factions, formatted)
            msg += 41*"—"+"\n"                
            
        for x,y,z in ctrl_retreat:
            name = "{}".format(x)
            retreat_inf = "{:.2f}   ".format(y)
            d,h,m = [str(foo) for foo in ctrl_retreat]
            
            formatted = "{}D {}H {}M".format(d.zfill(2),
                     h.zfill(2),
                     m.zfill(2))
            
            msg += template.format(name, retreat_inf, formatted)
    
        msg += simbad.last_updated()
    
        
        
        await ctx.send("**Simbad controlled systems with <7 factions or there is a retreating faction in the system**")
        await ctx.send("```{}```".format(msg))
    
    
    elif command == "recon":
        # List of systems that haven't been updated in X days
        days = int(args[1])
        template = "{0:15} | {1:15}\n" 
        
        older = simbad.recon(days)

        msg_old = template.format("System", "Last Updated") 
        msg_old += 36*"=" + "\n"
        
        
        for x,y in older:
            bold_sys = "{}".format(x)
            formatted = "{}D {}H {}M".format(*y)
            
            msg_old += template.format(bold_sys, formatted)
        
        msg_old += "\n" + simbad.last_updated()
        
        await ctx.send("**List of Simbad presence systems that hasn't been updated in {} days**".format(
            days))
        await ctx.send("```{}```".format(msg_old))
        
    
    elif command == "status":  
        detail = "short"
        
        if len(args) > 1:
            detail = args[1].lower()
        
        # BGS status report
        # d_inf = highest_inf - second_highest_inf 
        # ok: d_inf > 30%
        # caution: 20% > d_inf > 10%
        # warning: d_inf < 10%
        
        ok, caution, warning = simbad.status()
        
        template = "{0:15} | {1:5}  | {2:8} | {3:15}\n" 
        
        if detail == "short":
            
            msg_status = template.format("System", "ΔInf", "Status", "Last Updated")
            msg_status += 49*"=" + "\n"
            
            for a,b,c in caution:
                sys_name = "{}".format(a)
                inf_diff = "{:.2f}".format(float(b))
                sys_status = "Caution"
                
                time_diff = bgs_info.time_difference(c)
                d,h,m = [str(foo).zfill(2) for foo in time_diff]
                
                last_update = "{}D {}H {}M".format(d,h,m)
                
                msg_status += template.format(sys_name,inf_diff,
                              sys_status,last_update)
                
                msg_status += (49*"—" + "\n")


            for a,b,c in warning:
                sys_name = "{}".format(a)
                inf_diff = "{:.2f}".format(b)
                sys_status = "Caution"
                
                time_diff = bgs_info.time_difference(c)
                d,h,m = [str(foo).zfill(2) for foo in time_diff]
                
                last_update = "{}D {}H {}M".format(d,h,m)
                
                msg_status += template.format(sys_name,inf_diff,
                              sys_status,last_update)
                
                msg_status += (49*"—" + "\n")
                
                
            msg_status += "\n" + simbad.last_updated()
            await ctx.send("```{}```".format(msg_status))
            

    
#%%

bot.run(secret_key)
