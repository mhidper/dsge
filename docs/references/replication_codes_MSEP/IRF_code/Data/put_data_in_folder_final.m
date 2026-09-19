
datos_path = data_path;
datos_file   = [datos_path 'DB1.xlsx'];
datos_sheet  = 'Data';
datos_rangedata  = 'C6:AD77';  
datos_rangenames = 'C1:AD1';

datos_0 = readtable(datos_file,'Sheet',datos_sheet,'Range',datos_rangedata);

[~,names_0,~] = xlsread(datos_file,datos_sheet,datos_rangenames);
datos_0.Properties.VariableNames = names_0;

datos_0 = table2timetable(datos_0);

saveData(datos_0,[model_path, 'data_nueva_MEP_reducida']);


