%Endogenous Variables
var	 dYnomin d_Ypot G d_Y_anual ynomin ;

%CPI
    % SAE and Core CPI
    var inflIPC inflIPC4 inflsae inflsae_core inflsae_core_nt inflsae_core_t inflsae_resto; 
    var inflsae_core_anual inflsaeanual;

    %Food and Energy CPI
    var infle infla;

%Labor Market
var  Ubar u U gUbar Ubar_total zu;

%Domestic Financial Variables
var i in rlp bcu5 bcu10 rn r i_desv ;

%Exchange rate variables
var rer deus drerus deusrm de drer ;

%Foreing Variables
    %Foreing Demand
    var  yx_avan yx_emer; 
    %Foreing Financial Variables
    var iUSTbill90 rUSTbill90 inflCPIUS;  
    %Foreing inflation    
    var inflIPE inflnoUS embi_ch sum_inflUS;

%ToT variables
    var tdi pcu pmoil  px px_pcu px_pnpcu  pm pm_oil pm_pnoil ;
    var dtdi dpx dpx_pcu dpx_pnpcu dpm dpm_oil dpm_pnoil;
    var tdi_fun px_fun pm_fun px_pcu_fun px_pnpcu_fun pm_oil_fun pm_pnoil_fun;
    var  delta_i delta_i_ext rer_gap rer_pot drer_gap;
%MEPCO
     var  d_pmoil_mepco;
%%
%% Endogenous Shocks (AR (1) Shocks)
%Demand Shocks
var zynomin ;
%Cost Push Shocks
var zinfle zinfla zinflsae_core_nt zinflsae_core_t zinflsae_resto;
% Monetary Shocks
var   zi zrn zrlp ;
% UIP Shocks
var zdeus  zdeusrm ;
% Foreing Shocks
     %Foreing Demand
     var zyx_emer zyx_avan; 
     %Foreing Financial Variables
     var ziUSTbill90;
     %Foreing inflation   
     var zembi_ch zinflCPIUS  zinflnoUS; 
  
% ToT Shocks   
var  zpx_pnpcu zpm_pnoil  zpmoil;
  

%%
%% Anual quarterly equivalences
var GROWTH_EY0 GROWTH_EY1 GROWTH_EY2 GROWTH_EY1LR GROWTH_EY2LR GROWTH_EY3LR GROWTH_EY4LR 
    GROWTH_EY5LR GROWTH_EY6TO10LR PIE_EY0 PIE_EY1 ;

%% Others
var inflsae_2 Alimentos Energia IPC;

%%
%% Shocks IID - Variables Exogenas      
%%

 %Output Shocks
 varexo zzd_Ypot zzG zzynomin ;

 %Cost Push Shocks
 varexo zzinfla zzinfle zzsae_core_nt zzsae_core_nt_s zzsae_core_t zzsae_core_t_s zzsae_resto zzsae_resto_s ;
 
 %Approximation Shocks
 varexo zzIPCSAE zzIPCSAEcore zzinflIPC ;  

 %Labor Shocks  
varexo zzUbar zzgUbar zzu;  

 %Monetary Shocks   
varexo zzi zzrlp zzrn;

%UIP Shocks
varexo zzdeus zzdeusrm ;

%Foreing Shocks
    %Foreing Demanda
    varexo zzyx_emer zzyx_avan; 
    %Foreing Financial Variables
    varexo zziUSTbill90; 
    %Foreing inflation   
    varexo zzinflCPIUS zzinflIPE zzembi_ch;

%ToT Shocks
varexo  zzpcu zzpmoil zzpx zzpx_pcu zzpx_pnpcu zzpm zzpm_oil zzpm_pnoil;

%MEPCO Shock
varexo  zzmepco;
%%
%% Parametrization - Names

%IS Parameters
parameters	 a7 a6 a5 a4 a3 a2 a1;

%CPI Parameters
parameters share_core_nt share_core_t share_core share_sae share_a share_e inftarget;
    
%Phillips Curve Parameters
parameters	bnt1 bnt2 bnt3 bnt4 bnt5 rho_zinflsae_core_nt; 
parameters	bt1 bt2 bt3 bt4 bt5 bt_ec rho_zinflsae_core_t ;
parameters	rho_inflsae_resto rho_zinflsae_resto ;
    
%STD Scale Parameters
parameters std_inflsae_core_nt std_inflsae_core_nt_s std_inflsae_core_t std_inflsae_core_t_s std_inflsae_resto std_inflsae_resto_s ;   
parameters std_inflsae_core std_inflsae std_inflIPC;

%CPI Parameters
parameters rho_infla ;

%Taylor Rule Parameters
parameters c3 c2 c1 ;

%Foreing Parameters
    %Foreing Demand
    parameters rho1_yx_emer rho1_yx_avan; 
    %Foreing Financial and Inflation parameters
    parameters rho1_embi_ch rho1_inflCPIUS rho1_deusrm ;

