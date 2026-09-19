clearvars -except main_path

model_path= [main_path 'Decomp_code\Model\'];
data_path= [main_path 'IRF_code\Data\'];
results_path= [main_path 'Results\'];

%% Put data in folders
cd(data_path)
put_data_in_folder_final;

%% MEP TNT Estimation 
cd(model_path)
dynare('calculate_decomp.mod','nointeractive','noclearall');

%% Make Variance Descomposition
cd(results_path);
Print_var_dec







