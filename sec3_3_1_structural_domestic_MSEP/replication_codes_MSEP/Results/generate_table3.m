save_file = [results_path 'parameters_3.xlsx'];

%POSTERIOR MODE
posterior_mode_p=struct2cell(oo_.posterior_mode.parameters);
posterior_mode_names_p=fieldnames(oo_.posterior_mode.parameters);
xlswrite(save_file, posterior_mode_p, 'Table 3 Estimated Parameters','F3');
xlswrite(save_file, posterior_mode_names_p, 'Table 3 Estimated Parameters','B3');

%Write headers
xlswrite('parameters_3.xlsx', {'''Parameter'}, 'Table 3 Estimated Parameters','B2')
xlswrite('parameters_3.xlsx', {'''Distribution'}, 'Table 3 Estimated Parameters','C2')
xlswrite('parameters_3.xlsx', {'''Posterior mode'}, 'Table 3 Estimated Parameters','F2')

%%
%POSTERIOR MEAN
posterior_mean_p=struct2cell(oo_.posterior_mean.parameters);
posterior_mean_names_p=fieldnames(oo_.posterior_mean.parameters);
Posterior_mean_p=[posterior_mean_p];
xlswrite(save_file, Posterior_mean_p, 'Table 3 Estimated Parameters','G3');

%Write headers
xlswrite('parameters_3.xlsx', {'''Posterior mean'}, 'Table 3 Estimated Parameters','G2')

%%
%INF
posterior_inf_p=struct2cell(oo_.posterior_hpdinf.parameters);
posterior_inf_names_p=fieldnames(oo_.posterior_hpdinf.parameters);
Posterior_inf_p=[posterior_inf_p];

xlswrite(save_file, Posterior_inf_p, 'Table 3 Estimated Parameters','H3');

%Write headers
xlswrite('parameters_3.xlsx', {'''p5'}, 'Table 3 Estimated Parameters','H2')

%%
% SUP
posterior_sup_p=struct2cell(oo_.posterior_hpdsup.parameters);
posterior_sup_names_p=fieldnames(oo_.posterior_hpdsup.parameters);
Posterior_sup_p=[posterior_sup_p];

xlswrite(save_file, Posterior_sup_p, 'Table 3 Estimated Parameters','I3');

%Write headers
xlswrite('parameters_3.xlsx', {'''p95'}, 'Table 3 Estimated Parameters','I2')

%%
%PRIOR MEAN
prior_mean=oo_.prior.mean;
prior_mean=prior_mean(31:end);
xlswrite(save_file, prior_mean, 'Table 3 Estimated Parameters','D3');

%Write headers
xlswrite('parameters_3.xlsx', {'''Prior mean'}, 'Table 3 Estimated Parameters','D2')

%%
%PRIOR STANDARD DEVIATION
prior_sd=diag(oo_.prior.variance.^0.5);
prior_sd=prior_sd(31:end);
xlswrite(save_file, prior_sd, 'Table 3 Estimated Parameters','E3');
xlswrite('parameters_3.xlsx', {'''PriorSD'}, 'Table 3 Estimated Parameters','E2')

%ORDER TO MEET TABLE 3
datos_file   = [results_path 'parameters_3.xlsx'];
datos_sheet  = 'Table 3 Estimated Parameters';
datos_sheet2  = 'Table 5 Estimated Parameters';
datos_all= 'B2:I39'; 
datos_rangedata  = 'B3:I39'; 
datos_rangenames = 'B2:I2';


datos_2 = readtable(datos_file,'Sheet',datos_sheet,'Range',datos_all);

datos_3 = [datos_2(1:11,:); datos_2(13:16,:); datos_2(19,:); datos_2(17:18,:); datos_2(12,:); datos_2(20,:); datos_2(35,:); datos_2(34,:);  
datos_2(24,:); datos_2(23,:); datos_2(22,:); datos_2(36:37,:); datos_2(27:28,:); datos_2(30:33,:); datos_2(25:26,:) ]; 

aux_columndatos_3 = ["B"; "B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B";"N";"G";"B";"B";"B";"B";"B";"B";"B";"B";"B";"B"];
datos_3.Distribution= aux_columndatos_3;

delete('parameters_3.xlsx');
writetable(datos_3,'Parameters.xlsx','Sheet',datos_sheet,'Range', datos_all)
