#
# dictionary of crime categories and synonyms
crimedict={
    'arson':[],
    'assault':['assault with a deadly weapon'],
    'attempted suicide':[],
    'auto burglary':[],
    'battery':[],
    'brandishing a weapon':[],
    'burglary/commercial':['commercial burglary'],
    'burglary/residential':['residential burglary'],
    'corporal injury to spouse/cohabitant':[],
    'disorderly conduct':[],
    'disturbance':[],
    'disturbance/domestic':['domestic disturbance'],
    'driving under the influence':[],
    'homicide':[],
    'identity theft':[],
    'missing person':['missing person - adult','missing person - juvenile'],
    'obscene phone calls':['obscene/annoying phone calls'],
    'possession':[],
    'possession/narcotics':['narcotics possession','possession of marijuana'],
    'probation':[],
    'rape':[],
    'reckless driving':[],
    'robbery':[],
    'shoplifting':[],
    'stolen vehicle':[],
    'suspected child abuse':[],
    'suspicious circumstances':['suspicious persons','suspicious circumstances/persons'],
    'terrorist threats':[],
    'theft/grand':['grand theft'],
    'theft/petty':['petty theft'],
    'trespassing':[],
    'vandalism':[]
}

def all_crimes():
    """
    return list of all crimes and their synonyms"""
    L=[]
    for k in crimedict.iterkeys():
        #
        # add the crime to the list
        L.append(k)
        
        # add synonyms to the list
        synonyms=crimedict[k]
        if synonyms!=None:
            L.extend(synonyms)

    return L
        
        

            

