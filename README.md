# Pliki

- ***drogi.py*** - skrypt do uruchomienia w oprogramowaniu QGIS (najpierw należy dodać go do Panelu algorytmów)
- ***drogi_kom.py*** - skrypt będący kopią ww. skryptu, opatrzony komentarzami
- ***drogi.pyt*** - skrypt (Python Toolbox) do uruchomienia w oprogramowaniu ArcGIS
- ***drogi_kom.pyt*** - skrypt będący kopią ww. skryptu, opatrzony komentarzami
- ***wykaz_drog.csv*** - parametr dla ww. skryptów

# Opis

Skrypty w tym repozytorium służą do wygenerowania warstwy liniowej z pliku CSV (*wykaz_drog.csv*) schematycznie przedstawiającej drogi wojewódzkie. Plik CSV zawiera wykaz dróg wojewódzkich. Plik ten jest mojego autorstwa - jest symulacją danych jakie można byłoby dostać od zarządów dróg wojewódzkich; jego tworzenie nie było zautomatyzowane. Każda droga wymieniona w wykazie przebiega przez przynajmniej dwa miasta. Każdy wiersz pliku reprezentuje jedną drogę; zawiera jej numer oraz nazwy miast leżących na danej drodze, wymienione w odpowiedniej kolejności. Skrypty generują warstwę z liniami łączącymi miasta na mapie, symbolizującymi połączenia miast przez drogi wojewódzkie. Numery dróg i nazwy połączonych miast są zapisywane w tabeli atrybutów warstwy. Skrypty odczytują lokalizacje miast na podstawie OpenStreetMap, więc poprawność wygenerowanej warstwy można stwierdzić poprzez jej wyświetlenie w oprogramowaniu GIS na mapie podkładowej OpenStreetMap.

**Skrypty generują warstwę z odniesieniem przestrzennym, mimo że nie ma takiego w pliku CSV (plik nie zawiera współrzędnych miast). Wykrywają też miasta kryjące się pod tą samą nazwą, mimo że w pliku CSV nie ma dodatkowej informacji (np. nazwy województwa) rozróżniającej miasta o takiej samej nazwie.**

Plik CSV będzie aktualizowany w związku z pojawianiem się nowych miast w Polsce 1 stycznia każdego roku. W celu przyspieszenia działania skryptów kod jest dostosowany do obecnej sytuacji, w której co najwyżej dwa polskie miasta mogą nosić taką samą nazwę - będzie tak co najmniej do końca 2024 r. (jeśli sytuacja się zmieni, zostaną wprowadzone drobne zmiany w kodzie).
