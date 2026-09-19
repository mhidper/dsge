This readme helps you to replicate the paper:

Arroyo Marioli, F., Bullano, F., Fornero, J., Zúñiga R. (2020), Semi-Structural forecasting model. Working paper #866 Central Bank of Chile.
https://www.bcentral.cl/contenido/-/detalle/semi-structural-forecasting-model

This distribution was made by Matías Solorza, Francisco Bullano and Roberto Zúñiga. 

********************************************************************************************************************************************
Software requirements:

Excel (English format for numbers)
Dynare (Tested on Dynare 4.6.1)
Matlab (Tested on Matlab 2018a)

********************************************************************************************************************************************


///////////////////////////////////
1)	Preparatory steps
///////////////////////////////////

Install Dynare. (www.dynare.org)

///////////////////////////////////
2)	Replication steps
///////////////////////////////////

2.1) 	Run MATLAB script "Option_file.m". Enter the option number depending on what you desire to replicate:

Option 1. Generates the files to replicate "Table 3: Estimated parameters", p.15.

Option 2. Generates Figures 3 to 7: Conditional Variance Decomposition, p. 20-21.

Option 3. Generates IRF. Matlab generates IRFs and Figures 8 to 12 are handled in Excel file ".\Results\IRF.xlsx", p.22-26.

Option 4. Generates Figures 13-14:Forecasts, p. 27-28.

Option 5. Generates Figure 15: Historical Shocks Decomposition, p. 30.


2.2)	All results are stored in ".\Results"

2.3)   To replicate with MSEP "Recuadro III.4, “Uso de Modelos Macroeconómicos en el Banco Central de Chile” (2020)." you sould change the
	parameter that multiplies the expectation term in the Phillips curve as stated in the box and then run Option 2 and save IRFs for the
	monetary shock.


Warning about results of option 1:

(i) To save time, this distribution calculates the posterior-mean of the parameters with 1,000 replications of the Metropolis-Hasting algorithm.
In contrast, the paper's results used 200,000 replications.

(ii) Note: There is a typo in the document. Mean Prior distribution of parameters in equations (10) is 0.20 instead of 0.25 and S.D. Prior distribution of parameters in equations (14) is 0.18 instead of 0.10.

Warning about results of option 3:

The "IRF.m" code generates Impulse Response Functions based on the impact of one-standar-distribution of the respective shock. In the "IRF.xlsx" 
the AL-AS columns calculate to replicate what is intended to be replicated.



********************************************************************************************************************************************