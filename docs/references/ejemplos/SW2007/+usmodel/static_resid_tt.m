function T = static_resid_tt(T, y, x, params)
% function T = static_resid_tt(T, y, x, params)
%
% File created by Dynare Preprocessor from .mod file
%
% Inputs:
%   T         [#temp variables by 1]  double   vector of temporary terms to be filled by function
%   y         [M_.endo_nbr by 1]      double   vector of endogenous variables in declaration order
%   x         [M_.exo_nbr by 1]       double   vector of exogenous variables in declaration order
%   params    [M_.param_nbr by 1]     double   vector of parameter values in declaration order
%
% Output:
%   T         [#temp variables by 1]  double   vector of temporary terms
%

assert(length(T) >= 11);

T(1) = 1/(params(10)/(1-params(10)));
T(2) = 1/(1+params(44)*params(42));
T(3) = params(42)^2;
T(4) = T(3)*params(12);
T(5) = params(15)/params(42);
T(6) = (1-T(5))/(params(14)*(1+T(5)));
T(7) = (1-params(13))/(params(47)+1-params(13));
T(8) = 1/(1+params(44)*params(42)*params(21));
T(9) = (1-params(22))*(1-params(44)*params(42)*params(22))/params(22)/(1+(params(18)-1)*params(3));
T(10) = params(44)*params(42)/(1+params(44)*params(42));
T(11) = (1-params(20))*(1-params(44)*params(42)*params(20))/((1+params(44)*params(42))*params(20))*1/(1+(params(24)-1)*params(1));

end
