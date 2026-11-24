# Idea Immobiliare — Sito Web

Sito statico per l'agenzia Idea Immobiliare di Mordini Fabrizio, Lugo (RA).

## Come funziona

Il sito si genera automaticamente dalla cartella `annunci/`. Ogni volta che aggiungi, modifichi o elimini una cartella e fai **push su GitHub**, il sito si aggiorna da solo in pochi minuti.

---

## Come aggiungere un annuncio

### 1. Crea la cartella dell'annuncio

Vai nella cartella giusta:
- **Vendite**: `annunci/vendite/NOME-COMUNE/`
- **Affitti**: `annunci/affitti/NOME-COMUNE/`

Crea una nuova cartella con il **titolo dell'annuncio** come nome.  
Esempio: `annunci/vendite/lugo/Via Roma 12 - Trilocale/`

> Se il comune non esiste ancora, crea prima la cartella del comune (es. `annunci/vendite/conselice/`).

### 2. Aggiungi le foto

Metti le foto dell'immobile nella cartella dell'annuncio.  
- Formati accettati: `.jpg`, `.jpeg`, `.png`, `.webp`
- Le foto vengono ordinate per nome: `01.jpg`, `02.jpg`, `03.jpg`...
- La **prima foto** (in ordine alfabetico) diventa la copertina dell'annuncio

### 3. Crea il file `info.txt`

Nella cartella dell'annuncio, crea un file chiamato **`info.txt`** con questo formato:

```
sottotitolo: Trilocale 85 mq, 2 camere, 1 bagno, balcone, garage
prezzo: € 135.000
indirizzo: Via Roma 12, Lugo (RA)
classe_energetica: C
mq: 85
camere: 2
---
Luminoso appartamento al secondo piano in zona residenziale tranquilla.
L'immobile si compone di ingresso, soggiorno con angolo cottura, 
due camere da letto, bagno finestrato e balcone.
```

**Regole importanti:**
- Ogni campo va su una **riga separata** con il formato `campo: valore`
- I campi sono tutti **facoltativi** — se ne manca uno, semplicemente non viene mostrato
- I nomi dei campi non sono sensibili a maiuscole/minuscole (`Prezzo`, `PREZZO`, `prezzo` funzionano tutti)
- Il separatore `---` divide i campi dalla descrizione libera
- La descrizione sotto `---` può essere lunga quanto vuoi

### 4. Foto copertina del comune (opzionale)

Per aggiungere una foto di copertina per un comune, metti un file `copertina.jpg` nella cartella del comune:

```
annunci/vendite/lugo/copertina.jpg
annunci/affitti/lugo/copertina.jpg
```

### 5. Push su GitHub

Dopo aver aggiunto tutto, fai commit e push:

```
git add .
git commit -m "Aggiunto annuncio Via Roma 12"
git push
```

Il sito si aggiorna automaticamente in 2-3 minuti.

---

## Come eliminare un annuncio

Elimina la cartella dell'annuncio e fai push. L'annuncio scompare dal sito.

---

## Struttura delle cartelle

```
annunci/
├── vendite/
│   ├── lugo/
│   │   ├── copertina.jpg              ← foto copertina del comune
│   │   └── Via Roma 12 - Trilocale/   ← cartella annuncio
│   │       ├── 01.jpg                 ← foto
│   │       ├── 02.jpg
│   │       └── info.txt               ← dati dell'annuncio
│   └── bagnacavallo/
│       ├── copertina.jpg
│       └── ...
└── affitti/
    └── lugo/
        ├── copertina.jpg
        └── ...
```

---

## Configurazione iniziale del repository

### 1. Crea il repository su GitHub

1. Vai su [github.com/new](https://github.com/new)
2. Nome: `ideaimmobiliare` (o quello che preferisci)
3. Pubblico
4. Clicca "Create repository"

### 2. Carica i file

```bash
cd ideaimmobiliare
git init
git add .
git commit -m "Primo caricamento sito"
git branch -M main
git remote add origin https://github.com/TUO-USERNAME/ideaimmobiliare.git
git push -u origin main
```

### 3. Attiva GitHub Pages

1. Vai nelle **Settings** del repository
2. Sezione **Pages** (nella barra laterale)
3. Source: seleziona **GitHub Actions**
4. Salva

Il sito sarà disponibile all'indirizzo:  
`https://TUO-USERNAME.github.io/ideaimmobiliare/`

---

## Errori

Se qualcosa non va (un info.txt mancante, un campo problematico), dopo la build viene generato un file `_errori.txt` nella root del progetto con l'elenco dei problemi trovati. L'annuncio incompleto viene comunque pubblicato con i dati disponibili.

---

## Contatti e orari

Per modificare indirizzo, email, telefono e orari, modifica le variabili all'inizio del file `build.py`:

```python
CONTACT_ADDRESS = "Via Alberto Acquacalda 6/6, 48022 Lugo (RA)"
CONTACT_EMAIL = "ideaimmobiliare2@gmail.com"
CONTACT_PHONE = ""   # Inserisci il numero
CONTACT_HOURS = ""   # Inserisci gli orari
```
