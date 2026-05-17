%% 
% od 15 do 19.00 autobus 1845, od 19 do 1.00 7734.
% Linia 4/146. 

clear all
close all
clc

BUS_number = '146';

cd('C:\Users\Maciej Kozłowski\Documents\Code\AutobusMZA')

path_DANE = 'C:\Users\Maciej Kozłowski\Documents\Code\AutobusMZA\DANE';
path_OUTPUT = 'C:\Users\Maciej Kozłowski\Documents\Code\AutobusMZA\OUTPUT';

%% =========================================================
% WCZYTANIE STOP TIMES
% ==========================================================

if strcmp(BUS_number,'146')

    stoptimes_DW_FAL = importfile( ...
        "C:\Users\Maciej Kozłowski\Documents\Code\AutobusMZA\DANE\stoptimes_146_DW_FAL.xlsx", ...
        "stoptimes", ...
        [2, Inf]);

    stoptimes_FAL_DW = importfile( ...
        "C:\Users\Maciej Kozłowski\Documents\Code\AutobusMZA\DANE\stoptimes_146_FAL_DW.xlsx", ...
        "stoptimes", ...
        [2, Inf]);

end

%% =========================================================
% SEKWENCJE PRZYSTANKÓW
% ==========================================================

stop_sequence_DW_FAL = table2array(stoptimes_DW_FAL(:,3));
stop_sequence_FAL_DW = table2array(stoptimes_FAL_DW(:,3));

[liczba_przystankow_FAL_DW,~] = size(stop_sequence_FAL_DW);
[liczba_przystankow_DW_FAL,~] = size(stop_sequence_DW_FAL);

disp(['Liczba przystanków FAL -> DW: ', num2str(liczba_przystankow_FAL_DW)])
disp(['Liczba przystanków DW -> FAL: ', num2str(liczba_przystankow_DW_FAL)])

%% =========================================================
% WSPÓŁRZĘDNE PRZYSTANKÓW
% ==========================================================

lat_stop_DW_FAL = stoptimes_DW_FAL.stop_lat;
lon_stop_DW_FAL = stoptimes_DW_FAL.stop_lon;

lat_stop_FAL_DW = stoptimes_FAL_DW.stop_lat;
lon_stop_FAL_DW = stoptimes_FAL_DW.stop_lon;

% przystanki krańcowe

lat_stop_DW_FAL_pocz = lat_stop_DW_FAL(1);
lon_stop_DW_FAL_pocz = lon_stop_DW_FAL(1);

lat_stop_DW_FAL_kon = lat_stop_DW_FAL(end);
lon_stop_DW_FAL_kon = lon_stop_DW_FAL(end);

lat_stop_FAL_DW_pocz = lat_stop_FAL_DW(1);
lon_stop_FAL_DW_pocz = lon_stop_FAL_DW(1);

lat_stop_FAL_DW_kon = lat_stop_FAL_DW(end);
lon_stop_FAL_DW_kon = lon_stop_FAL_DW(end);

%% =========================================================
% WCZYTANIE AVL
% ==========================================================

MZA1 = importfile1( ...
    "C:\Users\Maciej Kozłowski\Documents\Code\AutobusMZA\DANE\MZA_1.csv", ...
    [1, Inf]);

line         = table2array(MZA1(:,1));
vehicle_nr   = table2array(MZA1(:,2));
brigade      = table2array(MZA1(:,3));
lat_raw = string(table2array(MZA1(:,4)));
lon_raw = string(table2array(MZA1(:,5)));
vehicle_time = table2array(MZA1(:,6));

lat = zeros(length(lat_raw),1);
lon = zeros(length(lon_raw),1);

N = length(lon_raw);

lon = zeros(N,1);
lat = zeros(N,1);

for i = 1:N

    % ===== LON =====
    s_lon = char(lon_raw(i));

    s_lon_new = [s_lon(1:2) '.' s_lon(3:end)];

    lon(i) = str2double(s_lon_new);

    % ===== LAT =====
    s_lat = char(lat_raw(i));

    s_lat_new = [s_lat(1:2) '.' s_lat(3:end)];

    lat(i) = str2double(s_lat_new);

