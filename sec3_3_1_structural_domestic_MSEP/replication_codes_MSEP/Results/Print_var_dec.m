names = {'y','core_t','core_nt','i','rer'};
var_index = [5,11,10,23,31];
shocks = {'demand', 'costs', 'monetary', 'UIP', 'ffcond', 'finf', 'fdemand', 'tot', 'f&e', 'others'};
shocks_groups=[10,10,1,9,9,2,2,2,2,2,2,2,2,2,10,10,10,3,3,3,4,4,7,7,5,5,6,5,8,8,8,8,8,8,8,8,8]';


fevd = oo_.conditional_variance_decomposition(var_index,:,:);

n = 10;
fevd_new = Group_shocks(fevd,n,shocks_groups);
%% colors
c1 = [231, 76, 60]/255;
c2 = [41, 128, 185]/255;
c3 = [39, 174, 96]/255;
c4 = [244, 208, 63]/255;
c5 = [165, 105, 189]/255;
c6 = [160, 64, 0]/255;
c7 = [93, 109, 126]/255;
c8 = [240,180,180]/255;
c9 = [178, 186, 187]/255;
c10 = [72, 201, 176]/255;

cc = [c1;c2;c3;c4;c5;c6;c7;c8;c9;c10];

%% Plot

FontName='Latin Modern Roman';
AxisFontName='Latin Modern Roman';
lgsz = 6;
ImageDPI=800;
ImageSizeX=12;
ImageSizeY=6;
ImageFontSize=8;

for i = 1:5
    
    if i == 1
             f=figure('Name','Figure 3: Forecast Error Variance Decomposition of the Output Gap','NumberTitle','off');
    elseif i == 2
             f=figure('Name','Figure 4: Forecast Error Variance Decomposition of Tradable Inflation','NumberTitle','off');
    elseif i == 3
             f=figure('Name','Figure 5: Forecast Error Variance Decomposition of Non-Tradable Inflation','NumberTitle','off');
    elseif i == 4
             f=figure('Name','Figure 6: Forecast Error Variance Decomposition of the MPR','NumberTitle','off');
    elseif i == 5
             f=figure('Name','Figure 7: Forecast Error Variance Decomposition of the RER','NumberTitle','off');
    else
             f= figure(i)
    end
    
    clf;
    this_fevd = squeeze(fevd_new(i,:,:));
    h = area(this_fevd);
    ylim([0 1]);
    xlim([1 12]);
    for j=1:n
        h(j).FaceColor = cc(j,:);
    end
    l = legend(shocks,'Location','southoutside','Orientation','horizontal');
    l.NumColumns = 5;
    
    set(gca,'FontName',AxisFontName,'FontSize',ImageFontSize,'FontWeight','bold')
    l.FontSize = lgsz;
    
    set(gcf,'PaperUnits','centimeters','PaperPosition',[0 0 ImageSizeX ImageSizeY]);
    l.FontSize = lgsz;
    print('-dpng', strcat('fig_',names{i}, '.png') , strcat('-r',num2str(ImageDPI)));
    fprintf([names{i} '\n'])
    
end



%%