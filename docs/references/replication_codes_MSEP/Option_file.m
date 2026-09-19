clear
close all

disp('Option 1. Generate section 4.2 results: Estimated parameters (mean)')
disp('Option 2. Generate section 5.1 results: Conditional Variance Decomposition')
disp('Option 3. Generate section 5.2 results: IRF')
disp('Option 4. Generate section 5.3 results: Forecasts')
disp('Option 5. Generate section 5.4 results: Historical Shocks Decomposition')


% Asignar la ruta del directorio actual a la variable main_path
main_path= 'C:\Users\Usuario\Documents\Github\DGSE\sec3_3_1_structural_domestic_MSEP\replication_codes_MSEP\';
 

addpath('Programas_intermedios\');

cont = 1;

while cont
    
    n = input('Enter a number: ');
    
    switch n
        
        case 1
            disp('Estimating parameters. Output —Parameters.xlsx— will be located in "Results" folder')
            Estimate % run selected m.file
            disp('Output —Parameters.xlsx— is located in "Results" folder')
            
        case 2
            disp('Generating Conditional Variance Decomposition. Figures —PNG files— will be located in "Results" folder')
            Decomp % run selected m.file  
            disp('Figures —PNG files— are located in "Results" folder')
            
        case 3
            disp('Generating IRF. Output —IRF.xlsx— will be located in "Results" folder')
            IRF % run selected m.file
            disp('Output —IRF.xlsx— is located in "Results" folder')
            
        case 4
            disp('Generating Forecasts')
            Forecast
            % run selected m.file
            disp('Figures and pdf files are located in "Results" folder')
            %cd(main_path);
            
        case 5
            disp('Generating Historical Shocks Decomposition. Output —HD.xlsx— will be located in "Results" folder')
            HD % run selected m.file
            disp('Output —HD.xlsx— is located in "Results" folder')
            
        otherwise
            disp('Please use a number from the list {1,2,3,4,5}')
    end
    
    cont = input('Do you want to run another excercise? (1 = yes; 0 = no): ');
        
end
