clearvars -except main_path

code_path= [main_path 'HD_code\Codes\'];
model_path= [main_path 'HD_code\Model\'];
data_path= [main_path 'IRF_code\Data\'];
results_path= [main_path 'Results\'];


%% Put data in folders
cd(data_path)
put_data_in_folder_final;


%% Dynare
cd(model_path)
dynare('calculate_HD.mod','nointeractive','noclearall');


%% Make Shock Descomposition
cd(code_path)
save_file = [ results_path 'HD_MSEP.xlsx'];
HD_MSEP;