%Shocks persistance parameters
parameters rhoyresto rhoi   rhozinfla rhozinfle rhorlp  rhozyx_emer  rhozyx_avan rhodeus;
parameters rhozdeusrm rho1_iUSTbill90 rhoziUSTbill90  rhozinflCPIUS rho1_inflnoUS rhozinflnoUS rhozembi_ch;


%ToT Parameters   
parameters  ec moil rho_pcu rho1_pmoil rho2_pmoil rhozpmoil ;
parameters  rho_zpx_pnpcu rho_zpm_pnoil;
parameters std_pcu std_pmoil std_px std_px_pcu std_px_pnpcu std_zpx_pnpcu std_pm std_pm_oil std_pm_pnoil std_zpm_pnoil;

  
%Labor Parameters
parameters tau4  tau3 tau2 tau1 rhozu;
parameters std_Ubar std_gUbar std_u;
parameters landa_1 landa_2;

%Long-Run Parameters 
parameters theta_G growth_ss Uss crnpot;

%Others Parameters
parameters cc1 e1 pie1  f1 ;

%STD Scale Parameters
parameters std_infla std_infle std_yxemer std_yxavan std_iUSTbill90 std_embi std_inflCPIUS std_inflIPE;

%UIP Parameter
parameters tita;
%MEPCO Parameter
parameters  std_mepco;

%Food CPI Parameters
parameters gap_infla;
%Volatile CPI Parameters
parameters br1 br2;

%%
%% Parametrization - Values

%IS Parameters
 a7 = 0.0229379683358625;
 a6 = 0.0189224894696350;
 a5 = 0.0876166213223136;
 a4 = 0.0268640844193142;
 a3 = 0.0600756805588971;
 a2 = 0.0649989201905854;
 a1 = 0.113847594203229;
 rhoyresto = 0.410188404158809;

%Taylor Rule Parameters
 c3 =0.232720721727646;
 c2 =1.60458792508645;
 c1 =0.744380121342180;
 rhoi =0;
 
%Long-Run Parameters 
 theta_G =0.07;
 growth_ss =0.00825;
 Uss = 0.081; 
 
%Labor Parameters
tau4 =0.1;
tau3 =0.1;
tau1= 0.027;
tau2= 0.503;
rhozu=0;
     
landa_1=1;
landa_2=0.8/0.3;    
std_Ubar=1;
std_gUbar=1;
std_u=1;
 

%CPI Parameters
rho_infla =0.626651;
rhozinfla =0;
pie1 =0.5;
rhozinfle =0;
 
 
%CPI Parameters
    share_core_nt = 0.3816159;
    share_core_t = 0.1311754;
    share_core = 0.5127913;
    share_sae = 0.73158220;
    share_a = 0.19301310000;
    share_e = 0.07540470000;
    
%Phillips Curve Parameters
   
      %Non Tradable PC
            bnt1=0.2*1; %Foward Loking Expectation
            bnt2=0.5; %Back Loking Indexation
            bnt3=0.1; %Output Gap Pressure
            bnt4=0.3; %Salaries Push
            bnt5=0; %Error Correction
            rho_zinflsae_core_nt=0.3;

      %Tradable PC
            bt1=0.1*0; %Foward Loking Expectation
            bt2=0.5; %Back Loking Indexation
            bt3=0.1; %Output Gap Pressure
            bt4=0.05; %Error Correction
            bt5=0.03; %Error Correction
            bt_ec=0.03;
            rho_zinflsae_core_t=0;

       %Volatile CPIC
            br1=0.1;
            br2=0.5*0.02;
            rho_inflsae_resto=0.3;
            rho_zinflsae_resto=0.1;
            
            
        

%STD Scale Parameters 
std_inflsae_core_nt=1;
std_inflsae_core_nt_s=1;
std_inflsae_core_t=1;
std_inflsae_core_t_s=1;
std_inflsae_resto=1;
std_inflsae_resto_s=1; 
std_inflsae_core=1;
std_inflsae=1;
std_inflIPC=1;

        
%Others Parameters 
 cc1 =0.875;
 
 %UIP
 e1 =0;
 rhorlp =0.4125;
 
%Long-Run Parameters 
 
 crnpot =(1/3.3)*4;
 inftarget =0.03;
 
 %Persistencias
 %UIP Parameter
  tita = 0.35;
  
 %Shocks persistance parameters 
 rhodeus = 0.740455375151389; 
 rho1_deusrm =0.3262305975522828;
 rhozdeusrm =0;
 rho1_yx_emer =0.969;
 rhozyx_emer =0;
 rho1_yx_avan =0.956;
 rhozyx_avan =0;
 