end

%% =========================================================
% FILTR LINII 146
% ==========================================================

idx_line = strcmp(string(line), BUS_number);

line_146         = line(idx_line);
vehicle_nr_146   = vehicle_nr(idx_line);
brigade_146      = brigade(idx_line);
lat_146          = lat(idx_line);
lon_146          = lon(idx_line);
vehicle_time_146 = vehicle_time(idx_line);

%% =========================================================
% KONWERSJA CZASU
% ==========================================================

% jeśli vehicle_time jest stringiem

try
    time_datetime = datetime( ...
        vehicle_time_146, ...
        'InputFormat','yyyy-MM-dd HH:mm:ss');
catch

    try
        time_datetime = datetime(vehicle_time_146);

    catch
        disp('Problem z konwersją czasu')
    end
end

%% =========================================================
% WYBÓR AUTOBUSÓW
% ==========================================================

% od 15:00 do 19:00 autobus 1845
% od 19:00 do 01:00 autobus 7734

godzina = hour(time_datetime);

idx_1845 = ...
    vehicle_nr_146 == 1845 & ...
    godzina >= 15 & ...
    godzina < 19;

idx_7734 = ...
    vehicle_nr_146 == 7734 & ...
    (godzina >= 19 | godzina <= 1);

%% =========================================================
% ŁĄCZNY ZBIÓR
% ==========================================================

idx_final = idx_1845 | idx_7734;

lat_bus  = lat_146(idx_final);
lon_bus  = lon_146(idx_final);
time_bus = time_datetime(idx_final);
veh_bus  = vehicle_nr_146(idx_final);

%% =========================================================
% SORTOWANIE CZASU
% ==========================================================

[time_bus_sorted, idx_sort] = sort(time_bus);

lat_bus_sorted = lat_bus(idx_sort);
lon_bus_sorted = lon_bus(idx_sort);
veh_bus_sorted = veh_bus(idx_sort);

%% =========================================================
% OBLICZENIE PRĘDKOŚCI
% ==========================================================

N = length(lat_bus_sorted);

speed_kmh = zeros(N,1);
distance_m = zeros(N,1);
time_s = zeros(N,1);

R = 6371000; % promień Ziemi [m]

for i = 2:N

    lat1 = deg2rad(lat_bus_sorted(i-1));
    lon1 = deg2rad(lon_bus_sorted(i-1));

    lat2 = deg2rad(lat_bus_sorted(i));
    lon2 = deg2rad(lon_bus_sorted(i));

    dlat = lat2 - lat1;
    dlon = lon2 - lon1;

    a = sin(dlat/2)^2 + ...
        cos(lat1) * cos(lat2) * sin(dlon/2)^2;

    c = 2 * atan2(sqrt(a), sqrt(1-a));

    distance_m(i) = R * c;

    dt = seconds(time_bus_sorted(i) - time_bus_sorted(i-1));

    time_s(i) = dt;

    if dt > 0
        speed_kmh(i) = (distance_m(i) / dt) * 3.6;
    else
        speed_kmh(i) = 0;
    end

end

%% =========================================================
% USUWANIE BŁĘDÓW GPS
% ==========================================================

%speed_kmh(speed_kmh > 120) = NaN;

%% =========================================================
% WYKRES TIME - SPEED
% ==========================================================

figure('Color','white')

plot( ...
    cumsum(time_s)/60, ...
    speed_kmh, ...
    'b-', ...
    'LineWidth',1.5)

grid on

xlabel('Czas')
ylabel('Prędkość [km/h]')

title(['Linia ', BUS_number, ...
       ' - zależność czas / prędkość'])

%% =========================================================
% MAPA TRASY
% ==========================================================

figure('Color','white')

geoplot( ...
    lat_bus_sorted, ...
    lon_bus_sorted, ...
    'b.')

hold on

