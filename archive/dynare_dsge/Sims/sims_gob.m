var pi x rf i yf y a g r;
varexo ea eg;
parameters sigma chi beta phi zeta psi rhoa rhog phipi gamma;
load param_dnk_reduce;
set_param_value('beta',beta);
set_param_value('sigma',sigma);
set_param_value('chi',chi);
set_param_value('psi',psi);
set_param_value('phi',phi);
set_param_value('zeta',zeta);
set_param_value('rhoa',rhoa);
set_param_value('rhog',rhog);
set_param_value('phipi',phipi);
set_param_value('gamma',gamma);

model(linear);
% Phillips Curve
pi = zeta*gamma*x + beta*pi(+1);

% IS equation
x = x(+1) - ((1-psi)/sigma)*(i - pi(+1) - rf);

% rf
rf = (sigma/(1-psi)) * ((1+chi)*(1-psi)/(chi*(1-psi) + sigma))*(a(+1) - a) -
(sigma/(1-psi)) * (psi*chi*(1-psi)/(chi*(1-psi)+sigma))*(g(+1) - g);

% yf
yf = ( (1+chi)*(1-psi) / (chi*(1-psi)+sigma))*a + (psi*sigma/(chi*(1-psi) + sigma))*g;

% Output gap
x = y - yf;

% Taylor rule
i = phipi*pi;

% Productivity process
a = rhoa*a(-1) + ea;