%Foreing Parameters
 rho1_iUSTbill90 = 0.884827689520846;% //  0.75;  %Calibracion XMAS Search
 rhoziUSTbill90 =0;
 rho1_embi_ch =0.72;
 rho1_inflCPIUS =0.205;
 rhozinflCPIUS =0;
 rho1_inflnoUS =0.444817;
 rhozinflnoUS =0;
 f1 =0.2232;
 rhozembi_ch =0;
 
  %ToT Parameters   
  std_pcu=1;
  std_pmoil=1;
  std_px=1;
  std_px_pcu=1;
  std_px_pnpcu=1;
  std_zpx_pnpcu=1;
  std_pm=1;
  std_pm_oil=1;
  std_pm_pnoil=1;
  std_zpm_pnoil=1;

  ec=0.4;
  moil=0.1;
  rho_pcu=0.5;
  rho2_pmoil =0;
  rho1_pmoil =0.63;
  rhozpmoil =0;
  rho_zpx_pnpcu=0.5;
  rho_zpm_pnoil=0.5;

     
 %STD Scale Parameters     
 std_infla=1;
 std_infle=1;
 std_yxemer=1;
 std_yxavan=1;
 std_iUSTbill90=1;
 std_embi=1;
 std_inflCPIUS=1;
 std_inflIPE=1;
 std_mepco=1;
 
 %Food CPI Parameters
 gap_infla =0.3;
 
%%
%% MODEL
 model(linear);
// Equation #1 IS

ynomin - ynomin(-1) = -a1*(ynomin(-1) + ynomin(-2)) -a2*(ynomin(-1) -ynomin(-2)) -a3*(r + r(-1) - rn - rn(-1)) + a4*(yx_emer +yx_emer(-1)) +a5*(yx_avan + yx_avan(-1)) + a6*(rer(-1)) +a7*tdi +zynomin;

// Equation #2 
zynomin =rhoyresto*(zynomin(-1)) +zzynomin;

    
// Equation #3 - Non Tradable PC 
inflsae_core_nt = bnt1*inflsae_core_nt(+1) + bnt2*(inflsae_core_nt(-1) - std_inflsae_core_nt_s*zzsae_core_nt_s(-1)) + bnt3*ynomin +  std_inflsae_core_nt_s*zzsae_core_nt_s + zinflsae_core_nt;

// Equation #4 
zinflsae_core_nt = rho_zinflsae_core_nt*zinflsae_core_nt(-1) + std_inflsae_core_nt*zzsae_core_nt;

// Equation #5 - Tradable PC 
inflsae_core_t = bt1*inflsae_core_t(+1) + bt2*(inflsae_core_t(-1) - std_inflsae_core_t_s*zzsae_core_t_s(-1)) + 
                 bt4*((drer + inflIPC-inflIPE)+ (drer(-1) + inflIPC(-1)- inflIPE(-1))) 
                 + bt3*ynomin +bt5*rer(-1) +  zinflsae_core_t + std_inflsae_core_t_s*zzsae_core_t_s ;

// Equation #6 - Tradable PC             
zinflsae_core_t = rho_zinflsae_core_t*zinflsae_core_t(-1) + std_inflsae_core_t*zzsae_core_t ;

// Equation #7 - Volatile CPI             
 inflsae_resto = rho_inflsae_resto*(inflsae_resto(-1) - std_inflsae_resto_s*zzsae_resto_s(-1)) 
            + br1*(drer + inflIPC-inflIPE) 
            + br2*(rer(-1))         
            + zinflsae_resto + std_inflsae_resto_s*zzsae_resto_s;

// Equation #8             
zinflsae_resto = rho_zinflsae_resto*zinflsae_resto(-1)+  std_inflsae_resto*zzsae_resto;

// Equation #9 - Core CPI agregation             
inflsae_core = (share_core_nt*inflsae_core_nt + share_core_t*inflsae_core_t)/share_core + std_inflsae_core*zzIPCSAEcore ;

// Equation #10 - Non Food and Energy CPI agregation             
inflsae = (share_core*inflsae_core + (share_sae-share_core)*inflsae_resto)/share_sae + std_inflsae*zzIPCSAE ;

// Equation #11 - CPI agregation             
 inflIPC = share_sae*inflsae + share_a*infla + share_e*infle + std_inflIPC*zzinflIPC;

// Equation #12 - Annual Core CPI              
inflsae_core_anual = inflsae_core + inflsae_core(-1) + inflsae_core(-2) + inflsae_core(-3);

// Equation #13 - Annual Non Food and Energy CPI              
inflsaeanual =inflsae +inflsae(-1) +inflsae(-2) +inflsae(-3);

// Equation #14 Taylor Rule
 i - in = c1*(i(-1) - in(-1)) +(1-c1)*(c2*(inflsaeanual(+1)) +c3*ynomin) +zi;
                 
// Equation #15 
zi =rhoi*(zi(-1)) + zzi;

// Equation #16 - Growth decomposition
ynomin -ynomin(-1) = dYnomin - d_Ypot;

