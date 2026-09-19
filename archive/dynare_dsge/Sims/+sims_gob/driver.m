%
% Status : main Dynare file
%
% Warning : this file is generated automatically by Dynare
%           from model file (.mod)

if isoctave || matlab_ver_less_than('8.6')
    clear all
else
    clearvars -global
    clear_persistent_variables(fileparts(which('dynare')), false)
end
tic0 = tic;
% Define global variables.
global M_ options_ oo_ estim_params_ bayestopt_ dataset_ dataset_info estimation_info ys0_ ex0_
options_ = [];
M_.fname = 'sims_gob';
M_.dynare_version = '5.5';
oo_.dynare_version = '5.5';
options_.dynare_version = '5.5';
%
% Some global variables initialization
%
global_initialization;
M_.exo_names = cell(2,1);
M_.exo_names_tex = cell(2,1);
M_.exo_names_long = cell(2,1);
M_.exo_names(1) = {'ea'};
M_.exo_names_tex(1) = {'ea'};
M_.exo_names_long(1) = {'ea'};
M_.exo_names(2) = {'eg'};
M_.exo_names_tex(2) = {'eg'};
M_.exo_names_long(2) = {'eg'};
M_.endo_names = cell(9,1);
M_.endo_names_tex = cell(9,1);
M_.endo_names_long = cell(9,1);
M_.endo_names(1) = {'pi'};
M_.endo_names_tex(1) = {'pi'};
M_.endo_names_long(1) = {'pi'};
M_.endo_names(2) = {'x'};
M_.endo_names_tex(2) = {'x'};
M_.endo_names_long(2) = {'x'};
M_.endo_names(3) = {'rf'};
M_.endo_names_tex(3) = {'rf'};
M_.endo_names_long(3) = {'rf'};
M_.endo_names(4) = {'i'};
M_.endo_names_tex(4) = {'i'};
M_.endo_names_long(4) = {'i'};
M_.endo_names(5) = {'yf'};
M_.endo_names_tex(5) = {'yf'};
M_.endo_names_long(5) = {'yf'};
M_.endo_names(6) = {'y'};
M_.endo_names_tex(6) = {'y'};
M_.endo_names_long(6) = {'y'};
M_.endo_names(7) = {'a'};
M_.endo_names_tex(7) = {'a'};
M_.endo_names_long(7) = {'a'};
M_.endo_names(8) = {'g'};
M_.endo_names_tex(8) = {'g'};
M_.endo_names_long(8) = {'g'};
M_.endo_names(9) = {'r'};
M_.endo_names_tex(9) = {'r'};
M_.endo_names_long(9) = {'r'};
M_.endo_partitions = struct();
M_.param_names = cell(10,1);
M_.param_names_tex = cell(10,1);
M_.param_names_long = cell(10,1);
M_.param_names(1) = {'sigma'};
M_.param_names_tex(1) = {'sigma'};
M_.param_names_long(1) = {'sigma'};
M_.param_names(2) = {'chi'};
M_.param_names_tex(2) = {'chi'};
M_.param_names_long(2) = {'chi'};
M_.param_names(3) = {'beta'};
M_.param_names_tex(3) = {'beta'};
M_.param_names_long(3) = {'beta'};
M_.param_names(4) = {'phi'};
M_.param_names_tex(4) = {'phi'};
M_.param_names_long(4) = {'phi'};
M_.param_names(5) = {'zeta'};
M_.param_names_tex(5) = {'zeta'};
M_.param_names_long(5) = {'zeta'};
M_.param_names(6) = {'psi'};
M_.param_names_tex(6) = {'psi'};
M_.param_names_long(6) = {'psi'};
M_.param_names(7) = {'rhoa'};
M_.param_names_tex(7) = {'rhoa'};
M_.param_names_long(7) = {'rhoa'};
M_.param_names(8) = {'rhog'};
M_.param_names_tex(8) = {'rhog'};
M_.param_names_long(8) = {'rhog'};
M_.param_names(9) = {'phipi'};
M_.param_names_tex(9) = {'phipi'};
M_.param_names_long(9) = {'phipi'};
M_.param_names(10) = {'gamma'};
M_.param_names_tex(10) = {'gamma'};
M_.param_names_long(10) = {'gamma'};
M_.param_partitions = struct();
M_.exo_det_nbr = 0;
M_.exo_nbr = 2;
M_.endo_nbr = 9;
M_.param_nbr = 10;
M_.orig_endo_nbr = 9;
M_.aux_vars = [];
M_ = setup_solvers(M_);
M_.Sigma_e = zeros(2, 2);
M_.Correlation_matrix = eye(2, 2);
M_.H = 0;
M_.Correlation_matrix_ME = 1;
M_.sigma_e_is_diagonal = true;
M_.det_shocks = [];
M_.surprise_shocks = [];
M_.heteroskedastic_shocks.Qvalue_orig = [];
M_.heteroskedastic_shocks.Qscale_orig = [];
options_.linear = true;
options_.block = false;
options_.bytecode = false;
options_.use_dll = false;
M_.nonzero_hessian_eqs = [];
M_.hessian_eq_zero = isempty(M_.nonzero_hessian_eqs);
M_.orig_eq_nbr = 9;
M_.eq_nbr = 9;
M_.ramsey_eq_nbr = 0;
M_.set_auxiliary_variables = exist(['./+' M_.fname '/set_auxiliary_variables.m'], 'file') == 2;
M_.epilogue_names = {};
M_.epilogue_var_list_ = {};
M_.orig_maximum_endo_lag = 1;
M_.orig_maximum_endo_lead = 1;
M_.orig_maximum_exo_lag = 0;
M_.orig_maximum_exo_lead = 0;
M_.orig_maximum_exo_det_lag = 0;
M_.orig_maximum_exo_det_lead = 0;
M_.orig_maximum_lag = 1;
M_.orig_maximum_lead = 1;
M_.orig_maximum_lag_with_diffs_expanded = 1;
M_.lead_lag_incidence = [
 0 3 12;
 0 4 13;
 0 5 0;
 0 6 0;
 0 7 0;
 0 8 0;
 1 9 14;
 2 10 15;
 0 11 0;]';