geoplot( ...
    lat_stop_DW_FAL, ...
    lon_stop_DW_FAL, ...
    'ro-', ...
    'LineWidth',1.5)

title(['Trasa AVL + przystanki linii ', BUS_number])

legend( ...
    'AVL autobusów', ...
    'Przystanki')

%% =========================================================
% HISTOGRAM PRĘDKOŚCI
% ==========================================================

figure('Color','white')

histogram(speed_kmh,30)

xlabel('Prędkość [km/h]')
ylabel('Liczba obserwacji')

title('Histogram prędkości autobusu')

grid on

%% =========================================================
% ZAPIS WYNIKÓW
% ==========================================================

wyniki = table( ...
    time_bus_sorted, ...
    veh_bus_sorted, ...
    lat_bus_sorted, ...
    lon_bus_sorted, ...
    speed_kmh);

writetable( ...
    wyniki, ...
    fullfile(path_OUTPUT, ...
    ['wyniki_', BUS_number, '.xlsx']))

%% =========================================================
% ANALIZA RUCHU AUTOBUSU
% CZAS -> STOP_SEQUENCE
% ==========================================================

% ----------------------------------------------------------
% Założenie:
%
% lat_bus_sorted
% lon_bus_sorted
% time_bus_sorted
%
% oraz:
%
% lat_stop_DW_FAL
% lon_stop_DW_FAL
% stop_sequence_DW_FAL
%
% są już poprawnie przygotowane
% ----------------------------------------------------------

N_bus = length(lat_bus_sorted);

nearest_stop_id = zeros(N_bus,1);
nearest_distance = zeros(N_bus,1);

R = 6371000; % [m]

%% =========================================================
% PĘTLA PO WSZYSTKICH PUNKTACH AVL
% ==========================================================

for i = 1:N_bus

    % ------------------------------------------------------
    % aktualna pozycja autobusu
    % ------------------------------------------------------

    lat_bus_i = lat_bus_sorted(i);
    lon_bus_i = lon_bus_sorted(i);

    % ------------------------------------------------------
    % odległości do wszystkich przystanków
    % ------------------------------------------------------

    dist_all = zeros(liczba_przystankow_DW_FAL,1);

    for j = 1:liczba_przystankow_DW_FAL

        lat_stop_j = lat_stop_DW_FAL(j);
        lon_stop_j = lon_stop_DW_FAL(j);

        % ==================================================
        % HAVERSINE
        % ==================================================

        lat1 = deg2rad(lat_bus_i);
        lon1 = deg2rad(lon_bus_i);

        lat2 = deg2rad(lat_stop_j);
        lon2 = deg2rad(lon_stop_j);

        dlat = lat2 - lat1;
        dlon = lon2 - lon1;

        a = sin(dlat/2)^2 + ...
            cos(lat1) * cos(lat2) * sin(dlon/2)^2;

        c = 2 * atan2(sqrt(a), sqrt(1-a));

        dist_all(j) = R * c;

    end

    % ------------------------------------------------------
    % najbliższy przystanek
    % ------------------------------------------------------

    [min_dist, idx_min] = min(dist_all);

    nearest_distance(i) = min_dist;

    nearest_stop_id(i) = stop_sequence_DW_FAL(idx_min);

end

%% =========================================================
% FILTR ODLĘGŁOŚCI
% ==========================================================

MAX_STOP_DISTANCE = 120; % [m]

nearest_stop_id_filtered = nearest_stop_id;

nearest_stop_id_filtered( ...
    nearest_distance > MAX_STOP_DISTANCE) = NaN;

%% =========================================================
% WYKRES CZAS - PRZYSTANEK
% ==========================================================

figure('Color','white')

scatter( ...
    time_bus_sorted, ...
    nearest_stop_id_filtered, ...
    12, ...
    'filled')

grid on

xlabel('Czas')
ylabel('Stop sequence')

title([ ...
    'Linia ', ...
    BUS_number, ...
    ' - czas / przystanek'])

%% =========================================================
% WYGŁADZENIE (opcjonalne)
% ==========================================================

