# Proiect practica anul 2 #

*Denumire proiect*: **Aplicatie python de scraping pentru stiri din mediul online**

*Descriere aplicatie*: Aplicatia va face scraping pe mai multe site-uri de stiri, colectand titlul, continutul, precum si metadatele acestora (data, autor, categorie), urmand ca toate aceste informatii sa fie stocate intr-o baza de date localhost MySQL. De asemenea, vom folosi un API pentru a centraliza si stoca toate informatiile stranse in BD, impachetate in format JSON (serializare). Diverse cereri API de filtrare catre baza de date vor putea fi adaugate pentru o mai buna vizualizare a informatiilor (ex: ultimele n stiri, vizualizare stiri pana intr-o anumita data calendaristica, etc.)

*Tehnologii si programe software folosite*:
- Limbaj de programare utilizat: Python3.13
- RDBSM utilizat: MariaDB
- Editor de cod : Visual Studio Code
- Librarii Python utilizate: beautifulsoup4 (pentru extragerea/scraping a informatiilor din HTML), fastapi (framework REST API), mysql-connector-python (driver oficial pentru comunicarea cu BD), ollama (LLM utilizat: llama3.2), requests (pentru descarcarea codului sursa al paginilor web), uvicorn (server REST API)
- Pentru vizualizarea rezultatelor, vom utiliza interfata generata automat de FastAPI, precum si DBeaver pentru a verifica integritatea bazei de date (daca scrapingul functioneaza corect)
- Toate pachetele necesare proiectului au fost instalate in cadrul unui venv (virtual environment)

*Denumire prezentare*: **Diferenta dintre arhitecturile de procesor ARM si x86**
### Slide-uri prezentare:

1. Slide cu titlu
2. Cuprins
3. Introducere: Evolutia procesoarelor in era digitala
4. Arhitectura x86: Performanta prin complexitate (CISC)
5. Arhitectura ARM: Eficienta prin simplitate (RISC)
6. RISC vs CISC: Diferentele fundamentale dintre seturile de instructiuni
7. Consumul energetic si managementul termic: ARM vs x86
8. Performanta in calculul de inalta densitate (servere vs dispozitive mobile)
9. Compatibilitatea software si provocarile ecosistemelor
10. Segmentarea pietei: Unde domina x86 si unde straluceste ARM? 