// Equation #17 - Potencial Growth 
d_Ypot =G +zzd_Ypot;

// Equation #17  - Potencial Growth
G =theta_G*growth_ss+(1-theta_G)*(G(-1)) +zzG;

// Equation #18 - Annual Growth
d_Y_anual =dYnomin +dYnomin(-1) +dYnomin(-2) +dYnomin(-3);

// Equation #19 - Unemployment
U =u +Ubar;

// Equation #20 - NAIRU 
Ubar =tau4*Uss+(1-tau4)*(Ubar(-1)) +gUbar +std_Ubar*landa_1*zzUbar;

// Equation #21 - NAIRU growth
gUbar =(1-tau3)*(gUbar(-1)) + std_Ubar*landa_1*zzgUbar;

// Equation #22 - Okun Law
u = tau2*u(-1)-tau1*ynomin + zu;

// Equation #23
zu = rhozu*zu(-1) + std_Ubar*landa_2*zzu;

// Equation #30 - Food Inflation
infla =rho_infla*(infla(-1)) + gap_infla*ynomin +zinfla;

// Equation #31 
zinfla =rhozinfla*(zinfla(-1)) + std_infla*zzinfla;

// Equation #32 - MEPCO
d_pmoil_mepco = 0.7*0.43*d_pmoil_mepco(-1) + (1-0.7)*( (drer +inflIPC -inflIPE) + inflIPE + pmoil -pmoil(-1))+std_mepco*zzmepco;

// Equation #33 - Energy Inflation
infle =(5.268090*d_pmoil_mepco + 2.272380*zinfle)/7.540470;

// Equation #34 
zinfle =rhozinfle*(zinfle(-1)) +std_infle*zzinfle;

// Equation #35 - Annual CPI 
inflIPC4 =inflIPC +inflIPC(-1) +inflIPC(-2) +inflIPC(-3);

// Equation #36 - Real rate definition
r - rn = i - in -4*(inflIPC(1));

// Equation #37 - Foward  Equation
rlp =cc1*(rlp(1)) +(1-cc1)*(r -rn) +zrlp;

// Equation #39  - bcu5 Equation
bcu5 =cc1*(bcu5(1)) +(1-cc1)*(r -rn);

// Equation #40 - bcu10 Equation
bcu10 =cc1*(bcu10(1)) +(1-cc1)*(r -rn);

// Equation #41 
    delta_i = ((i-in) - (i(-1)-in(-1)))/4;

// Equation #42 
 delta_i_ext = iUSTbill90/4 + embi_ch/4 - (iUSTbill90(-1)/4 + embi_ch(-1)/4);
    
// Equation #43 - UIP 

(i -in)/4 -iUSTbill90/4 -embi_ch/4 =(1-e1)*deus(+1) -e1*deus +zdeus;

// Equation #44 - Real Exchange rate 
rer = rer_gap + rer_pot;

// Equation #45 - Equilibrium Real Exchange rate 
rer_pot = -(i-in)/4 + iUSTbill90/4 + embi_ch/4  - tita*tdi_fun;

// Equation #46 - Change in cycle Real exchange rate 
drer_gap =deus +inflIPE -inflIPC;

// Equation #47 - Cycle Real exchange rate
rer_gap =rer_gap(-1) +drer_gap;

// Equation #48 - Real Exchange rate
rer =rer(-1) +drer;    

// Equation #49 
zrlp =rhorlp*(zrlp(-1)) +zzrlp;

// Equation #50 - Real Neutral Interest Rate 
rn =crnpot*(d_Ypot(1)) +zrn;

// Equation #51 
zrn =0*(zrn(-1)) +zzrn;

// Equation #52 - Nominal Neutral Interest Rate
in =rn +inftarget;

// Equation #53 
i_desv =i -in;

// Equation #54 - Dollar/Clp Depreciation 
drerus =deus +inflCPIUS -inflIPC;

// Equation #55 
de =deus +deusrm;

// Equation #56 - Real Foreing Interet Rate
rUSTbill90 =iUSTbill90 -4*(inflCPIUS(1));

// Equation #57- UIP Shock 
zdeus =rhodeus*(zdeus(-1)) +zzdeus;

// Equation #58 
deusrm =rho1_deusrm*(deusrm(-1)) +zdeusrm;

// Equation #59 
zdeusrm =rhozdeusrm*(zdeusrm(-1)) +zzdeusrm;

// Equation #60 - Foreing Demand: E 
yx_emer =rho1_yx_emer*(yx_emer(-1)) +zyx_emer;

// Equation #61 
zyx_emer =rhozyx_emer*(zyx_emer(-1)) +std_yxemer*zzyx_emer;

// Equation #62 - Foreing Demand: A
yx_avan =rho1_yx_avan*(yx_avan(-1)) +zyx_avan;

// Equation #63 
zyx_avan =rhozyx_avan*(zyx_avan(-1)) +std_yxavan*zzyx_avan;

