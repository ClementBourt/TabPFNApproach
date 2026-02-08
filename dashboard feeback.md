Looking at the results in the dashbaord raises a few questions, i will list questions and observations per accounts : 
603700, why is there no test set ? 
606000, why is there no test set ? Why is there no prophet forecast ?
606110, why is there no test set ?
606120 why is there no test set ?
606300 the test set seem strangely different from the train set, we need to investigate to make sure this is normal.
606400, the fact that some metrics are undefined because of the 0 values in the test set is normal, how ever i thought some of the metrics in the table were computed on yearly agegated data, we need to investigate if it is the case, if not we will need to add such metrics.
606800 the test set seem strangely different from the train set, we need to investigate to make sure this is normal.
the fact that some metrics are undefined because of the 0 values in the test set is normal, how ever i thought some of the metrics in the table were computed on yearly agegated data, we need to investigate if it is the case, if not we will need to add such metrics.
607031 why is there no test set ?
607200 why is there no test set ?
609700 why is there no test set ?
613500 the fact that some metrics are undefined because of the 0 values in the test set is normal, how ever i thought some of the metrics in the table were computed on yearly agegated data, we need to investigate if it is the case, if not we will need to add such metrics.
613500 why is there no test set ?
615500 why is there no test set ?
615600 the test set seem strangely different from the train set, we need to investigate to make sure this is normal.
606400, the fact that some metrics are undefined because of the 0 values in the test set is normal, how ever i thought some of the metrics in the table were computed on yearly agegated data, we need to investigate if it is the case, if not we will need to add such metrics.
616300 why is there no test set ?
622200 why is there no test set ?
622201 why is there no test set ?
622601 why is there no test set ? why no prophet forecast ?
622610 for extreme cases like this where we only have one data point at the end of the train period should simply make a carry forward forecast like is done with the prophet workflow
622700 why no test set ?