# PLAnT-level dynamic Optimization model (PLATO)
## Model Overview

PLATO is a recursive dynamic decision-making model built on mixed integer linear programming functions. It has four distinguishing characteristics. 
First, coal plants can achieve emission reduction through a variety of low-carbon transformation technologies, including biomass and coal co-firing (BE), carbon capture and storage (CCS), flexibility operation (Flex), compulsory retirement (CR), choosing to remain as coal power plants (PP) or achieve natural retirement (NR). If the coal power plant has been retrofitted with BE and CCS technology, it can be regarded as a BECCS plant. 
Second, the decisions made by a plant during the previous period will influence its choices in the subsequent decision-making years. For example, a plant equipped with CCS can consistently capture carbon emissions from its retrofit year and can be further upgraded to a BECCS plant by retrofitting with BE technology. 
Third, this model addresses the resource competition issues among different coal plants. The biomass and coal co-firing ratio can vary among plants, depending on the mitigation requirement of the coal plant, the nearby biomass supply amount, and the competitiveness of the neighboring coal power plants. 
Fourth, the operating hours for each plant are designed as continuous variables, which means once a coal plant is retrofitted with Flex, its operation hours become flexible and will be determined by the model in each decision-making year. Moreover, to ensure that coal plants can reliably supply the necessary stable electricity amidst the integration of large-scale variable renewable energy sources, we also incorporate the scenarios generated by the power system as constraints. 

## Model Application
Now this model is applied to China’s 4,200+ coal plants as a case study, aiming to uncover opportunities for cost reduction within coal plants themselves and through effective policy design, thereby facilitating more ambitious goals for coal phase-out globally. It can be applied to other regions once the datasets for coal plants, biomass resources, and carbon storage sites are properly provided. 
