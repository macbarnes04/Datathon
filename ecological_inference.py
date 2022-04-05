import pandas as pd
import numpy as np
import pymc3 as pm

from pyei.data import Datasets
from pyei.two_by_two import TwoByTwoEI
from pyei.goodmans_er import GoodmansER
from pyei.goodmans_er import GoodmansERBayes
from pyei.r_by_c import RowByColumnEI

from pyei.plot_utils import tomography_plot
from pyei.plot_utils import plot_precinct_scatterplot
df = pd.read_csv("tracts.csv")

# generate percentages
# check on datapoints by year
df["county"] = df["geoid"].astype(str).str[2:7].str.strip("0").str[0:3].astype(int)
df["other%"] =  100-(df["white%"] + df["black%"] + df["hispanic%"])
df[["white%","black%", "hispanic%", "other%"]] = df[["white%","black%", "hispanic%", "other%"]]/100
df["none"] = 100-df["100/20%"]

df[["none","100/20%"]] = df[["none","100/20%"]]/100
df = df.dropna()
df["population"] = df["population"].astype(int)
for i,group in df.groupby("county"):
    print(group.iloc[0])
    print(i)
    exit()
    #print(group)
    
    race_fractions = np.array(group[["white%", "black%", "hispanic%", "other%"]]).T
    access_fractions = np.array(group[["100/20%","none"]]).T

    race_names = ["White", "Black", "Latino", "Other"]
    access_names = ["Broadband Access", "No Broadband Access"]

    tract_pops = np.array(group["population"])
    ei_rbyc = RowByColumnEI(model_name='multinomial-dirichlet-modified', pareto_shape=100, pareto_scale=100)
    ei_rbyc.fit(race_fractions, 
       access_fractions, 
       tract_pops, 
       demographic_group_names=race_names, 
       candidate_names=access_names, 
    )

    print(ei_rbyc.summary())
    print('here')
    exit()