
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% cd(info.modelo_dir);
% modelo = info.modelo;

% vars={'y', 'inflsae','i', 'exp_inf', 'model_exp_sae','inflsae_nt','inflsae_t',};
% u_forecast = {'forecast_output_1','forecast_sae_1','forecast_sae_nt_1','forecast_sae_t_1','forecast_tpm_1','forecast_growth_1'...
%                ,'forecast_output_2','forecast_sae_2','forecast_sae_nt_2','forecast_sae_t_2','forecast_tpm_2','forecast_growth_2'...
%                ,'forecast_output_3','forecast_sae_3','forecast_sae_nt_3','forecast_sae_t_3','forecast_tpm_3','forecast_growth_3'...
%                ,'forecast_output_4','forecast_sae_4','forecast_sae_nt_4','forecast_sae_t_4','forecast_tpm_4','forecast_growth_4'};
% u_errors = {   'error1_output','error1_sae','error1_sae_nt','error1_sae_t','error1_tpm','error1_growth'...
%                 ,'error2_output','error2_sae','error2_sae_nt','error2_sae_t','error2_tpm','error2_growth'...
%                 ,'error3_output','error3_sae','error3_sae_nt','error3_sae_t','error3_tpm','error3_growth'...
%                 ,'error4_output','error4_sae','error4_sae_nt','error4_sae_t','error4_tpm','error4_growth'};

%vars={'ynomin', 'inflsae','inflsae_nt','inflsae_t','inflIPC','i','rer','tnt_relative'};
vars={'ynomin', 'inflsae','inflIPC','i','rer','tdi','U','dYnomin','pcu','pmoil','px_pcu','pm_oil','yx_emer','yx_avan','inflsae_core','inflsae_core_nt','inflsae_core_t','inflsae_resto'};

% errors={'error_tpm_1','error_tpm_2','error_tpm_3','error_tpm_4'...
%       ,'error_tpm_5','error_tpm_6','error_tpm_7','error_tpm_8'};
% 
% errors2={'error_inflsae_1','error_inflsae_2','error_inflsae_3','error_inflsae_4'...
%       ,'error_inflsae_5','error_inflsae_6','error_inflsae_7','error_inflsae_8'};
%       
% total=[vars,errors,errors2];            
total=[vars];            

                
cell_obs = 'AS2';

addpath('N:\GAM\DPM\MODELOS\MEP\newplataforma_MEP\IPoM\Programas\MEP_code_2018_Dif_Modelos');



%Hace el HD:

varlist=[];
%oo_2 = shock_decomposition_2(M_,oo_,options_,varlist);
oo_2 = shock_decomposition_2_calib(M_,oo_,options_,varlist);

endo_names1 =deblank(char(M_.endo_names));
shocks_names = deblank(char(M_.exo_names));
shocks_names1 = cellstr(shocks_names)';

%El LOOP recupera la descomposicion
for i = 1:length(total)

 variable=char(total(i));
    
 f = loc(endo_names1,variable);
 
 descomp = oo_2.shock_decomposition(f,:,:);
 descomp= reshape(descomp,[size(descomp,2),size(descomp,3)]);
 descomp =descomp'; 

xlswrite(save_file,shocks_names1,variable,'B1');
xlswrite(save_file,descomp,variable,'B2');
smoothed=getfield(oo_.SmoothedVariables,variable);
xlswrite(save_file,smoothed,variable,cell_obs);
end

%Escribre los Shocks en excel -- proyeccion limpia
% Shocks_1=struct2table(oo_.SmoothedShocks);
% writetable(Shocks_1,save_file,'sheet','Shocks_1','range','B2');

