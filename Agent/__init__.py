##ABM of investment in the power sector
import pandas as pd
import pdb
import numpy as np
from copy import deepcopy
from itertools import repeat
from operator import itemgetter 
import random

def func_read_in_data(data_file):
    # ~ df_slice_params = pd.read_excel("slice_param.xlsx",sheet_name="slice_params",header=0,index_col=0)
    data_slice_params = pd.read_excel(data_file,sheet_name="slice_params",header=0,index_col=0)
    data_initial_pp = pd.read_excel(data_file,sheet_name="input_initial_500",header=1)
    data_new_pp = pd.read_excel(data_file,sheet_name="new_pp",header=1)

    return data_slice_params,data_initial_pp,data_new_pp
    
    
def func_ABM(numyears, hr_input,data_file):
    slice_data,data_initial_pp,data_new_pp= func_read_in_data(data_file)
    #part 1. parameters of power plants.
    """
    # ~ capacity ## unit:KWe
    # ~ running_cost ## unit: cent/kWh
    # ~ investment_cost ## unit: KW * cent/KW
    # ~ lifetime ## unit:year
    # ~ emission_intensity ## unit: ton CO2eq/kWh
    """
    pp_list =['coal','gas','nuclear','solar','wind']
    coal_pp = {'plant_type': 'coal', 'capacity':500*10**3,'running_cost': 2,'investment_cost':145000*500*10**3,'lifetime':40,'emission_intensity':0.001}
    gas_pp = {'plant_type': 'gas', 'capacity':500*10**3,'running_cost': 4.5,'investment_cost':90000*500*10**3,'lifetime':30,'emission_intensity':0.00045}
    nuclear_pp = {'plant_type': 'nuclear', 'capacity':500*10**3,'running_cost': 1,'investment_cost':600000*500*10**3,'lifetime':40,'emission_intensity':0}
    solar_pp = {'plant_type': 'solar', 'capacity':500*10**3,'running_cost': 0,'investment_cost':80000*500*10**3,'lifetime':25,'emission_intensity':0}
    wind_pp = {'plant_type': 'wind', 'capacity':500*10**3,'running_cost': 0,'investment_cost':150000*500*10**3,'lifetime':25,'emission_intensity':0}

    capacity = {'nuclear':500*10**3,'coal':500*10**3,'gas':500*10**3,'solar':500*10**3,'wind':500*10**3}
    investment_cost = {'nuclear':600000*500*10**3,'coal':145000*500*10**3,'gas':90000*500*10**3,'solar':80000*500*10**3,'wind':150000*500*10**3}
    lifetime = {'nuclear':40,'coal':40,'gas':30,'solar':25,'wind':25}
    fuel_cost = {'biogas': 10,'nuclear':1,'coal':2,'natural_gas':4.5,'wind':0,'solar':0}
    ##================================================
    #part 2. company_params
    hr_lst = hr_input #hurdle rate use by agents.
    CRF = {} ##CRF = {(plant_type,hr):value}
    NPV_rate = {}
    for pp in pp_list:
        for hr in  hr_lst:
            CRF[(pp, hr)] =  hr/(1-(1+hr)**(-1*lifetime[pp]))
            NPV_rate[(pp, hr)] = (1-(1+hr)**(-1*lifetime[pp]))/ hr
    ##================================================
    #part 3. parameters of time slice, demand elesticity and carbon price.
    df_slice_params= slice_data
    demand_level = df_slice_params.loc['demand_level'].values
    slice_hours = df_slice_params.loc['slice_hours'].values

    avail_coal = df_slice_params.loc['coal_level'].values
    avail_gas = df_slice_params.loc['gas_level'].values
    avail_nuclear = df_slice_params.loc['nuclear_level'].values
    avail_solar = df_slice_params.loc['solar_level'].values
    avail_wind = df_slice_params.loc['wind_level'].values

    pp_avail_slice = {'coal':avail_coal,'gas':avail_gas,'nuclear':avail_nuclear,'solar':avail_solar,'wind':avail_wind}

    eps = -0.05
    p0 = 3 #cent/kWh.

    CarbonTax_lst = []##set carbon tax (cent/ton co2).
    for ts in range(0,100): ##ts is year.
        if ts <= 10: tax = 0  ## carbon tax is 0 before year 10.
        elif 10 <= ts <= 50: tax = 250 * ts - 2500 ## from year 10 to 50, carbon tax increases linearly to 10000 cent/ton.
        else:tax = 10000   ## after year 50, carbon tax stays at 10000 cent/ton.
        CarbonTax_lst.append(tax)
    ##================================================
    #part4. define function to calculate electricity price of each slice.
    def func_demand_supply(supply_lst,q0,plant_order,marginal_cost):##q0 = demand
        total_avail_capacity = sum(supply_lst)
        # ~ print('\n' + 'The total_avail_capacity is: ' + str(total_avail_capacity))
        eq_production = 0
    # =============================================================================
        for pos, pp_capacity in enumerate(supply_lst, start=0):
            eq_production += pp_capacity
            if eq_production == 0: continue
            demand_price = p0 * q0 ** (-1 / eps) * eq_production ** (1 / eps)
            
            if demand_price <= marginal_cost[pos]:
                eq_price = marginal_cost[pos]## means price will be the running cost of first type.
                eq_production = q0 * (eq_price / p0) ** eps 
                break
                
            else: ##if demand_price > run_costs[i]
                eq_price = demand_price
                if total_avail_capacity - eq_production > 0 and demand_price > marginal_cost[pos+1]: continue
                    ## first if :## if there is still remaining/unruned production/plants.second if: check if on the vertical line
                else: break ## if demand_price <= run_costs[i+1] or total_avail_capacity=max
        
        last_dispatch_type = plant_order[pos]  ##get the name of the last supply plant type.
        last_tp_dispatch_amount = eq_production - sum(supply_lst[0:pos])##dispatch amount from the last running type.
        last_dispatch_avail = supply_lst[pos] #available capacity of the last running type.
        return eq_price#,last_supply_percent,last_dispatch_type,eq_production

    ##================================================
    #part5. define function to calculate NPV and make investment desicions.
    """
    func_ex_ante_evaluation
    function that evaluate each investment option,
    and return profit index for each investment option for individual agents.
    Function input:
    -new_pp: the investment option (a type of plant) will be evaluated.
    -plant_order: the merit order of current plant.
    -AvailCapacity_lst: available capacity at each time slice for each type of plant.
    -maginal_cost_order: the cost of each plant, which is a sorted list.
    """
    def func_ex_ante_evaluation (new_pp,plant_order,AvailCapacity_lst,maginal_cost_order): 
        new_pp_index = plant_order.index(new_pp)
        
        avail_capacity_new_pp = 500000 * pp_avail_slice[new_pp]
        AvailCapacity_lst[new_pp_index] += avail_capacity_new_pp
        
        avail_capacity_slice = list(zip(AvailCapacity_lst[0],AvailCapacity_lst[1],AvailCapacity_lst[2],AvailCapacity_lst[3],AvailCapacity_lst[4]))
        eq_price_lst = np.array([func_demand_supply(supply,demand,plant_order,maginal_cost_order) for supply,demand in zip(avail_capacity_slice,demand_level)])
        price_diff= eq_price_lst- maginal_cost_order[new_pp_index] ##electricity price minus the marginal cost of the plant.
        slice_profit = price_diff * avail_capacity_new_pp #profiy of each time slice.
        slice_profit = np.where(slice_profit < 0, 0, slice_profit)
        annual_profit = (slice_profit * slice_hours).sum()# annual profit.
        ##pi=profit index for different hr (hr=hurdle rate).
        pi_hr = [annual_profit/investment_cost[str(new_pp)]- CRF[(new_pp, hr)] for hr in hr_lst]##profit index at different hurdle rates.
        #return the profit index for the 3 companies:
        return (new_pp,pi_hr[0]),(new_pp,pi_hr[1]),(new_pp,pi_hr[2])


    ##part5. main module
    pd.set_option('display.precision',3) ##dismal digits.
    pd.set_option('display.max_columns', 12)
    pd.options.mode.chained_assignment = None
    #finish import Python libraries.

    # abbreviation:
    #pp= power plant; df= (Pandas) data frame;yr=year;

    # =============================================================================
    ##read input data(read-in the data as Pandas framework)
    ##initial(year 0) power plants that are in the system.
    initial_pp = data_initial_pp
    df_pp = deepcopy(initial_pp)
    #characteriztic of new plants (coal,gas,PV,nuclear,wind)
    new_pp_chioce = data_new_pp
    
    tot_time_step = numyears#total time step is 70 years.
    ts = 0 #currrent time step. start from  0.
    ##in this model version,there are 3 heterogeneous agents who use different hurdle rates.
    invest_order = [0,1,2] ## the order of company for taking investment decision, shuffled annually. 
    annual_capacity = []#make an empty list for later restore: annaul capacity

    # =============================================================================
    if __name__ == "__main__":    
        while ts < tot_time_step:
            # ==================================================
            print('\n' + 'tot=' + str(tot_time_step) +'------Current year is ' + str(ts))
            carbon_tax = CarbonTax_lst[ts] ##current carbon tax.
            annual_tot_invest = []# empty lst.
            df_pp.reset_index(drop=True,inplace=True) ## reset the index of the (Pandas) data-framwork (df).
            random.shuffle(invest_order)# shuffle the investment order of companies.
         # =============================================================================    
        #   1.check decommission and lifetime -1.
            df_pp.lifetime_remain -= 1 ## the lifetime of each plant is subtract by 1. 
            df_next_year = df_pp.query('lifetime_remain > 0')##dismentle all retired plants when go to next year.
            
            if (df_pp['lifetime_remain']==0).any(): ##if any plant reaches end of its lifetime.
                dicommision_list = df_pp[df_pp['lifetime_remain']==0].sample(frac=1) ##list the to-be-retire plant to a new df, and shuffle the order by .sample()
                # ~ print('dicommision_list of current year:')
                # ~ print(dicommision_list[['name','plant_type','lifetime_remain']])
            df_pp_grouped = df_pp.groupby('plant_type',as_index=False).agg({'capacity':'sum','running_cost':'mean','emission_intensity':'mean'})##group the pp by plant type.
            
            
            ##=======record capacity for plotting================##
            # ~ annual_capacity.append(df_pp_grouped['capacity'])
            # ~ print('annual_capacity is ','\n',annual_capacity)

            ##====================================================#
            #2. oder the plant by marginal cost.
            df_pp_grouped['marginal_cost'] = df_pp_grouped['running_cost'] + carbon_tax * df_pp_grouped['emission_intensity'] #add carbon tax to the marginal_cost.
            fuel_cost_NatGas = fuel_cost['natural_gas']+ carbon_tax * 0.00045##0.00045=gas_pp['emission_intensity']
            df_pp_grouped.loc[df_pp_grouped['plant_type'] == 'gas', 'marginal_cost'] = min(fuel_cost_NatGas,fuel_cost['biogas']) ##choose between NG or bio-gas.
           
            df_pp_grouped.sort_values('marginal_cost',inplace=True)# sort the plant by it marginal cost (merit order).
            df_pp_grouped.reset_index(drop=False,inplace=True)
            
            plant_order = df_pp_grouped['plant_type'].tolist()# put the merit order in to a list.
            
        # =============================================================================
        #   3.Making invest decisions.
            while True:
                #step 3-1: retired old plants.
                if dicommision_list.size >0: #if any plant is remain to be decommission.
                    remove_plant = dicommision_list.iloc[-1]# only decommission one at a time.
                    df_pp_grouped.loc[df_pp_grouped['plant_type'] == remove_plant['plant_type'],'capacity'] -= remove_plant['capacity'] ##remove capacity of retired plant.
                    dicommision_list.drop(dicommision_list.index[-1],axis=0, inplace=True)
                #calculate available capacity at each time slice:
                df_pp_grouped['avail_capacities'] = [df_pp_grouped.loc[df_pp_grouped['plant_type'] == pp, 'capacity'].values * pp_avail_slice[pp] for pp in plant_order]
                # ~ print('avail_capacities of wind in each slice is :')
                # ~ print( df_pp_grouped.loc[df_pp_grouped['plant_type'] == 'wind','avail_capacities'])
            # =============================================================================
                #step 3-2:agents/companies make investment decisions.
                ##----------------decision-making------------------------------------##
                # ~ invest_made = func_decision_making(df_pp_grouped,carbon_tax,plant_order) ##investment function: take investment decisions.
                AvailCapacity_lst = df_pp_grouped['avail_capacities'].tolist() #copy the available capacity to a list.
                # ~ print('\n' + 'The avail_capacities is: ' + str(avail_capacities))
                maginal_cost_order = df_pp_grouped['marginal_cost'].tolist()#copy the merit order to a list.
                ##calculate profit for new pp
                profit_index = [func_ex_ante_evaluation(pp, plant_order, deepcopy(AvailCapacity_lst), maginal_cost_order) for pp in pp_list]
                
                invest_made = None##default investment=None.
                for compNr in invest_order: #iterate over company list.
                    pp_index = list(zip(*profit_index))[compNr]
                    pp_index = sorted(pp_index,key=itemgetter(1), reverse=True) #sort the list by the highest profit.
                    #print('pp_index ',pp_index)
                    # ~ pdb.set_trace()
                    if pp_index[0][1]> 0: # if the profit of the first plant is larger than zero.
                        invest_made = pp_index[0][0]##invest_made = plant type.then make investment.
                        break # go to decommision another old plant.
                    else: continue
                print('\n' + 'The invest_made is: ' + str(invest_made))
                ##----------------decision-making module ends------------------------------------##
                # =============================================================================
                # ~ print(invest_made)
                if invest_made is None:
                    if (dicommision_list['lifetime_remain']==0).any():##if more pp needs to be retired this year.
                        continue
                    else:
                        ts +=1 ##move to next step/year
                        # ~ rounds = 0
                        break 
                else:
                    df_pp_grouped.loc[df_pp_grouped['plant_type'] == invest_made,'capacity'] += 500000 ##add capacity of invested plant.
                    annual_tot_invest.append(new_pp_chioce.loc[new_pp_chioce['plant_type'] == invest_made])##append the newly invested plant to the df of the annual investment 'catalog'.
                    
                    #investment_list.append(invest_made['plant_type'])
                    # ~ df_pp = df_pp.append(new_pp_chioce.loc[invest_made],ignore_index=False,sort=False)## append new pp to df.
                    # ~ count_invest_pp[invest_made.plant_type.item()] += 1
                    continue
                
            annual_tot_invest.append(df_next_year)#append the all the investment from current year to the df.
            
            df_pp = pd.concat(annual_tot_invest, axis=0, ignore_index=True,sort=False,copy=False)#df concatenate.
            # ~ print('\n' + 'df_next_year is ------------' + '\n' + str(df_pp))
            continue
            # =========================================
        print('(main module)end')

    return df_pp_grouped
    

#capacity_mix = func_ABM(numyears=20, hr_input=[0.06,0.08,0.10],data_file="abm_data.xlsx")