// Equation #64 - Foreing Interest Rate
iUSTbill90 =rho1_iUSTbill90*(iUSTbill90(-1)) +ziUSTbill90;

// Equation #65 
ziUSTbill90 =rhoziUSTbill90*(ziUSTbill90(-1)) +std_iUSTbill90*zziUSTbill90;

// Equation #66 - Risk Premium
embi_ch =rho1_embi_ch*(embi_ch(-1)) +zembi_ch;

// Equation #67 - US CPI
inflCPIUS =rho1_inflCPIUS*(inflCPIUS(-1)) +zinflCPIUS;

// Equation #68 
zinflCPIUS =rhozinflCPIUS*(zinflCPIUS(-1)) +std_inflCPIUS*zzinflCPIUS;

// Equation #69 - Non US CPI
inflnoUS =rho1_inflnoUS*(inflnoUS(-1)) +zinflnoUS;

// Equation #70 
zinflnoUS =rhozinflnoUS*(zinflnoUS(-1)) +std_inflIPE*zzinflIPE;

// Equation #71 
zembi_ch =rhozembi_ch*zembi_ch +std_embi*zzembi_ch;

// Equation #72 - ToT definition 
tdi = px - pm;  

// Equation #73 - Fundamental ToT definition    
tdi_fun = px_fun - pm_fun;

// Equation #74 - Fundamental Export Prices    
px_fun = ec*px_pcu_fun + (1-ec)*px_pnpcu_fun;

// Equation #75 - Fundamental Import Prices    
pm_fun = moil*pm_oil_fun + (1-moil)*pm_pnoil_fun;

// Equation #76 - Fundamental Copper Export prices    
px_pcu_fun=pcu;

// Equation #77 - Fundamental Non-Copper Export prices    
px_pnpcu_fun=zpx_pnpcu;

// Equation #78 - Fundamental Oil Import prices    
pm_oil_fun=pmoil;

// Equation #79 - Fundamental Non-Oil Import prices    
pm_pnoil_fun=zpm_pnoil;
    
// Equation #80 - Export Prices    
px = ec*px_pcu + (1-ec)*px_pnpcu + std_px*zzpx;

// Equation #81 - Copper Export Prices    
px_pcu = pcu + std_px_pcu*zzpx_pcu;

// Equation #82 - Non-Copper Export Prices    
px_pnpcu = zpx_pnpcu;

// Equation #83    
zpx_pnpcu=rho_zpx_pnpcu*zpx_pnpcu(-1) + std_zpx_pnpcu*zzpx_pnpcu;

// Equation #84 - Import Prices        
pm = moil*pm_oil + (1-moil)*pm_pnoil + std_pm*zzpm;

// Equation #85 - Oil Import Prices        
pm_oil = pmoil + std_pm_oil*zzpm_oil;

// Equation #86 - Non-Oil Import Prices        
pm_pnoil = zpm_pnoil;

// Equation #87        
zpm_pnoil=rho_zpm_pnoil*zpm_pnoil(-1) + std_zpm_pnoil*zzpm_pnoil;

// Equation #88 - Copper Price        
pcu =rho_pcu*pcu(-1) +std_pcu*zzpcu;

// Equation #89 - Oil Price        
pmoil =rho1_pmoil*(pmoil(-1)) +rho2_pmoil*(pmoil(-2)) +zpmoil;

// Equation #90         
zpmoil =rhozpmoil*(zpmoil(-1)) +std_pmoil*zzpmoil;
    
// Equation #91       
dtdi = tdi - tdi(-1);   

// Equation #92       
dpx = px - px(-1);

// Equation #93       
dpx_pcu = px_pcu - px_pcu(-1) ;

// Equation #94       
dpx_pnpcu=px_pnpcu - px_pnpcu(-1);

// Equation #95       
dpm=pm - pm(-1) ;

// Equation #95       
dpm_oil =pm_oil - pm_oil(-1)  ;

// Equation #96       
dpm_pnoil= pm_pnoil - pm_pnoil(1) ;

// Equation #97 - Foreing Inflation       
inflIPE =f1*inflCPIUS +(1-f1)*inflnoUS;
    
// Equation #98 - Annual Growth       
GROWTH_EY0 =(dYnomin(3) +2*(dYnomin(2)) +3*(dYnomin(1)) +4*(dYnomin(0)) +3*(dYnomin(-1)) +2*(dYnomin(-2)) +dYnomin(-6))/4;

// Equation #99 - Annual Growth (+1)
GROWTH_EY1 =(dYnomin(7) +2*(dYnomin(6)) +3*(dYnomin(5)) +4*(dYnomin(4)) +3*(dYnomin(3)) +2*(dYnomin(2)) +dYnomin(-2))/4;

// Equation #100 - Annual Growth (+2)
GROWTH_EY2 =(dYnomin(11) +2*(dYnomin(10)) +3*(dYnomin(9)) +4*(dYnomin(8)) +3*(dYnomin(7)) +2*(dYnomin(6)) +dYnomin(2))/4;

