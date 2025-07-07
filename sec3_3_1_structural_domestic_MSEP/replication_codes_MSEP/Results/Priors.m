save_file = [results_path 'parameters_3.xlsx'];

%PRIOR MEAN
prior_mean=oo_.prior.mean;
prior_mean=prior_mean(31:end);
xlswrite(save_file, prior_mean, 'Table 3 Estimated Parameters','D3');
%xlswrite(save_file, Posterior_mode_v, 'Parameters_MSEP','V3');

%Write headers
% xlswrite('parameters_3.xlsx', {'''Posterior mode'}, 'Parameters_MSEP','S1')
%xlswrite('parameters_3.xlsx', {'''names_param'}, 'Table 3 Estimated Parameters','S2')
xlswrite('parameters_3.xlsx', {'''Prior mean'}, 'Table 3 Estimated Parameters','D2')
%xlswrite('parameters_3.xlsx', {'''Posterior mode'}, 'Parameters_MSEP','V1')
%xlswrite('parameters_3.xlsx', {'''exo_variables'}, 'Parameters_MSEP','V2')
%xlswrite('parameters_3.xlsx', {'''stardar_desviation'}, 'Parameters_MSEP','W2')


%PRIOR STANDARD DEVIATION
prior_sd=diag(oo_.prior.variance.^0.5);
prior_sd=prior_sd(31:end);
xlswrite(save_file, prior_sd, 'Table 3 Estimated Parameters','E3');
xlswrite('parameters_3.xlsx', {'''Prior mean'}, 'Table 3 Estimated Parameters','E2')






