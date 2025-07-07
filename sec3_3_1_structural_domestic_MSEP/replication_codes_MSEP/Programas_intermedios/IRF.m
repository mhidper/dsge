clearvars -except main_path

code_path= [main_path 'IRF_code\Codes\'];
model_path= [main_path 'IRF_code\Model\'];
data_path= [main_path 'IRF_code\Data\'];
results_path= [main_path 'Results\'];


%% Put data in folders
cd(data_path)
put_data_in_folder_final;

%% dynare
cd(model_path)
dynare('calculate_IRF.mod','nointeractive','noclearall');

%% Export IRFs

file_out = [results_path 'IRF.xlsx'];
cd(code_path)
info =struct;
info.modelo_utilizado='MSEP';
IRF_save;

%%