// Equation #101 - Annual Growth (+1)
GROWTH_EY1LR =(dYnomin(5) +2*(dYnomin(4)) +3*(dYnomin(3)) +4*(dYnomin(2)) +3*(dYnomin(1)) +2*(dYnomin(0)) +dYnomin(-1))/4;

// Equation #102 - Annual Growth (+2)
GROWTH_EY2LR =(dYnomin(9) +2*(dYnomin(8)) +3*(dYnomin(7)) +4*(dYnomin(6)) +3*(dYnomin(5)) +2*(dYnomin(4)) +dYnomin(3))/4;

// Equation #103 - Annual Growth (+3)
GROWTH_EY3LR =(dYnomin(13) +2*(dYnomin(12)) +3*(dYnomin(11)) +4*(dYnomin(10)) +3*(dYnomin(9)) +2*(dYnomin(8)) +dYnomin(7))/4;

// Equation #104 - Annual Growth (+4)
GROWTH_EY4LR =(dYnomin(17) +2*(dYnomin(16)) +3*(dYnomin(15)) +4*(dYnomin(14)) +3*(dYnomin(13)) +2*(dYnomin(12)) +dYnomin(11))/4;

// Equation #105 - Annual Growth (+5)
GROWTH_EY5LR =(dYnomin(21) +2*(dYnomin(20)) +3*(dYnomin(19)) +4*(dYnomin(18)) +3*(dYnomin(17)) +2*(dYnomin(16)) +dYnomin(15))/4;

// Equation #106 - Annual Growth (+6)
GROWTH_EY6TO10LR =((dYnomin(25) +2*(dYnomin(24)) +3*(dYnomin(23)) +4*(dYnomin(22)) +3*(dYnomin(21)) +2*(dYnomin(20)) +dYnomin(19))/4 +(dYnomin(29) +2*(dYnomin(28)) +3*(dYnomin(27)) +4*(dYnomin(26)) +3*(dYnomin(25)) +2*(dYnomin(24)) +dYnomin(23))/4 +(dYnomin(33) +2*(dYnomin(32)) +3*(dYnomin(31)) +4*(dYnomin(30)) +3*(dYnomin(29)) +2*(dYnomin(28)) +dYnomin(27))/4 +(dYnomin(37) +2*(dYnomin(36)) +3*(dYnomin(35)) +4*(dYnomin(34)) +3*(dYnomin(33)) +2*(dYnomin(32)) +dYnomin(31))/4 +(dYnomin(41) +2*(dYnomin(40)) +3*(dYnomin(39)) +4*(dYnomin(38)) +3*(dYnomin(37)) +2*(dYnomin(36)) +dYnomin(35))/4)/5;

// Equation #107 - Annual CPI
PIE_EY0 =inflIPC +inflIPC(1) +inflIPC(2) +inflIPC(3);

// Equation #108 - Annual CPI
PIE_EY1 =inflIPC(4) +inflIPC(5) +inflIPC(6) +inflIPC(7);

// Equation #109 - 
Ubar = Ubar_total;

// Equation #110 -
inflsae_2=inflsae;

// Equation #111 - 
Alimentos = infla;

// Equation #112 -
Energia =infle;

// Equation #113 -
IPC=inflIPC;

// Equation #114 
sum_inflUS=inflCPIUS + inflCPIUS(-1) +inflCPIUS(-2) +inflCPIUS(-4);

end;

shocks;
          

var	zzynomin	;	stderr 0.007;      
%Cost Push Shocks    
 var	zzsae_core_nt	;	stderr 0.007;
 var	zzsae_core_nt_s	;	stderr 0.007;
 var	zzsae_core_t	;	stderr 0.007;
 var	zzsae_core_t_s	;	stderr 0.007;
 var	zzsae_resto	;	stderr 0.007;
 var	zzsae_resto_s	;	stderr 0.007;
 
%Approximation Shocks
 var	zzIPCSAE	;	stderr 0.007;
 var	zzIPCSAEcore	;	stderr 0.007;
 var	zzinflIPC	;	stderr 0.007;
    
%Monetary Shocks
var	zzi	;	stderr 0.00671569113892264;

%Output Shocks
var	zzd_Ypot	;	stderr 0.007*(13/82.5); %FMV-X Ratio Calibration
var	zzG	;	stderr 0.007*(13/82.5);%FMV-X Ratio Calibration

%Labor Shocks  
var	zzUbar	;	stderr 0.007; %FMV-X Ratio Calibration
var	zzgUbar	;	stderr 1; %FMV-X Ratio Calibration
var	zzu	;	stderr 1;  %FMV-X Ratio Calibration

var	zzinfla	;	stderr 0.007;
var	zzinfle	;	stderr 0.007;

 %UIP Shocks 
