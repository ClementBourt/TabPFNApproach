1. The Dashboard has be written exclusively in french. The only word that has to stay written in english is "forecast." So things like Net Income should be written.

2. There is an issue in how the data looks. It seems like you have computed the solde of the accounts with the wront sign conventon. For example the values for the test and train data for the account 707010, for this company, should be positive, not negative. All account soldes do not follow the same rules regarding their computations, some of them are compute with the formula DEBIT-CREDIT, others CREDIT-DEBIT. Make sure you respect these conventions approprietly. 

3. The data from the prophet forecast is stored as "FirstTry". Rename the file where this name is assigned to this forecast with the name "ProphetWorkflow".

4. TabPFN provide confidence intervals, plot them as well. 
