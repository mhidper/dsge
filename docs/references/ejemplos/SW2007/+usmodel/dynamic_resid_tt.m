function T = dynamic_resid_tt(T, y, x, params, steady_state, it_)
% function T = dynamic_resid_tt(T, y, x, params, steady_state, it_)
%
% File created by Dynare Preprocessor from .mod file
%
% Inputs:
%   T             [#temp variables by 1]     double  vector of temporary terms to be filled by function
%   y             [#dynamic variables by 1]  double  vector of endogenous variables in the order stored
%                                                    in M_.lead_lag_incidence; see the Manual
%   x             [nperiods by M_.exo_nbr]   double  matrix of exogenous variables (in declaration order)
%                                                    for all simulation periods
%   steady_state  [M_.endo_nbr by 1]         double  vector of steady state values
%   params        [M_.param_nbr by 1]        double  vector of parameter values in declaration order
%   it_           scalar                     double  time period for exogenous variables for which
%                                                    to evaluate the model
%
% Output:
%   T           [#temp variables by 1]       double  vector of temporary terms
%

assert(length(T) >= 14);

T(1) = 1/(params(10)/(1-params(10)));
T(2) = 1/(1+params(44)*params(42));
T(3) = params(42)^2;
T(4) = T(3)*params(12);
T(5) = params(15)/params(42);
T(6) = (1-T(5))/(params(14)*(1+T(5)));
T(7) = (1-params(13))/(params(47)+1-params(13));
T(8) = (params(14)-1)*params(56)/(params(14)*(1+T(5)));
T(9) = 1/(1-T(5));
T(10) = T(5)/(1-T(5));
T(11) = 1/(1+params(44)*params(42)*params(21));
T(12) = (1-params(22))*(1-params(44)*params(42)*params(22))/params(22)/(1+(params(18)-1)*params(3));
T(13) = params(44)*params(42)/(1+params(44)*params(42));
T(14) = (1-params(20))*(1-params(44)*params(42)*params(20))/((1+params(44)*params(42))*params(20))*1/(1+(params(24)-1)*params(1));

end