var	zzrlp	;	stderr 0.00369064299293808;
var	zzrn	;	stderr 0.1/100;
var	zzdeus	;	stderr 0.00867829180755364;
var	zzdeusrm	;	stderr 0.0160444294872015;

%Foreing Shocks
var	zzyx_emer	;	stderr 0.007;
var	zzyx_avan	;	stderr 0.007;
var	zziUSTbill90	;	stderr 0.007;
var	zzinflCPIUS	;	stderr 0.007;
var	zzinflIPE	;	stderr 0.007;
var	zzembi_ch	;	stderr 0.007;

%ToT Shocks
var	zzpcu	;	stderr 0.007;
var	zzpmoil	;	stderr 0.007;
var	zzpx	;	stderr 0.007;
var	zzpx_pcu	;	stderr 0.007;
var	zzpx_pnpcu	;	stderr 0.007;
var	zzpm	;	stderr 0.007;
var	zzpm_oil	;	stderr 0.007;
var	zzpm_pnoil	;	stderr 0.007;
%MEPCO Shock 
var	zzmepco	;	stderr 0.007;

end;

initval;
                      
tdi=0;
pcu=0;
pmoil=0;
zpmoil=0;
px=0;
px_pcu=0;
px_pnpcu=0;
zpx_pnpcu=0;
pm=0;
pm_oil=0;
pm_pnoil=0;
zpm_pnoil=0;
dtdi=0;
dpx=0;
dpx_pcu=0;
dpx_pnpcu=0;
dpm=0;
dpm_oil=0;
dpm_pnoil=0;

rer=0;
yx_avan=0;
yx_emer=0;
rn=crnpot*growth_ss;
r =rn;
ynomin=0;
zynomin=0;

inflIPC=0;
infla=0; 
infle=0;
inflIPC4=0;
zinfla=0;
zinfle=0;
inflsae=0;
inflsae_core=0;
inflsae_core_nt=0;
inflsae_core_t=0;
inflsae_resto=0;
inflsae_core_anual=0;
inflsaeanual=0;

deus=0;
in=rn+0.03;
i=in; 
zi=0; 
d_Ypot=growth_ss;
dYnomin =growth_ss;
G=growth_ss;
d_Y_anual=4*growth_ss;

Ubar=Uss;
u=0;
U=Uss;
gUbar=0;
Ubar_total =Ubar;
zu=0;

rlp=0;
zrlp=0;
bcu5=0;
bcu10=0;
zdeus=0;
embi_ch=0;
iUSTbill90=0;
zrn=0;
i_desv=0;
inflCPIUS=0;
drerus =0;
deusrm=0;
de=0;
inflIPE=0;
drer=0;
rUSTbill90=0;
zdeusrm =0;
zyx_emer=0;
zyx_avan=0;
ziUSTbill90=0;
zembi_ch=0;
zinflCPIUS=0;
inflnoUS=0;
zinflnoUS=0;

GROWTH_EY0 = 4*growth_ss      ;
GROWTH_EY1 = 4*growth_ss      ;
GROWTH_EY2 = 4*growth_ss      ;
GROWTH_EY1LR = 4*growth_ss    ;
GROWTH_EY2LR = 4*growth_ss    ;
GROWTH_EY3LR = 4*growth_ss    ;
GROWTH_EY4LR = 4*growth_ss    ;
GROWTH_EY5LR = 4*growth_ss    ;
GROWTH_EY6TO10LR = 4*growth_ss;
PIE_EY0=0;
PIE_EY1=0;
end;

% Estimacion
varobs          dYnomin inflsae i rer yx_emer
                yx_avan embi_ch iUSTbill90  
                U infla infle inflIPC inflIPE
                
                inflsae_core inflsae_core_nt inflsae_core_t inflsae_resto 
                
                
                               
                pmoil pcu dpx dpx_pcu dpx_pnpcu dpm dpm_oil pm_pnoil 
                 
                ynomin  ; 


estimated_params;
%IS Parameters
a1      	,	beta_pdf	,	0.15	,	0.04	;
a2      	,	beta_pdf	,	0.05	,	0.03	;
a3      	,	beta_pdf	,	0.07	,	0.02	;
a4      	,	beta_pdf	,	0.07	,	0.02	; %SS.CC STATA Emergentes parece tener mas impacto sobre la brecha
a5      	,	beta_pdf	,	0.06	,	0.02	; %SS.CC STATA Dejamos Prios Iguales
a6      	,	beta_pdf	,	0.01	,	0.005	;
a7      	,	beta_pdf	,	0.04	,	0.02	;

rhoyresto      ,   beta_pdf, 0.40, 0.10             ;
  
%Non Tradable PC Parameters
   
bnt1      	,	beta_pdf	,	0.2	,	0.05	; %Foward Looking STATA 
bnt2      	,	beta_pdf	,	0.5	,	0.15	; %Indexation STATA
bnt3      	,	beta_pdf	,	0.1	,	0.05/2	; %MC Pressueres STATA

