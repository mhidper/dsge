function [fevd_new] = Group_shocks(fevd,n,shocks_groups)

for i = 1:n
    [i1,v1] = find(shocks_groups==i);
    fevd_new(:,:,i) = sum(fevd(:,:,i1),3);
end


end