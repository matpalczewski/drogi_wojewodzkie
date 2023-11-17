# Pliki

- ***drogi.py*** - skrypt do uruchomienia w oprogramowaniu QGIS (najpierw należy dodać go do Panelu algorytmów)
- ***drogi_kom.py*** - skrypt będący kopią skryptu wspomnianego powyżej, opatrzony komentarzami
- ***drogi.pyt*** - skrypt (Python Toolbox) do uruchomienia w oprogramowaniu ArcGIS
- ***drogi_kom.pyt*** - skrypt będący kopią skryptu wspomnianego powyżej, opatrzony komentarzami
- ***wykaz_drog.csv*** - parametr dla wspomnianych wyżej skryptów

# Opis

Skrypty w tym repozytorium służą do wygenerowania warstwy liniowej z pliku CSV (*wykaz_drog.csv*) schematycznie przedstawiającej drogi wojewódzkie. Plik CSV zawiera wykaz dróg wojewódzkich. Każda droga wymieniona w wykazie przebiega przez przynajmniej dwa miasta. Każdy wiersz pliku reprezentuje jedną drogę; zawiera jej numer oraz nazwy miast leżących na danej drodze, wymienione w odpowiedniej kolejności. Skrypty zwracają warstwę z liniami łączącymi miasta na mapie, tak jak robią to drogi wojewódzkie. Numery dróg i nazwy połączonych miast są zapisywane w tabeli atrybutów warstwy.\
**Skrypty zwracają warstwę z odniesieniem przestrzennym, mimo że nie ma takiego w pliku CSV (plik nie zawiera współrzędnych miast).**\
Plik CSV będzie aktualizowany w związku z pojawianiem się nowych miast w Polsce 1 stycznia każdego roku. W celu przyspieszenia działania skryptu kod jest dostosowany do obecnej sytuacji, w której co najwyżej dwa polskie miasta mogą nosić taką samą nazwę - będzie tak co najmniej do końca 2024 r. (jeśli sytuacja się zmieni, zostaną wprowadzone drobne zmiany w kodzie).
