
#####################
### BACKEND STUFF ###
#####################

import numpy as np

def status (self):
    dinf = [bgs_info.get_recon_info(sys)
            for sys in self.ctrl_full
    ]
    
    dinf = sorted(dinf, key=lambda x: x[2])
    
    g,y,r = bgs_info.status_report(dinf)
    
            
    return g,y,r 


### Helper functions for status ###

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
    Returns green, yellow, red, which are are systems that are OKAY, CAUTION,
    WARNING, respectively. 
    
    Parameters: 
        inf_diff_list - A list of [system, inf_difference, last_updated]. This
        is also the output of "get_recon_info()"
        
        g, y, r: thresholds for OK, CAUTION, WARNING
        
    RETURNS:
        green - list of [system_name, inf_diff, last_updated] for OK systems
        yellow - same but for caution
        red - same but for warning
    """
    yu, yl = y   # upper/lower bound for "CAUTION" 
    
    inf_diff_list = sorted(inf_diff_list, key=lambda x: -x[1])  # sort by inf_diff
    
    names = np.array([x[0] for x in inf_diff_list])
    inf = 100*np.array([x[1] for x in inf_diff_list], dtype="float32")
    last_updated = np.array([x[2] for x in inf_diff_list])
    
    
    # Find indices for OK, CAUTION, and WARNING
    index_g = np.argwhere(inf>g)    
    index_y = np.argwhere(np.logical_and(yu>inf, inf>yl))
    index_r = np.argwhere(inf<r)
    
    # Stacking [system_name, inf_diff, and last_updated]
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
    
    
######################
### FRONTEND STUFF ###
######################

@bot.command()
async def oops (ctx, *args):

# stuff for $oops expansion, $oops recon, etc. here 

    elif command == "status":  
        detail = "short"
        
        if len(args) > 1:
            detail = args[1].lower()
        
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
            
            
            title = "Difference in INF to the 2nd highest INF in Simbad controlled"
            title += "systems\nCAUTION: Difference between 10% and 20%. WARNING: "
            title += "Difference < 10%"
            
            await ctx.send(title)
            await ctx.send("```{}```".format(msg_status))
   
    
    
