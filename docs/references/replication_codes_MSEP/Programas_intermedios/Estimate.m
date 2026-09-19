clearvars -except main_path

model_path= [main_path 'Estimate_code\Model\'];
data_path= [main_path 'IRF_code\Data\'];
results_path= [main_path 'Results\'];
code_path= [main_path 'Estimate_code\codigos\'];

%% Put data in folders
cd(data_path)
put_data_in_folder_final;

%% MEP TNT Estimation 
cd(model_path)
dynare('calculate_estimate.mod','nointeractive','noclearall');


%% Export parameters
cd(results_path)
file_out = [results_path 'parameters.xlsx'];
info =struct;
info.modelo_utilizado='MSEP';
generate_table3










