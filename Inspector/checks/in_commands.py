import maya.cmds as mc
 
def triangle_count(objects_list,settings):
    max_count = settings["options"][0]["max"][1]         
    discrepancy_list = []  
    for obj in objects_list:
        count = mc.polyEvaluate(obj, t=True)             
        if count > int(max_count):                      
            error = "Object has {} triangles and exceeds {} maximum count".format(count,max_count)
            discrepancy_list.append([obj,error])         
    return discrepancy_list

def lamina_faces(objects_list):  
    discrepancy_list = []      
    for obj in objects_list:
        lamina_faces = mc.polyInfo(obj, lf=True)
        if lamina_faces != None:
            error = "Object has lamina faces"
            discrepancy_list.append([obj,error,lamina_faces])
    return discrepancy_list           

def missing_UVS(objects_list):
    discrepancy_list  = []   
    for obj in objects_list:        
        if mc.polyEvaluate(obj, uvShell=True) == 0:
            error = "Object has no uv shells"
            discrepancy_list.append([obj,error])  
    return discrepancy_list

def naming_convention(objects_list,settings):  
    discrepancy_list  = [] 
    prefixes = ""
    error_obj = []
    for p in settings["options"]:
        prefixes = prefixes + p.values()[0][1]  
        for obj in objects_list:                     
            if prefixes not in obj:
                error = "Object name {} doesn`t have {} prefix".format(obj,prefixes)  
                if obj not in error_obj:         
                    discrepancy_list.append([obj,error])        
        for index in discrepancy_list:
            error_obj.append(index[0])
    return discrepancy_list

def history(objects_list):
    discrepancy_list  = []  
    for obj in objects_list:
        if len(mc.listHistory(obj)) > 1:
            error = "Object has history"
            discrepancy_list.append([obj,error])
    return discrepancy_list  

