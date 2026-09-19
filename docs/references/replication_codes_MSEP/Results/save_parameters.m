info.variables_guardar = {'ynomin' 'i' 'r' 'rer' 'drer' 'deus' 'yx_emer'...
            'yx_avan' 'embi_ch' 'iUSTbill90' 'inflIPE' ...
            'inflIPC' 'infla' 'infle' 'inflsae' 'U' 'tdi' 'px_pcu' 'pcu' 'px_pnpcu' 'px' 'pm' 'pm_oil' 'pm_pnoil' 'pmoil' 'inflsae_core'	'inflsae_core_nt'	'inflsae_core_t' 'inflsae_resto'};

 var_names = info.variables_guardar;
 info.varexo_model= cellstr(M_.exo_names)';          
 VARexo= info.varexo_model;     
 
 %Guardamos Parametros y Desvios Estandards
 names_param = cellstr(M_.param_names);
 param_values = cellstr(num2str(M_.params));

 exo_variables = cellstr(M_.exo_names);
 stardar_desviation = cellstr(num2str((diag(M_.Sigma_e.^0.5))));

 A =[names_param param_values];
 B= [exo_variables stardar_desviation];
 xlswrite(file_out,A,['Parameters_'  info.modelo_utilizado],'A2');
 xlswrite(file_out,B,['Parameters_'  info.modelo_utilizado],'D2');
 
 