M_.nstatic = 5;
M_.nfwrd   = 2;
M_.npred   = 0;
M_.nboth   = 2;
M_.nsfwrd   = 4;
M_.nspred   = 2;
M_.ndynamic   = 4;
M_.dynamic_tmp_nbr = [3; 0; 0; 0; ];
M_.model_local_variables_dynamic_tt_idxs = {
};
M_.equations_tags = {
  1 , 'name' , 'pi' ;
  2 , 'name' , 'x' ;
  3 , 'name' , 'rf' ;
  4 , 'name' , 'yf' ;
  5 , 'name' , '5' ;
  6 , 'name' , 'i' ;
  7 , 'name' , 'a' ;
  8 , 'name' , 'g' ;
  9 , 'name' , 'r' ;
};
M_.mapping.pi.eqidx = [1 2 6 9 ];
M_.mapping.x.eqidx = [1 2 5 ];
M_.mapping.rf.eqidx = [2 3 ];
M_.mapping.i.eqidx = [2 6 9 ];
M_.mapping.yf.eqidx = [4 5 ];
M_.mapping.y.eqidx = [5 ];
M_.mapping.a.eqidx = [3 4 7 ];
M_.mapping.g.eqidx = [3 4 8 ];
M_.mapping.r.eqidx = [9 ];
M_.mapping.ea.eqidx = [7 ];
M_.mapping.eg.eqidx = [8 ];
M_.static_and_dynamic_models_differ = false;
M_.has_external_function = false;
M_.state_var = [7 8 ];
M_.exo_names_orig_ord = [1:2];
M_.maximum_lag = 1;
M_.maximum_lead = 1;
M_.maximum_endo_lag = 1;
M_.maximum_endo_lead = 1;
oo_.steady_state = zeros(9, 1);
M_.maximum_exo_lag = 0;
M_.maximum_exo_lead = 0;
oo_.exo_steady_state = zeros(2, 1);
M_.params = NaN(10, 1);
M_.endo_trends = struct('deflator', cell(9, 1), 'log_deflator', cell(9, 1), 'growth_factor', cell(9, 1), 'log_growth_factor', cell(9, 1));
M_.NNZDerivatives = [30; 0; -1; ];
M_.static_tmp_nbr = [0; 0; 0; 0; ];
M_.model_local_variables_static_tt_idxs = {
};
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
%
% SHOCKS instructions
%
M_.exo_det_length = 0;
M_.Sigma_e(1, 1) = 1;
M_.Sigma_e(2, 2) = 1;
options_.ar = 1;
options_.irf = 20;
options_.nograph = true;
options_.order = 1;
var_list_ = {};
[info, oo_, options_, M_] = stoch_simul(M_, options_, oo_, var_list_);


oo_.time = toc(tic0);
disp(['Total computing time : ' dynsec2hms(oo_.time) ]);
if ~exist([M_.dname filesep 'Output'],'dir')
    mkdir(M_.dname,'Output');
end
save([M_.dname filesep 'Output' filesep 'sims_gob_results.mat'], 'oo_', 'M_', 'options_');
if exist('estim_params_', 'var') == 1
  save([M_.dname filesep 'Output' filesep 'sims_gob_results.mat'], 'estim_params_', '-append');
end
if exist('bayestopt_', 'var') == 1
  save([M_.dname filesep 'Output' filesep 'sims_gob_results.mat'], 'bayestopt_', '-append');
end
if exist('dataset_', 'var') == 1
  save([M_.dname filesep 'Output' filesep 'sims_gob_results.mat'], 'dataset_', '-append');
end
if exist('estimation_info', 'var') == 1
  save([M_.dname filesep 'Output' filesep 'sims_gob_results.mat'], 'estimation_info', '-append');
end
if exist('dataset_info', 'var') == 1
  save([M_.dname filesep 'Output' filesep 'sims_gob_results.mat'], 'dataset_info', '-append');
end
if exist('oo_recursive_', 'var') == 1
  save([M_.dname filesep 'Output' filesep 'sims_gob_results.mat'], 'oo_recursive_', '-append');
end
if ~isempty(lastwarn)
  disp('Note: warning(s) encountered in MATLAB/Octave code')
end
