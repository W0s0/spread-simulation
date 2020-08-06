% This script attend the need of downloading historic stock data for each
% exchange (Nasdaq, Nyse and Amex) from the depreciated yahoo API.
% By clean data mean data that are available for all the timeframe

%% Data Download
s1 = 'NASDAQ';
s2 = 'NYSE';
s3 = 'AMEX';

start_date = '18022012';
end_date = '18022019';

% Stock Data
nasdaqStock = hist_stock_data(start_date, end_date, fullfile('tickers', 'NASDAQtickers.txt'));
nyseStock = hist_stock_data(start_date, end_date, fullfile('tickers', 'NYSEtickers.txt'));
amexStock = hist_stock_data(start_date, end_date, fullfile('tickers', 'AMEXtickers.txt'));

amexIndex = hist_stock_data(start_date, end_date, '^XAX');
nyseIndex = hist_stock_data(start_date, end_date, '^NYA');
nasdaqIndex = hist_stock_data(start_date, end_date, '^IXIC');

%% Clean Data
% Keep only data that are available for all the periods
% Indices are cleaned.

amexStockClean = {}
k = 1
for i=1:size(amexStock, 2)
    if size(amexStock(i).Close, 1) == 1759
        amexStockClean(k).Date = amexStock(i).Date;
        amexStockClean(k).Open = amexStock(i).Open;
        amexStockClean(k).High = amexStock(i).High;
        amexStockClean(k).Low = amexStock(i).Low;
        amexStockClean(k).Close = amexStock(i).Close;
        amexStockClean(k).AdjClose = amexStock(i).AdjClose;
        amexStockClean(k).Volume = amexStock(i).Volume;
        amexStockClean(k).Ticker = amexStock(i).Ticker;
        k = k + 1;
    end
end


nyseStockClean = {}
k = 1
for i=1:size(nyseStock, 2)
    if size(nyseStock(i).Close, 1) == 1759
        nyseStockClean(k).Date = nyseStock(i).Date;
        nyseStockClean(k).Open = nyseStock(i).Open;
        nyseStockClean(k).High = nyseStock(i).High;
        nyseStockClean(k).Low = nyseStock(i).Low;
        nyseStockClean(k).Close = nyseStock(i).Close;
        nyseStockClean(k).AdjClose = nyseStock(i).AdjClose;
        nyseStockClean(k).Volume = nyseStock(i).Volume;
        nyseStockClean(k).Ticker = nyseStock(i).Ticker;
        k = k + 1;
    end
end


nasdaqStockClean = {}
k = 1
for i=1:size(nasdaqStock, 2)
    if size(nasdaqStock(i).Close, 1) == 1759
        nasdaqStockClean(k).Date = nasdaqStock(i).Date;
        nasdaqStockClean(k).Open = nasdaqStock(i).Open;
        nasdaqStockClean(k).High = nasdaqStock(i).High;
        nasdaqStockClean(k).Low = nasdaqStock(i).Low;
        nasdaqStockClean(k).Close = nasdaqStock(i).Close;
        nasdaqStockClean(k).AdjClose = nasdaqStock(i).AdjClose;
        nasdaqStockClean(k).Volume = nasdaqStock(i).Volume;
        nasdaqStockClean(k).Ticker = nasdaqStock(i).Ticker;
        k = k + 1;
    end
end

%% Write in csv format to desired directory

% check if directory exists.
check_for_dir(fullfile(pwd, 'Database'));
    
% Data Write
    
% Amex
my_directory = fullfile(pwd, 'Database', 'AmexStockData7yClean');
% create amex directory
check_for_dir(my_directory);

strct = amexStockClean;
for i=1:size(amexStockClean, 2)
    s = struct();
    s.Date = strct(i).Date;
    s.Open = strct(i).Open;
    s.High = strct(i).High;
    s.Low = strct(i).Low;
    s.Close = strct(i).Close;
    s.AdjClose = strct(i).AdjClose;
    s.Volume = strct(i).Volume;
    dict = fullfile(my_directory, [strct(i).Ticker '.csv']);
    writetable(struct2table(s), dict);
end


% Nyse
my_directory = fullfile(pwd, 'Database', 'NyseStockData7yClean');
check_for_dir(my_directory);

strct = nyseStockClean;
for i=1:size(nyseStockClean, 2)
    s = struct();
    s.Date = strct(i).Date;
    s.Open = strct(i).Open;
    s.High = strct(i).High;
    s.Low = strct(i).Low;
    s.Close = strct(i).Close;
    s.AdjClose = strct(i).AdjClose;
    s.Volume = strct(i).Volume;
    dict = fullfile(my_directory, [strct(i).Ticker '.csv']);
    writetable(struct2table(s), dict);
end

% Nasdaq
my_directory = fullfile(pwd, 'Database', 'NasdaqStockData7yClean');
check_for_dir(my_directory);

strct = nasdaqStockClean;
for i=1:size(nasdaqStockClean, 2)
    s = struct();
    s.Date = strct(i).Date;
    s.Open = strct(i).Open;
    s.High = strct(i).High;
    s.Low = strct(i).Low;
    s.Close = strct(i).Close;
    s.AdjClose = strct(i).AdjClose;
    s.Volume = strct(i).Volume;
    if strcmp(strct(i).Ticker, 'PRN')
        % in case of windows reserved file name
        strct(i).Ticker = 'prn';
    else
        dict = fullfile(my_directory, [strct(i).Ticker '.csv']);
    end
    writetable(struct2table(s), dict);
end

    
% Indices Write
my_directory = fullfile(pwd, 'Database');

% Amex
strct = amexIndex;
s = struct();
s.Date = strct.Date;
s.Open = strct.Open;
s.High = strct.High;
s.Low = strct.Low;
s.Close = strct.Close;
s.AdjClose = strct.AdjClose;
s.Volume = strct.Volume;
dict = fullfile(my_directory, [strct.Ticker '.csv']);
writetable(struct2table(s), dict);
    
% Nyse
strct = nyseIndex;
s = struct();
s.Date = strct.Date;
s.Open = strct.Open;
s.High = strct.High;
s.Low = strct.Low;
s.Close = strct.Close;
s.AdjClose = strct.AdjClose;
s.Volume = strct.Volume;
dict = fullfile(my_directory, [strct.Ticker '.csv']);
writetable(struct2table(s), dict);

% Nasdaq
strct = nasdaqIndex;
s = struct();
s.Date = strct.Date;
s.Open = strct.Open;
s.High = strct.High;
s.Low = strct.Low;
s.Close = strct.Close;
s.AdjClose = strct.AdjClose;
s.Volume = strct.Volume;
dict = fullfile(my_directory, [strct.Ticker '.csv']);
writetable(struct2table(s), dict);

%% Helper functions

function check_for_dir(dir_path)
    if exist(dir_path, 'dir')
        warning([dir_path, ' directory already exists.'])
    else
        mkdir(dir_path)
        disp([dir_path ' directory created'])
    end
end