hold on

plot( ...
    time_bus_sorted, ...
    nearest_stop_id_filtered, ...
    'r-', ...
    'LineWidth',1)

legend( ...
    'AVL points', ...
    'Trend')

%% =========================================================
% ZAPIS WYNIKÓW
% ==========================================================

wyniki_stop = table( ...
    time_bus_sorted, ...
    lat_bus_sorted, ...
    lon_bus_sorted, ...
    nearest_stop_id_filtered, ...
    nearest_distance);

writetable( ...
    wyniki_stop, ...
    fullfile( ...
        path_OUTPUT, ...
        ['czas_przystanek_', BUS_number, '.xlsx']))

%% =========================================================
% SEGMENTACJA KURSÓW
% METODA:
%
% diff(stop_sequence)
%
% +1  -> jazda w kierunku rosnącym
% -1  -> jazda w kierunku malejącym
%  0  -> postój / brak zmiany
%
% Nowy kurs:
% zmiana znaku kierunku
% ----------------------------------------------------------
%
% wejście:
%
% nearest_stop_id_filtered
% time_bus_sorted
%
% wyjście:
%
% course_id
%
%% =========================================================

stop_id = nearest_stop_id_filtered;

N = length(stop_id);

%% =========================================================
% RÓŻNICE STOP_SEQUENCE
% ==========================================================

dstop = diff(stop_id);

%% =========================================================
% KIERUNEK RUCHU
% ==========================================================

direction = zeros(N,1);

for i = 2:N

    if dstop(i-1) > 0

        direction(i) = 1;

    elseif dstop(i-1) < 0

        direction(i) = -1;

    else

        direction(i) = direction(i-1);

    end

end

%% =========================================================
% SEGMENTACJA KURSÓW
% ==========================================================

course_id = zeros(N,1);

course = 1;

course_id(1) = course;

for i = 2:N

    % ------------------------------------------------------
    % zmiana kierunku
    % ------------------------------------------------------

    if direction(i) ~= direction(i-1)

        % ignorujemy przejścia przez zero
        if direction(i) ~= 0 && direction(i-1) ~= 0

            course = course + 1;

        end

    end

    course_id(i) = course;

end

%% =========================================================
% WYKRES
% ==========================================================

figure('Color','white')

gscatter( ...
    time_bus_sorted, ...
    stop_id, ...
    course_id)

grid on

xlabel('Czas')
ylabel('Stop sequence')

title([ ...
    'Segmentacja kursów - linia ', ...
    BUS_number])

%% =========================================================
% TABELA WYNIKOWA
% ==========================================================

wyniki_kursy = table( ...
    time_bus_sorted, ...
    stop_id, ...
    direction, ...
    course_id);

%% =========================================================
% ZAPIS
% ==========================================================

writetable( ...
    wyniki_kursy, ...
    fullfile( ...
        path_OUTPUT, ...
        ['segmentacja_kursow_', BUS_number, '.xlsx']))

%% =========================================================
% WYKRES PRĘDKOŚĆ - CZAS
% Z KOLORAMI SEGMENTACJI KURSÓW
% ==========================================================

figure('Color','white')

hold on
grid on

colors = lines(max(course_id));

h = gobjects(max(course_id),1);

for c = 1:max(course_id)

    idx = course_id == c;

    h(c) = scatter( ...
        time_bus_sorted(idx), ...
        speed_kmh(idx), ...
        12, ...
        colors(c,:), ...
        'filled');

    plot( ...
        time_bus_sorted(idx), ...
        speed_kmh(idx), ...
        'Color', colors(c,:), ...
        'HandleVisibility','off');

end

xlabel('Czas')
ylabel('Prędkość [km/h]')

title([ ...
    'Linia ', ...
    BUS_number, ...
    ' - prędkość / czas / kurs'])

legend_strings = strings(max(course_id),1);

for c = 1:max(course_id)

    legend_strings(c) = ...
        ['Kurs ', num2str(c)];

end

legend(h,legend_strings,'Location','eastoutside')