rho_zinflsae_core_nt ,   beta_pdf, 0.20, 0.10             ;  %persistence stata low

%Tradable PC Parameters
bt2      	,	beta_pdf	,	0.7	,	0.15/2	; %Indexation STATA
bt3      	,	beta_pdf	,	0.02	,	0.01/2	; %ynomin with rer level in CP
bt4      	,	beta_pdf	,	0.05	,	0.01	; %dRER
bt5      	,	beta_pdf	,	0.02	,	0.01/2	; %deus 
            
              
%Volatile CPI Parameters
      
br1      	,	beta_pdf	,	0.1	,	0.025	;    
br2      	,	beta_pdf	,	0.05	,	0.01	;       
rho_inflsae_resto      	,	beta_pdf	,	0.5	,	0.18	; %Foward Looking      
rho_zinflsae_resto    	,	beta_pdf	,	0.25	,	0.18	; %Foward Looking

       
%Volatile CPI Parameters
    
stderr 	zzsae_core_nt 	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzsae_core_nt_s 	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzsae_core_t 	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzsae_core_t_s 	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzsae_resto 	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzsae_resto_s 	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzIPCSAE 	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzIPCSAEcore 	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzinflIPC 	,	inv_gamma_pdf	,	0.007	,	inf;
                         
  
   
%Labour Market std Parameters
std_Ubar     	,	inv_gamma_pdf	,	0.007	,	inf	;
stderr 	zzUbar 	,	inv_gamma_pdf	,	0.007	,	inf;
          
     

%Taylor Rule Parameters
c3      	,   gamma_pdf  ,   0.2    ,   0.05   	 ;
c2      	,	normal_pdf	,	1.7	,	0.1			 ;
c1      	,	beta_pdf	,	0.80	,	0.05	 ;



% Standard Deviations
stderr 	zzynomin 	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzi      	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzdeus     	,	inv_gamma_pdf	,	0.008	,	inf;
stderr 	zzinfla     	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzinfle     	,	inv_gamma_pdf	,	0.007	,	inf;


%Foreing Output Gap
rho1_yx_emer      	,	beta_pdf	,	0.85	,	0.1	; %AR1 Process
stderr 	zzyx_emer     	,	inv_gamma_pdf	,	0.007	,	inf;
rho1_yx_avan      	,	beta_pdf	,	0.85	,	0.1	; %AR1 Process
stderr 	zzyx_avan     	,	inv_gamma_pdf	,	0.007	,	inf;

%Foreing Finacial Variables

stderr 	zziUSTbill90     	,	inv_gamma_pdf	,	0.007	,	inf;
rho1_embi_ch      	,	beta_pdf	,	0.7	,	0.1	; %AR1 Process
stderr 	zzembi_ch     	,	inv_gamma_pdf	,	0.007	,	inf;

%Foreing Inflation
rho1_inflnoUS      	,	beta_pdf	,	0.25	,	0.18	; %AR1 Process
rho1_inflCPIUS      ,	beta_pdf	,	0.25	,	0.18	; %AR1 Process
    
stderr 	zzinflCPIUS     	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzinflIPE     	,	inv_gamma_pdf	,	0.007	,	inf;

%ToT Parameters    
rho_pcu      	    ,	beta_pdf	,	0.5	,	0.1	; %AR1 Process
rho1_pmoil      	,	beta_pdf	,	0.63	,	0.15	; %AR1 Process
rho_zpx_pnpcu       ,	beta_pdf	,	0.5	,	0.1	;
rho_zpm_pnoil       ,	beta_pdf	,	0.5	,	0.1	;
    
stderr 	zzpcu     	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzpmoil     	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzpx     	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzpx_pcu     	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzpx_pnpcu     	,	inv_gamma_pdf	,	0.007	,	inf;           
stderr 	zzpm     	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzpm_oil     	,	inv_gamma_pdf	,	0.007	,	inf;
stderr 	zzpm_pnoil     	,	inv_gamma_pdf	,	0.007	,	inf;  

%MEPCO Std
stderr 	zzmepco     	,	inv_gamma_pdf	,	0.007	,	inf;

%Food Inflation Parameters
gap_infla ,	beta_pdf	,	0.25	,	0.10	;
rho_infla ,	beta_pdf	,	0.25	,	0.10	;
  
%UIP Parameters
tita ,	beta_pdf	,	0.35	,	0.07	;
rhodeus ,	beta_pdf	,	0.35	,	0.10	;     


end;


resid;
steady;

%Estimation
estimation(datafile=data_nueva_MEP_reducida,mode_file=MSEP_mode,nobs=71,prefilter=0,mh_jscale=0.25,mode_compute=0, tex, mh_replic=0,nodisplay, smoother);
stoch_simul(periods=0, irf=60, order=1);


        