info.variables_guardar = {'ynomin' 'i' 'r' 'rer' 'drer' 'deus' 'yx_emer'...
            'yx_avan' 'embi_ch' 'iUSTbill90' 'inflIPE' ...
            'inflIPC' 'infla' 'infle' 'inflsae' 'U' 'tdi' 'px_pcu' 'pcu' 'px_pnpcu' 'px' 'pm' 'pm_oil' 'pm_pnoil' 'pmoil' 'inflsae_core'	'inflsae_core_nt'	'inflsae_core_t' 'inflsae_resto'};

var_names = info.variables_guardar;

info.varexo_model= cellstr(M_.exo_names)';          

VARexo= info.varexo_model;

%%subsample
info.shockstorelease = {'zzi' 'zzynomin' 'zzsae_core_nt' 'zzsae_core_nt_s' 'zzsae_core_t' 'zzsae_core_t_s' 'zzsae_resto'...
            'zzsae_resto_s' 'zzdeus' 'zzpcu'};

VARexo2= info.shockstorelease;

%standar deviation of shocks
shocks_sd = zeros(length(VARexo2),1);
for ii=1:size(M_.Sigma_e,2)
    shocks_sd(ii,1)=M_.Sigma_e(ii,ii)^(1/2);
end

example = eval(['[' [char(var_names(:,1)),'_'] ,char(VARexo2(:,1)) ']']);

IRF_raw = zeros(length(example),size(var_names,2),length(VARexo2));
IRF = IRF_raw;

 for k = 1:size(VARexo2,2)
   
     shock = char(VARexo2(:,k));
     variables = [];
     irfs = [];
     for j = 1:size(var_names,2)
         variable = char(var_names(:,j));
         variables = [variables {variable}];
		IRF_raw(:,j,k) = eval(['[' [char(var_names(:,j)),'_'] ,char(VARexo2(:,k)) ']']);
		IRF(:,j,k) = IRF_raw(:,j,k)/shocks_sd(k,1)/100;
        irfs = [irfs IRF(:,j,k)];
     end
     xlswrite(file_out,irfs*100,[shock '_'  info.modelo_utilizado],'A3');
     xlswrite(file_out,variables,[shock '_' info.modelo_utilizado],'A2');
     
    
 end          

 