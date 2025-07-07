function [] = saveData(timetable,path)

Data = struct();

varnames = timetable.Properties.VariableNames;

for iname = 1:length(varnames)
    thisname = varnames{iname};
    Data.(thisname) = timetable{:,thisname};
end

save(path, '-struct','Data');

end