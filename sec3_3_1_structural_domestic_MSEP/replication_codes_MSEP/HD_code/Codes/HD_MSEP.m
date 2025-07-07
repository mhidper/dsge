vars={'ynomin', 'inflsae','i','rer'};
           
total=[vars];            
            
cell_obs = 'AS2';

%This part does the historical decomposition

varlist=[];
oo_2 = shock_decomposition_auxiliar(M_,oo_,options_,varlist);

endo_names1 =deblank(char(M_.endo_names));
shocks_names = deblank(char(M_.exo_names));
shocks_names1 = cellstr(shocks_names)';

for i = 1:length(total)

 variable=char(total(i));
    
 f = loc(endo_names1,variable);
 
 descomp = oo_2.shock_decomposition(f,:,:);
 descomp= reshape(descomp,[size(descomp,2),size(descomp,3)]);
 descomp =descomp'; 

xlswrite(save_file,shocks_names1,variable,'B3');
xlswrite(save_file,descomp,variable,'B4');
smoothed=getfield(oo_.SmoothedVariables,variable);

end



