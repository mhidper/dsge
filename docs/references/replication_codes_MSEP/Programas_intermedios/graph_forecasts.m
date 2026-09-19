clearvars -except main_path

results_path= [main_path 'Results\'];
recursive_path= [main_path 'Programas_intermedios\'];
forecast_output_path= [main_path 'Programas_intermedios\recursive_forecast_output\'];

% Variables to be used
vars_names       ={'ynomin', 'inflsae', 'i'};
vars_names_latex       ={'y', '\pi^{XFE}', 'i'};

km = 1;
k2 = 18;
k2 =1;

% Setting of forecast
k = 22;       % Size of first recursive sample
h = 10;       % # of forecast periods
s = 70;       % Size of total sample
T = s+h;      % Size of total sample + # of forecast periods
dates = (2001.50:0.25:2018.75)';  % Dates


for j=1:length(vars_names)
    load(strcat([pwd '\recursive_forecast_output\' 'MEP_rec_forecasts'],'_',vars_names{j}))
    
    %Plot figure for NKSOE_search_0375 recursive forecasts
    hFig=figure(1);
    ywidth = 800/5*3;
    xwidth = 600;
    set(hFig, 'Position', [0 0 xwidth ywidth])
    
    subplot(length(vars_names),2,2*j-1);
    box on
    plot(dates,mat_smoothed(:,end),'k','LineWidth',1.5);
    hold on
    plot(dates,mat_forecast(:,k2:end),'r');
    xlim([2001.5 2018.75])
    ylabel(['$' vars_names_latex{j} '$'],'interpreter','latex','FontName','Times','FontSize',12,'Rotation',0,'HorizontalAlignment','right','VerticalAlignment','middle');
    if j==1
        ylim([-0.05 0.05])
    elseif j==2
        ylim([-0.02 0.02])
    elseif j==3
        ylim([0 0.1])
    else
        ylim([-0.2 0.2])
    end
    set(gca,'FontSize',12)
    set(gcf, 'PaperPosition', [0 0 14 14]);
    set(gcf, 'PaperSize', [14 28]);
    
    %Plot figure for NKSOE_search_075 recursive forecast
    load(strcat([forecast_output_path 'BVAR_base'],'_',vars_names{j}))
    subplot(length(vars_names),2,2*j);
    plot(dates,mat_smoothed(:,end),'k','LineWidth',1.5);
    hold on
    plot(dates,mat_forecast(:,k2:end),'r');
    xlim([2001.5 2018.75])
    if j==1
        ylim([-0.05 0.05])
    elseif j==2
        ylim([-0.02 0.02])
    elseif j==3
        ylim([0 0.1])
    else
        ylim([-0.2 0.2])
    end
    set(gca,'FontSize',12)
    set(gcf, 'PaperPosition', [0 0 14 14]);
    set(gcf, 'PaperSize', [14 22]);
    
    if j==length(vars_names)
        leg=legend('Data','Forecast');
        set(leg,'Position',[0.329 0.011 0.370 0.064],...
            'Orientation','Horizontal',...
            'FontName','Times',...
            'Fontsize',11);
        saveas(gcf,[results_path 'forecasts_CLASSIC.eps'],'epsc2');
        saveas(gcf,[results_path 'forecasts_CLASSIC.pdf'],'pdf');
        saveas(gcf,[results_path 'forecasts_CLASSIC.bmp'],'bmp');
        
       
    end
    
    %Plot RMSE
    figure(2)
    hFig = figure(2);
    ywidth = 800;
    xwidth = 800;
    set(hFig, 'Position', [0 0 xwidth ywidth])
    subplot(2,2,j);
    box on
    horizon=1:h;
    hold on
    load(strcat([pwd '\recursive_forecast_output\' 'MEP_rec_forecasts'],'_',vars_names{j}))
    if j == 2
        mat_RMSE = mat_RMSE*4;
    end
    plot(horizon,mat_RMSE*100,'-og','LineWidth',2,'MarkerFaceColor','g');
    
    if j~=4
        load(strcat([pwd '\recursive_forecast_output\' 'BVAR_base'],'_',vars_names{j}))
        if j == 2
            mat_RMSE = mat_RMSE*4;
        end
        plot(horizon,mat_RMSE*100,'-','LineWidth',2,'MarkerFaceColor','r');
    end
    
    load(strcat([pwd '\recursive_forecast_output\' 'BVAR_rer'],'_',vars_names{j}))
    if j == 2
        mat_RMSE = mat_RMSE*4;
    end
    plot(horizon,mat_RMSE*100,':','LineWidth',2,'MarkerFaceColor','b');
    
    load(strcat([pwd '\recursive_forecast_output\' 'BVAR_rer_foreign'],'_',vars_names{j}))
    if j == 2
        mat_RMSE = mat_RMSE*4;
    end
    plot(horizon,mat_RMSE*100,'--','LineWidth',2,'MarkerFaceColor','c');
    
    xlim([1 h]);
    ylim([0 4]);
    
    std_actual2 = std(mat_smoothed(38:end,end));
    
    if j == 2
        hline = refline([0 std_actual2*400]);
    else
         hline = refline([0 std_actual2*100]);
    end
    set(hline,'LineStyle','--','LineWidth',2)
    title(['$' vars_names_latex{j} '$'],'interpreter','latex','FontName','Times','FontSize',12)
    set(gca,'FontSize',14)
    set(gcf, 'PaperPosition', [0 0 20 20]);
    set(gcf, 'PaperSize', [20 20]);
    if j==length(vars_names)-1    
        leg=legend('MEP','BVAR1','BVAR2','BVAR3','s.d. datos');
        
        set(leg,'Position',[0.4 0.01 0.23 0.03],...
            'Orientation','Horizontal',...
            'FontName','Times',...
            'Fontsize',11);
         saveas(gcf,[results_path 'RMSE_CLASSIC.eps'],'epsc2');
         saveas(gcf,[results_path 'RMSE_CLASSIC.pdf'],'pdf');
         saveas(gcf,[results_path 'RMSE_CLASSIC.bmp'],'bmp');




        
        pos = get(hFig,'Position');
        
        set(hFig,'PaperPositionMode','Auto','PaperUnits','Inches','PaperSize',[pos(3), pos(4)])
        saveas(gcf,strcat('RMSE_CLASSIC'),'epsc2')
        saveas(gcf,strcat('RMSE_CLASSIC'),'png')
        saveas(gcf,strcat('RMSE_CLASSIC'),'bmp')
        
        
        
    end
    %try
         saveas(gcf,[results_path 'RMSE_CLASSIC.eps'],'epsc2');
         saveas(gcf,[results_path 'RMSE_CLASSIC.pdf'],'pdf');
         saveas(gcf,[results_path 'RMSE_CLASSIC.bmp'],'bmp');

    
end

cd(main_path)