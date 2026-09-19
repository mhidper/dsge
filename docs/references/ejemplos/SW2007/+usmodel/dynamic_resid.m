function residual = dynamic_resid(T, y, x, params, steady_state, it_, T_flag)
% function residual = dynamic_resid(T, y, x, params, steady_state, it_, T_flag)
%
% File created by Dynare Preprocessor from .mod file
%
% Inputs:
%   T             [#temp variables by 1]     double   vector of temporary terms to be filled by function
%   y             [#dynamic variables by 1]  double   vector of endogenous variables in the order stored
%                                                     in M_.lead_lag_incidence; see the Manual
%   x             [nperiods by M_.exo_nbr]   double   matrix of exogenous variables (in declaration order)
%                                                     for all simulation periods
%   steady_state  [M_.endo_nbr by 1]         double   vector of steady state values
%   params        [M_.param_nbr by 1]        double   vector of parameter values in declaration order
%   it_           scalar                     double   time period for exogenous variables for which
%                                                     to evaluate the model
%   T_flag        boolean                    boolean  flag saying whether or not to calculate temporary terms
%
% Output:
%   residual
%

if T_flag
    T = usmodel.dynamic_resid_tt(T, y, x, params, steady_state, it_);
end
residual = zeros(40, 1);
lhs = y(52);
rhs = params(9)*y(31)+(1-params(9))*y(38);
residual(1) = lhs - rhs;
lhs = y(30);
rhs = y(31)*T(1);
residual(2) = lhs - rhs;
lhs = y(31);
rhs = y(38)+y(37)-y(32);
residual(3) = lhs - rhs;
lhs = y(32);
rhs = y(30)+y(19);
residual(4) = lhs - rhs;
lhs = y(35);
rhs = T(2)*(y(4)+params(44)*params(42)*y(64)+1/T(4)*y(33))+y(55);
residual(5) = lhs - rhs;
lhs = y(33);
rhs = y(53)*1/T(6)-y(39)+params(47)/(params(47)+1-params(13))*y(61)+T(7)*y(62);
residual(6) = lhs - rhs;
lhs = y(34);
rhs = y(53)+T(5)/(1+T(5))*y(3)+1/(1+T(5))*y(63)+T(8)*(y(37)-y(65))-y(39)*T(6);
residual(7) = lhs - rhs;
lhs = y(36);
rhs = y(34)*params(54)+y(35)*params(53)+y(54)+y(30)*params(55);
residual(8) = lhs - rhs;
lhs = y(36);
rhs = params(18)*(y(52)+params(9)*y(32)+(1-params(9))*y(37));
residual(9) = lhs - rhs;
lhs = y(38);
rhs = y(37)*params(23)+y(34)*T(9)-y(3)*T(10);
residual(10) = lhs - rhs;
lhs = y(59);
rhs = y(19)*(1-params(49))+y(35)*params(49)+y(55)*T(4)*params(49);
residual(11) = lhs - rhs;
lhs = y(40);
rhs = params(9)*y(42)+(1-params(9))*y(50)-y(52);
residual(12) = lhs - rhs;
lhs = y(41);
rhs = T(1)*y(42);
residual(13) = lhs - rhs;
lhs = y(42);
rhs = y(50)+y(48)-y(43);
residual(14) = lhs - rhs;
lhs = y(43);
rhs = y(41)+y(20);
residual(15) = lhs - rhs;
lhs = y(46);
rhs = y(55)+T(2)*(y(7)+params(44)*params(42)*y(69)+1/T(4)*y(44));
residual(16) = lhs - rhs;
lhs = y(44);
rhs = y(53)*1/T(6)+y(71)-y(51)+params(47)/(params(47)+1-params(13))*y(66)+T(7)*y(67);
residual(17) = lhs - rhs;
lhs = y(45);
rhs = y(53)+T(5)/(1+T(5))*y(6)+1/(1+T(5))*y(68)+T(8)*(y(48)-y(70))-T(6)*(y(51)-y(71));
residual(18) = lhs - rhs;
lhs = y(47);
rhs = y(54)+params(54)*y(45)+params(53)*y(46)+params(55)*y(41);
residual(19) = lhs - rhs;
lhs = y(47);
rhs = params(18)*(y(52)+params(9)*y(43)+(1-params(9))*y(48));
residual(20) = lhs - rhs;
lhs = y(49);
rhs = T(11)*(params(44)*params(42)*y(71)+params(21)*y(9)+y(40)*T(12))+y(57);
residual(21) = lhs - rhs;
lhs = y(50);
rhs = T(2)*y(10)+T(13)*y(72)+y(9)*params(19)/(1+params(44)*params(42))-y(49)*(1+params(44)*params(42)*params(19))/(1+params(44)*params(42))+y(71)*T(13)+T(14)*(params(23)*y(48)+T(9)*y(45)-T(10)*y(6)-y(50))+y(58);
residual(22) = lhs - rhs;
lhs = y(51);
rhs = y(49)*params(26)*(1-params(29))+(1-params(29))*params(28)*(y(47)-y(36))+params(27)*(y(47)-y(36)-y(8)+y(5))+params(29)*y(11)+y(56);
residual(23) = lhs - rhs;
lhs = y(52);
rhs = params(30)*y(12)+x(it_, 1);
residual(24) = lhs - rhs;
lhs = y(53);
rhs = params(32)*y(13)+x(it_, 2);
residual(25) = lhs - rhs;
lhs = y(54);
rhs = params(33)*y(14)+x(it_, 3)+x(it_, 1)*params(2);
residual(26) = lhs - rhs;
lhs = y(55);
rhs = params(35)*y(15)+x(it_, 4);
residual(27) = lhs - rhs;
lhs = y(56);
rhs = params(36)*y(16)+x(it_, 5);
residual(28) = lhs - rhs;
lhs = y(57);
rhs = params(37)*y(17)+y(29)-params(8)*y(2);
residual(29) = lhs - rhs;
lhs = y(29);
rhs = x(it_, 6);
residual(30) = lhs - rhs;
lhs = y(58);
rhs = params(38)*y(18)+y(28)-params(7)*y(1);
residual(31) = lhs - rhs;
lhs = y(28);
rhs = x(it_, 7);
residual(32) = lhs - rhs;
lhs = y(60);
rhs = (1-params(49))*y(20)+params(49)*y(46)+y(55)*params(12)*T(3)*params(49);
residual(33) = lhs - rhs;
lhs = y(24);
rhs = y(47)-y(8)+params(39);
residual(34) = lhs - rhs;
lhs = y(25);
rhs = params(39)+y(45)-y(6);
residual(35) = lhs - rhs;
lhs = y(26);
rhs = params(39)+y(46)-y(7);
residual(36) = lhs - rhs;
lhs = y(27);
rhs = params(39)+y(50)-y(10);
residual(37) = lhs - rhs;
lhs = y(23);
rhs = y(49)+params(5);
residual(38) = lhs - rhs;
lhs = y(22);
rhs = y(51)+params(40);
residual(39) = lhs - rhs;
lhs = y(21);
rhs = y(48)+params(4);
residual(40) = lhs - rhs;

end
